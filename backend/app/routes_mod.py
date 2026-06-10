"""Moderator-only routes. Every mutation is recorded to the audit log."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from . import audit
from .auth import get_current_moderator
from .db import db
from .models import AddModerator, ApproveRequest, EntryUpdate, RejectRequest
from .notify import send_decision_email
from .utils import generate_unique_slug, now_iso

router = APIRouter(prefix="/mod")

EDITABLE_FIELDS = ["company_name", "company_domain", "person_name", "person_title", "quote", "statement_date"]


@router.get("/stats")
async def mod_stats(mod: dict = Depends(get_current_moderator)):
    live = await db.entries.count_documents({"status": "approved"})
    pending = await db.entries.count_documents({"status": "pending"})
    total = await db.entries.count_documents({})
    rejected = await db.entries.count_documents({"status": "rejected"})
    appeals = await db.appeals.count_documents({"status": "open"})
    return {"live": live, "pending": pending, "total": total, "rejected": rejected, "appeals": appeals}


@router.get("/entries")
async def mod_list(status: Optional[str] = None, mod: dict = Depends(get_current_moderator)):
    query = {}
    if status:
        query["status"] = status
    docs = await db.entries.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"items": docs}


@router.post("/entries/{entry_id}/approve")
async def approve_entry(entry_id: str, payload: ApproveRequest, mod: dict = Depends(get_current_moderator)):
    doc = await db.entries.find_one({"id": entry_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")

    score = max(1, min(5, payload.red_flag_score))
    update = {"red_flag_score": score, "status": "approved", "approved_at": now_iso(), "rejection_reason": None}
    for f in EDITABLE_FIELDS:
        val = getattr(payload, f)
        if val is not None:
            update[f] = val
    if payload.sources is not None:
        update["sources"] = [s.model_dump() for s in payload.sources]
    if payload.tags is not None:
        update["tags"] = payload.tags

    if not doc.get("slug"):
        update["slug"] = await generate_unique_slug(
            update.get("person_name", doc["person_name"]),
            update.get("company_name", doc["company_name"]),
            update.get("statement_date", doc.get("statement_date", "")),
        )
    await db.entries.update_one({"id": entry_id}, {"$set": update})
    fresh = await db.entries.find_one({"id": entry_id}, {"_id": 0})

    await audit.record_action(mod["email"], "approve", "entry", entry_id,
                              {"company_name": fresh.get("company_name"), "score": score})
    if fresh.get("submitter_email"):
        await send_decision_email(fresh["submitter_email"], "approved", fresh)
    return {"ok": True}


@router.post("/entries/{entry_id}/reject")
async def reject_entry(entry_id: str, payload: RejectRequest, mod: dict = Depends(get_current_moderator)):
    doc = await db.entries.find_one({"id": entry_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.entries.update_one(
        {"id": entry_id},
        {"$set": {"status": "rejected", "rejection_reason": payload.rejection_reason, "approved_at": None}},
    )
    await audit.record_action(mod["email"], "reject", "entry", entry_id,
                              {"company_name": doc.get("company_name"), "reason": payload.rejection_reason})
    if doc.get("submitter_email"):
        await send_decision_email(doc["submitter_email"], "rejected", doc, payload.rejection_reason)
    return {"ok": True}


@router.post("/entries/{entry_id}/unpublish")
async def unpublish_entry(entry_id: str, mod: dict = Depends(get_current_moderator)):
    res = await db.entries.update_one(
        {"id": entry_id}, {"$set": {"status": "pending", "approved_at": None}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    await audit.record_action(mod["email"], "unpublish", "entry", entry_id)
    return {"ok": True}


@router.put("/entries/{entry_id}")
async def update_entry(entry_id: str, payload: EntryUpdate, mod: dict = Depends(get_current_moderator)):
    doc = await db.entries.find_one({"id": entry_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")
    update = {}
    for f in EDITABLE_FIELDS:
        val = getattr(payload, f)
        if val is not None:
            update[f] = val
    if payload.red_flag_score is not None:
        update["red_flag_score"] = max(1, min(5, payload.red_flag_score))
    if payload.sources is not None:
        update["sources"] = [s.model_dump() for s in payload.sources]
    if payload.tags is not None:
        update["tags"] = payload.tags
    if update:
        await db.entries.update_one({"id": entry_id}, {"$set": update})
        await audit.record_action(mod["email"], "edit", "entry", entry_id,
                                  {"fields": sorted(update.keys())})
    return {"ok": True}


@router.get("/moderators")
async def list_moderators(mod: dict = Depends(get_current_moderator)):
    docs = await db.moderators.find({}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return {"items": docs, "me": mod["email"]}


@router.post("/moderators")
async def add_moderator(payload: AddModerator, mod: dict = Depends(get_current_moderator)):
    email = payload.email.lower()
    existing = await db.moderators.find_one({"email": email})
    if existing:
        if not existing.get("active", True):
            await db.moderators.update_one({"email": email}, {"$set": {"active": True}})
            await audit.record_action(mod["email"], "reactivate_moderator", "moderator", email)
            return {"ok": True, "reactivated": True}
        raise HTTPException(status_code=400, detail="Moderator already exists")
    await db.moderators.insert_one({
        "email": email, "name": "", "picture": "",
        "added_by": mod["email"], "active": True, "created_at": now_iso(),
    })
    await audit.record_action(mod["email"], "add_moderator", "moderator", email)
    return {"ok": True, "reactivated": False}


@router.delete("/moderators/{email}")
async def remove_moderator(email: str, mod: dict = Depends(get_current_moderator)):
    email = email.lower()
    if email == mod["email"]:
        raise HTTPException(status_code=400, detail="You cannot remove yourself")
    target = await db.moderators.find_one({"email": email})
    if not target or not target.get("active", True):
        raise HTTPException(status_code=404, detail="Moderator not found")
    count = await db.moderators.count_documents({"active": True})
    if count <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last moderator")
    await db.moderators.update_one({"email": email}, {"$set": {"active": False}})
    await db.user_sessions.delete_many({"email": email})
    await audit.record_action(mod["email"], "remove_moderator", "moderator", email)
    return {"ok": True}


@router.get("/audit")
async def get_audit(limit: int = 100, mod: dict = Depends(get_current_moderator)):
    return {"items": await audit.list_actions(min(max(limit, 1), 500))}


@router.get("/appeals")
async def list_appeals(status: Optional[str] = None, mod: dict = Depends(get_current_moderator)):
    query = {}
    if status:
        query["status"] = status
    docs = await db.appeals.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"items": docs}


@router.post("/appeals/{appeal_id}/resolve")
async def resolve_appeal(appeal_id: str, mod: dict = Depends(get_current_moderator)):
    res = await db.appeals.update_one(
        {"id": appeal_id}, {"$set": {"status": "resolved", "resolved_by": mod["email"], "resolved_at": now_iso()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appeal not found")
    await audit.record_action(mod["email"], "resolve_appeal", "appeal", appeal_id)
    return {"ok": True}
