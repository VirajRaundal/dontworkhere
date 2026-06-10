"""Public + submitter routes: browse, search, detail, submit, appeal, og, sitemap."""
import re
import uuid
from typing import Optional
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Response
from pymongo import ReturnDocument

from .config import PUBLIC_BASE_URL
from .db import db
from .models import AppealCreate, SubmissionCreate
from .og import render_og_png
from .utils import now_iso, public_entry

router = APIRouter()

SORTS = {
    "newest": [("approved_at", -1)],
    "oldest": [("approved_at", 1)],
    "highest": [("red_flag_score", -1), ("approved_at", -1)],
    "most_viewed": [("views", -1), ("approved_at", -1)],
}


def _approved_query(search=None, tag=None):
    """Shared filter for approved entries — used by the listing and the tag facets."""
    query = {"status": "approved"}
    if search and search.strip():
        rx = re.escape(search.strip())
        query["$or"] = [
            {"company_name": {"$regex": rx, "$options": "i"}},
            {"person_name": {"$regex": rx, "$options": "i"}},
            {"quote": {"$regex": rx, "$options": "i"}},
        ]
    if tag and tag.strip():
        query["tags"] = tag.strip()
    return query


@router.get("/entries")
async def list_entries(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    sort: str = "newest",
    skip: int = 0,
    limit: int = 9,
):
    query = _approved_query(search, tag)
    order = SORTS.get(sort, SORTS["newest"])
    total = await db.entries.count_documents(query)
    cursor = db.entries.find(query, {"_id": 0}).sort(order).skip(skip).limit(limit)
    docs = await cursor.to_list(limit)
    return {"total": total, "items": [public_entry(d) for d in docs]}


@router.get("/tags")
async def list_tags(search: Optional[str] = None):
    """Tags + counts among approved entries matching `search` (for filter chips).

    Counts reflect the current search so the facets stay in sync with results;
    they intentionally ignore any selected tag so the user can switch between tags.
    """
    pipeline = [
        {"$match": _approved_query(search)},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    rows = await db.entries.aggregate(pipeline).to_list(200)
    return {"items": [{"tag": r["_id"], "count": r["count"]} for r in rows if r["_id"]]}


@router.get("/entries/{slug}")
async def get_entry(slug: str):
    # Atomically count the view and return the updated doc.
    doc = await db.entries.find_one_and_update(
        {"slug": slug, "status": "approved"},
        {"$inc": {"views": 1}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")
    return public_entry(doc)


@router.get("/entries/{slug}/og.png")
async def entry_og_image(slug: str):
    doc = await db.entries.find_one({"slug": slug, "status": "approved"}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Entry not found")
    png = render_og_png(doc)
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.post("/submissions")
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
        "tags": payload.tags or [],
        "submitter_email": (payload.submitter_email or "").strip(),
        "status": "pending",
        "red_flag_score": None,
        "slug": None,
        "rejection_reason": None,
        "views": 0,
        "created_at": now_iso(),
        "approved_at": None,
    }
    await db.entries.insert_one(doc)
    return {"ok": True, "id": doc["id"]}


@router.post("/entries/{slug}/appeal")
async def submit_appeal(slug: str, payload: AppealCreate):
    """Public correction/dispute request against a published entry."""
    entry = await db.entries.find_one({"slug": slug, "status": "approved"}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.appeals.insert_one({
        "id": str(uuid.uuid4()),
        "entry_id": entry["id"],
        "slug": slug,
        "company_name": entry.get("company_name", ""),
        "message": payload.message.strip(),
        "email": (payload.email or "").strip(),
        "status": "open",
        "created_at": now_iso(),
    })
    return {"ok": True}


@router.get("/sitemap.xml")
async def sitemap():
    docs = await db.entries.find(
        {"status": "approved"}, {"_id": 0, "slug": 1, "approved_at": 1}
    ).sort("approved_at", -1).to_list(5000)

    urls = [
        (f"{PUBLIC_BASE_URL}/", None),
        (f"{PUBLIC_BASE_URL}/submit", None),
    ]
    for d in docs:
        if d.get("slug"):
            urls.append((f"{PUBLIC_BASE_URL}/entry/{d['slug']}", d.get("approved_at")))

    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{escape(loc)}</loc>")
        if lastmod:
            parts.append(f"    <lastmod>{escape(str(lastmod)[:10])}</lastmod>")
        parts.append("  </url>")
    parts.append("</urlset>")
    xml = "\n".join(parts)
    return Response(content=xml, media_type="application/xml")
