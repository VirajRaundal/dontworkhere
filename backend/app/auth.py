"""Session authentication: the moderator dependency and Google OAuth routes.

Sign-in uses a standard Google OAuth 2.0 Authorization Code flow:
  GET /api/auth/google/login     -> redirect to Google consent
  GET /api/auth/google/callback  -> exchange code, verify moderator, set cookie

Only emails present (and active) in the ``moderators`` collection may sign in;
the first-ever login bootstraps the founding moderator.
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from .config import (
    COOKIE_SECURE,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    PUBLIC_BASE_URL,
    SESSION_DAYS,
)
from .db import db
from .utils import now_iso, parse_dt

router = APIRouter(prefix="/auth")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _redirect_uri() -> str:
    return f"{PUBLIC_BASE_URL}/api/auth/google/callback"


def _session_cookie_kwargs() -> dict:
    # SameSite=None requires Secure; for local http testing fall back to Lax.
    if COOKIE_SECURE:
        return dict(httponly=True, secure=True, samesite="none", path="/")
    return dict(httponly=True, secure=False, samesite="lax", path="/")


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


@router.get("/google/login")
async def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    resp = RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")
    # CSRF guard — verified on callback. Lax so it survives the top-level return from Google.
    resp.set_cookie("oauth_state", state, max_age=600, httponly=True,
                    secure=COOKIE_SECURE, samesite="lax", path="/")
    return resp


@router.get("/google/callback")
async def google_callback(request: Request, code: str = "", state: str = ""):
    if not code or not state or state != request.cookies.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient(timeout=15) as hc:
        tok = await hc.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        })
        if tok.status_code != 200:
            raise HTTPException(status_code=401, detail="Token exchange failed")
        access_token = tok.json().get("access_token")
        ui = await hc.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    if ui.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to fetch Google profile")

    info = ui.json()
    email = (info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Unverified Google account")
    name = info.get("name", "")
    picture = info.get("picture", "")

    # Bootstrap: first ever login becomes the founding moderator.
    if await db.moderators.count_documents({}) == 0:
        await db.moderators.insert_one({
            "email": email, "name": name, "picture": picture,
            "added_by": "bootstrap", "active": True, "created_at": now_iso(),
        })

    mod = await db.moderators.find_one({"email": email, "active": True}, {"_id": 0})
    if not mod:
        # Not authorized — bounce back to login with a flag the page can show.
        resp = RedirectResponse(f"{PUBLIC_BASE_URL}/mod/login?error=unauthorized")
        resp.delete_cookie("oauth_state", path="/")
        return resp

    await db.moderators.update_one(
        {"email": email},
        {"$set": {"name": name or mod.get("name", ""), "picture": picture or mod.get("picture", "")}},
    )

    session_token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    await db.user_sessions.insert_one({
        "session_token": session_token,
        "email": email,
        "expires_at": expires_at.isoformat(),
        "created_at": now_iso(),
    })

    resp = RedirectResponse(f"{PUBLIC_BASE_URL}/mod/dashboard")
    resp.set_cookie("session_token", session_token,
                    max_age=SESSION_DAYS * 24 * 60 * 60, **_session_cookie_kwargs())
    resp.delete_cookie("oauth_state", path="/")
    return resp


@router.get("/me")
async def auth_me(mod: dict = Depends(get_current_moderator)):
    return {"email": mod["email"], "name": mod.get("name", ""), "picture": mod.get("picture", "")}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    response.delete_cookie("session_token", path="/",
                           samesite="none" if COOKIE_SECURE else "lax", secure=COOKIE_SECURE)
    return {"ok": True}
