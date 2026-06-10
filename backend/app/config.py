"""Environment-driven configuration and constants."""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ (parent of this app/ package)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
# Comma-separated allowed origins. In production this MUST be the explicit
# frontend origin(s) — browsers reject "*" together with credentialed (cookie) requests.
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_DAYS = 7

# Public URL of the frontend — used for sitemap entries and share links.
# Falls back to the first concrete CORS origin, then localhost.
_first_origin = next((o for o in CORS_ORIGINS if o and o != "*"), "http://localhost:3000")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", _first_origin).rstrip("/")

# --- Email notifications (all optional) ---
# If neither key is set, decision emails are logged and skipped (no-op) so the
# app runs fine locally without an email provider.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "dontworkhere <noreply@dontworkhere.xyz>")
