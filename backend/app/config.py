"""Environment-driven configuration and constants."""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ (parent of this app/ package)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Defaults keep imports safe during a build/trace where env isn't injected yet.
# Production MUST set MONGO_URL + DB_NAME (e.g. a MongoDB Atlas connection string).
# .strip() tolerates accidental surrounding quotes/whitespace from the dashboard.
MONGO_URL = (os.environ.get("MONGO_URL") or "mongodb://localhost:27017").strip().strip('"').strip("'").strip()
DB_NAME = (os.environ.get("DB_NAME") or "dontworkhere").strip().strip('"').strip("'").strip()
# Comma-separated allowed origins. In production this MUST be the explicit
# frontend origin(s) — browsers reject "*" together with credentialed (cookie) requests.
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

SESSION_DAYS = 7

# Public URL of the app — used for sitemap entries, share links, and the OAuth
# redirect URI. Falls back to the first concrete CORS origin, then localhost.
_first_origin = next((o for o in CORS_ORIGINS if o and o != "*"), "http://localhost:3000")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", _first_origin).rstrip("/")

# --- Google OAuth (moderator sign-in) ---
# Create an OAuth 2.0 Client (type: Web application) in Google Cloud Console and
# register the redirect URI: {PUBLIC_BASE_URL}/api/auth/google/callback
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Session cookie security. Keep true in production (HTTPS). Set COOKIE_SECURE=false
# only for local http testing (then the cookie uses SameSite=Lax instead of None).
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"

# --- Email notifications (all optional) ---
# If neither key is set, decision emails are logged and skipped (no-op) so the
# app runs fine locally without an email provider.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "dontworkhere <noreply@dontworkhere.xyz>")
