"""Shared helpers: timestamps, date parsing, slugs, and public serialization."""
import re
import uuid
from datetime import datetime, timezone

from .db import db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value) -> datetime:
    """Parse an ISO datetime that may end in 'Z' into a tz-aware UTC datetime.

    Python 3.9's ``datetime.fromisoformat`` rejects a trailing 'Z', so we
    normalize it. Naive values are assumed to be UTC.
    """
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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
        "tags": doc.get("tags", []),
        "views": doc.get("views", 0),
        "approved_at": doc.get("approved_at"),
    }
