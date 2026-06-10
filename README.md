# dontworkhere

A community-powered accountability directory of the things bosses really said about
work culture. Visitors browse and search "Red Flags"; anyone can submit a quote;
moderators approve / reject / score before entries go public.

## Stack

- **Frontend** — React 19 (CRA + CRACO), react-router 7, Tailwind, framer-motion, sonner.
- **Backend** — FastAPI (`/api` prefix), Motor / MongoDB. Auth via Emergent-managed Google
  OAuth (portable — works from any origin) + an httpOnly session cookie (or `Bearer` token).
- **Backend package layout** (`backend/app/`): `config`, `db`, `models`, `utils`, `auth`,
  `audit`, `notify`, `og`, `routes_public`, `routes_mod`. `server.py` is the ASGI entrypoint.

## Features

Public browse with live search, sort (newest / highest / most-viewed / oldest) and tag
filter chips; per-entry view counts; submission form with sources + tags; entry pages with
OG share images and a "request a correction" appeal flow. Moderator dashboard: approve /
reject / edit / score / unpublish, manage moderators, appeals queue, and an activity log.
Optional submitter email on approve/reject. `sitemap.xml` for SEO.

## Local development

Requires MongoDB running locally (e.g. `brew services start mongodb-community`).

```bash
# Backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt   # or the lean api/requirements.txt
printf 'MONGO_URL=mongodb://localhost:27017\nDB_NAME=dontworkhere\nCORS_ORIGINS=http://localhost:3000\n' > .env
./.venv/bin/python seed.py                 # 8 fictional sample entries
./.venv/bin/uvicorn server:app --port 8001 --reload

# Frontend (separate terminal)
cd frontend
printf 'REACT_APP_BACKEND_URL=http://localhost:8001\n' > .env
yarn install && yarn start                 # http://localhost:3000
```

Moderator login needs your email in the `moderators` collection (the first-ever Google
login auto-becomes the founding moderator). The Secure/SameSite=None cookie won't persist
over `http://localhost`, so for local API testing seed a session and use a `Bearer` token —
see `auth_testing.md`.

## Environment variables

| Variable | Where | Required | Notes |
|---|---|---|---|
| `MONGO_URL` | backend | ✅ | MongoDB connection string (Atlas in prod) |
| `DB_NAME` | backend | ✅ | Database name |
| `PUBLIC_BASE_URL` | backend | prod | Public site URL — used in sitemap + email links |
| `CORS_ORIGINS` | backend | if cross-origin | Comma-separated origins; not needed when frontend + API are same-origin |
| `RESEND_API_KEY` / `SENDGRID_API_KEY` | backend | optional | Enables submitter emails (no-op + logged if unset) |
| `EMAIL_FROM` | backend | optional | From address for emails |
| `REACT_APP_BACKEND_URL` | frontend | optional | Leave **unset** when API is same-origin (`/api`); set to the backend URL otherwise |

## Tests

```bash
cd backend
REACT_APP_BACKEND_URL=http://127.0.0.1:8001 ./.venv/bin/pytest tests/ -q   # 33 tests
```

## Deploying

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for the full Vercel + MongoDB Atlas runbook.
