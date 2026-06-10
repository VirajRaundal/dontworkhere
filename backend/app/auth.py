"""Session authentication: the moderator dependency and the auth router."""
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .config import EMERGENT_SESSION_URL, SESSION_DAYS
from .db import db
from .utils import now_iso, parse_dt

router = APIRouter(prefix="/auth")


def _token_from(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    return token


async def get_current_moderator(request: Request) -> dict:
    token = _token_from(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    if parse_dt(session["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    mod = await db.moderators.find_one({"email": session["email"], "active": True}, {"_id": 0})
    if not mod:
        raise HTTPException(status_code=403, detail="Not a moderator")
    return mod


@router.post("/session")
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
        {"email": email},
        {"$set": {"name": name or mod.get("name", ""), "picture": picture or mod.get("picture", "")}},
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


@router.get("/me")
async def auth_me(mod: dict = Depends(get_current_moderator)):
    return {"email": mod["email"], "name": mod.get("name", ""), "picture": mod.get("picture", "")}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"ok": True}
