"""Pydantic request models."""
import re
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator

MAX_TAGS = 6


def _clean_tags(v):
    if not v:
        return []
    out = []
    for t in v:
        t = (t or "").strip()
        if t and t not in out:
            out.append(t)
    if len(out) > MAX_TAGS:
        raise ValueError(f"Maximum {MAX_TAGS} tags allowed")
    return out


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
    tags: Optional[List[str]] = []
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

    @field_validator("tags")
    @classmethod
    def tags_ok(cls, v):
        return _clean_tags(v)


class ApproveRequest(BaseModel):
    red_flag_score: int = 3
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    person_name: Optional[str] = None
    person_title: Optional[str] = None
    quote: Optional[str] = None
    statement_date: Optional[str] = None
    sources: Optional[List[Source]] = None
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def tags_ok(cls, v):
        return None if v is None else _clean_tags(v)


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
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def tags_ok(cls, v):
        return None if v is None else _clean_tags(v)


class AddModerator(BaseModel):
    email: EmailStr


class AppealCreate(BaseModel):
    """A public correction/appeal request against an entry."""
    message: str
    email: Optional[str] = ""

    @field_validator("message")
    @classmethod
    def message_ok(cls, v):
        v = (v or "").strip()
        if len(v) < 10:
            raise ValueError("Please describe the issue (at least 10 characters)")
        return v
