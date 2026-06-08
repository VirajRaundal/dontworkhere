from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import logging
import uuid
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_DAYS = 7

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ----------------------------- Models -----------------------------
class Source(BaseModel):
    label: str
    url: str

    @field_validator("label")
    @classmethod
    def label_ok(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Source label is required")
        return v

    @field_validator("url")
    @classmethod
    def url_ok(cls, v):
        v = v.strip()
        if not re.match(r"^https?://", v):
            raise ValueError("Source URL must start with http:// or https://")
        return v


class SubmissionCreate(BaseModel):
    company_name: str
    company_domain: Optional[str] = ""
    person_name: str
    person_title: Optional[str] = ""
    quote: str
    statement_date: Optional[str] = ""
    sources: List[Source]
    submitter_email: Optional[str] = ""

    @field_validator("company_name", "person_name")
    @classmethod
    def required_text(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("This field is required")
        return v

    @field_validator("quote")
    @classmethod
    def quote_len(cls, v):
        v = (v or "").strip()
        if len(v) < 20:
            raise ValueError("Quote must be at least 20 characters")
        return v

    @field_validator("sources")
    @classmethod
    def sources_ok(cls, v):
        if not v or len(v) < 1:
            raise ValueError("At least one source is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 sources allowed")
        return v


class ApproveRequest(BaseModel):
    red_flag_score: int = 3
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    person_name: Optional[str] = None
    person_title: Optional[str] = None
    quote: Optional[str] = None
    statement_date: Optional[str] = None
    sources: Optional[List[Source]] = None


class RejectRequest(BaseModel):
    rejection_reason: str = ""


class EntryUpdate(BaseModel):
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    person_name: Optional[str] = None
    person_title: Optional[str] = None
    quote: Optional[str] = None
    statement_date: Optional[str] = None
    red_flag_score: Optional[int] = None
    sources: Optional[List[Source]] = None


class AddModerator(BaseModel):
    email: EmailStr


# ----------------------------- Helpers -----------------------------
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


async def generate_unique_slug(person_name: str, company_name: str, statement_date: str) -> str:
    year = ""
    if statement_date:
        try:
            year = str(datetime.fromisoformat(statement_date.replace("Z", "")).year)
        except Exception:
            year = ""
    base = slugify(f"{person_name}-{company_name}" + (f"-{year}" if year else ""))
    if not base:
        base = f"red-flag-{uuid.uuid4().hex[:6]}"
    slug = base
    i = 2
    while await db.entries.find_one({"slug": slug}):
        slug = f"{base}-{i}"
        i += 1
    return slug


def public_entry(doc: dict) -> dict:
    """Strip private fields for public consumption."""
    return {
        "id": doc.get("id"),
        "slug": doc.get("slug"),
        "company_name": doc.get("company_name"),
        "company_domain": doc.get("company_domain", ""),
        "person_name": doc.get("person_name"),
        "person_title": doc.get("person_title", ""),
        "quote": doc.get("quote"),
        "statement_date": doc.get("statement_date", ""),
        "red_flag_score": doc.get("red_flag_score"),
        "sources": doc.get("sources", []),
        "approved_at": doc.get("approved_at"),
    }


async def get_current_moderator(request: Request) -> dict:
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    mod = await db.moderators.find_one({"email": session["email"], "active": True}, {"_id": 0})
    if not mod:
        raise HTTPException(status_code=403, detail="Not a moderator")
    return mod


# ----------------------------- Auth Routes -----------------------------
@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session id")

    async with httpx.AsyncClient(timeout=15) as hc:
        r = await hc.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": session_id})
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to validate session")
    data = r.json()
    email = data["email"]
    name = data.get("name", "")
    picture = data.get("picture", "")

    # Bootstrap: first ever login becomes the first moderator.
    mod_count = await db.moderators.count_documents({})
    if mod_count == 0:
        await db.moderators.insert_one({
            "email": email, "name": name, "picture": picture,
            "added_by": "bootstrap", "active": True, "created_at": now_iso(),
        })

    mod = await db.moderators.find_one({"email": email, "active": True}, {"_id": 0})
    if not mod:
        raise HTTPException(status_code=403, detail="This account is not authorized as a moderator.")

    # keep moderator profile fresh
    await db.moderators.update_one(
        {"email": email}, {"$set": {"name": name or mod.get("name", ""), "picture": picture or mod.get("picture", "")}}
    )

    session_token = data.get("session_token") or uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    await db.user_sessions.insert_one({
        "session_token": session_token,
        "email": email,
        "expires_at": expires_at.isoformat(),
        "created_at": now_iso(),
    })

    response.set_cookie(
        key="session_token", value=session_token, httponly=True,
        secure=True, samesite="none", path="/", max_age=SESSION_DAYS * 24 * 60 * 60,
    )
    return {"email": email, "name": name, "picture": picture}


@api_router.get("/auth/me")
async def auth_me(mod: dict = Depends(get_current_moderator)):
    return {"email": mod["email"], "name": mod.get("name", ""), "picture": mod.get("picture", "")}


@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"ok": True}


# ----------------------------- Public Routes -----------------------------
@api_router.get("/entries")
async def list_entries(search: Optional[str] = None, skip: int = 0, limit: int = 9):
    query = {"status": "approved"}
    if search and search.strip():
        rx = re.escape(search.strip())
        query["$or"] = [
            {"company_name": {"$regex": rx, "$options": "i"}},
            {"person_name": {"$regex": rx, "$options": "i"}},
            {"quote": {"$regex": rx, "$options": "i"}},
        ]
    total = await db.entries.count_documents(query)
    cursor = db.entries.find(query, {"_id": 0}).sort("approved_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(limit)
    return {"total": total, "items": [public_entry(d) for d in docs]}


@api_router.get("/entries/{slug}")
async def get_entry(slug: str):
    doc = await db.entries.find_one({"slug": slug, "status": "approved"}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")
    return public_entry(doc)


@api_router.post("/submissions")
async def create_submission(payload: SubmissionCreate):
    doc = {
        "id": str(uuid.uuid4()),
        "company_name": payload.company_name.strip(),
        "company_domain": (payload.company_domain or "").strip().replace("https://", "").replace("http://", "").strip("/"),
        "person_name": payload.person_name.strip(),
        "person_title": (payload.person_title or "").strip(),
        "quote": payload.quote.strip(),
        "statement_date": (payload.statement_date or "").strip(),
        "sources": [s.model_dump() for s in payload.sources],
        "submitter_email": (payload.submitter_email or "").strip(),
        "status": "pending",
        "red_flag_score": None,
        "slug": None,
        "rejection_reason": None,
        "created_at": now_iso(),
        "approved_at": None,
    }
    await db.entries.insert_one(doc)
    return {"ok": True, "id": doc["id"]}


# ----------------------------- Moderator Routes -----------------------------
@api_router.get("/mod/stats")
async def mod_stats(mod: dict = Depends(get_current_moderator)):
    live = await db.entries.count_documents({"status": "approved"})
    pending = await db.entries.count_documents({"status": "pending"})
    total = await db.entries.count_documents({})
    rejected = await db.entries.count_documents({"status": "rejected"})
    return {"live": live, "pending": pending, "total": total, "rejected": rejected}


@api_router.get("/mod/entries")
async def mod_list(status: Optional[str] = None, mod: dict = Depends(get_current_moderator)):
    query = {}
    if status:
        query["status"] = status
    docs = await db.entries.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"items": docs}


@api_router.post("/mod/entries/{entry_id}/approve")
async def approve_entry(entry_id: str, payload: ApproveRequest, mod: dict = Depends(get_current_moderator)):
    doc = await db.entries.find_one({"id": entry_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")

    score = max(1, min(5, payload.red_flag_score))
    update = {"red_flag_score": score, "status": "approved", "approved_at": now_iso(), "rejection_reason": None}
    for f in ["company_name", "company_domain", "person_name", "person_title", "quote", "statement_date"]:
        val = getattr(payload, f)
        if val is not None:
            update[f] = val
    if payload.sources is not None:
        update["sources"] = [s.model_dump() for s in payload.sources]

    if not doc.get("slug"):
        update["slug"] = await generate_unique_slug(
            update.get("person_name", doc["person_name"]),
            update.get("company_name", doc["company_name"]),
            update.get("statement_date", doc.get("statement_date", "")),
        )
    await db.entries.update_one({"id": entry_id}, {"$set": update})
    return {"ok": True}


@api_router.post("/mod/entries/{entry_id}/reject")
async def reject_entry(entry_id: str, payload: RejectRequest, mod: dict = Depends(get_current_moderator)):
    res = await db.entries.update_one(
        {"id": entry_id},
        {"$set": {"status": "rejected", "rejection_reason": payload.rejection_reason, "approved_at": None}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}


@api_router.post("/mod/entries/{entry_id}/unpublish")
async def unpublish_entry(entry_id: str, mod: dict = Depends(get_current_moderator)):
    res = await db.entries.update_one(
        {"id": entry_id}, {"$set": {"status": "pending", "approved_at": None}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}


@api_router.put("/mod/entries/{entry_id}")
async def update_entry(entry_id: str, payload: EntryUpdate, mod: dict = Depends(get_current_moderator)):
    doc = await db.entries.find_one({"id": entry_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")
    update = {}
    for f in ["company_name", "company_domain", "person_name", "person_title", "quote", "statement_date"]:
        val = getattr(payload, f)
        if val is not None:
            update[f] = val
    if payload.red_flag_score is not None:
        update["red_flag_score"] = max(1, min(5, payload.red_flag_score))
    if payload.sources is not None:
        update["sources"] = [s.model_dump() for s in payload.sources]
    if update:
        await db.entries.update_one({"id": entry_id}, {"$set": update})
    return {"ok": True}


@api_router.get("/mod/moderators")
async def list_moderators(mod: dict = Depends(get_current_moderator)):
    docs = await db.moderators.find({}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return {"items": docs, "me": mod["email"]}


@api_router.post("/mod/moderators")
async def add_moderator(payload: AddModerator, mod: dict = Depends(get_current_moderator)):
    email = payload.email.lower()
    existing = await db.moderators.find_one({"email": email})
    if existing:
        if not existing.get("active", True):
            await db.moderators.update_one({"email": email}, {"$set": {"active": True}})
            return {"ok": True}
        raise HTTPException(status_code=400, detail="Moderator already exists")
    await db.moderators.insert_one({
        "email": email, "name": "", "picture": "",
        "added_by": mod["email"], "active": True, "created_at": now_iso(),
    })
    return {"ok": True}


@api_router.delete("/mod/moderators/{email}")
async def remove_moderator(email: str, mod: dict = Depends(get_current_moderator)):
    email = email.lower()
    if email == mod["email"]:
        raise HTTPException(status_code=400, detail="You cannot remove yourself")
    count = await db.moderators.count_documents({"active": True})
    if count <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last moderator")
    await db.moderators.update_one({"email": email}, {"$set": {"active": False}})
    await db.user_sessions.delete_many({"email": email})
    return {"ok": True}


@api_router.get("/")
async def root():
    return {"message": "dontworkhere API"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
