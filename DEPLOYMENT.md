# Deploying dontworkhere to Vercel

Everything runs on **one Vercel project**:

```
  https://your-app.vercel.app
  ├─ /            → React static build (frontend/build)         [Vercel static]
  ├─ /api/*       → FastAPI (backend/) as a Python function     [Vercel serverless]
  └─ /sitemap.xml → same FastAPI function
        │
        └─ MongoDB Atlas (managed, free M0 tier)
```

Frontend and API share one origin, so the moderator session cookie is first-party.
Moderator sign-in uses **your own Google OAuth** (no third-party auth broker).

## Already configured in the repo

- `vercel.json` — builds the frontend, exposes `api/index.py` as a function, routes `/api/*`
  + `/sitemap.xml` to it, and falls back all other routes to the SPA `index.html`.
- `api/index.py` + `api/requirements.txt` — lean serverless entry serving the FastAPI app.
- `.vercelignore` — keeps the upload small.

---

## Step 1 — MongoDB Atlas (database)

1. Create a free account at https://www.mongodb.com/atlas and a free **M0** cluster.
2. **Database Access** → add a database user (username + password).
3. **Network Access** → add IP `0.0.0.0/0` (Vercel functions have dynamic IPs).
4. **Connect → Drivers** → copy the connection string, e.g.
   `mongodb+srv://USER:PASSWORD@cluster0.xxxx.mongodb.net/?retryWrites=true&w=majority`
   This is your `MONGO_URL`. Pick any `DB_NAME` (e.g. `dontworkhere`).

## Step 2 — First deploy (to get your domain)

1. `git push` the repo to GitHub.
2. https://vercel.com → **Add New… → Project** → import the repo.
   - **Root Directory:** repo root · **Framework Preset:** *Other* (the `vercel.json` drives it).
3. Add the database env vars (Settings → Environment Variables): `MONGO_URL`, `DB_NAME`,
   and `PUBLIC_BASE_URL` (set to the URL Vercel gives you, e.g. `https://your-app.vercel.app`).
4. **Deploy.** The public site works immediately; moderator login is wired up in Step 3.

## Step 3 — Google OAuth credentials (moderator sign-in)

1. https://console.cloud.google.com → create/select a project.
2. **APIs & Services → OAuth consent screen** → External → fill app name + your email →
   add yourself under **Test users** (or Publish the app when ready).
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID** → *Web application*.
   - **Authorized redirect URI:** `https://your-app.vercel.app/api/auth/google/callback`
     (use your exact production domain; add your custom domain here too once you have one).
4. Copy the **Client ID** and **Client secret**.
5. In Vercel, add env vars and **redeploy**:

| Variable | Value |
|---|---|
| `MONGO_URL` | your Atlas connection string |
| `DB_NAME` | `dontworkhere` |
| `PUBLIC_BASE_URL` | `https://your-app.vercel.app` (must match the OAuth redirect domain) |
| `GOOGLE_CLIENT_ID` | from Step 3 |
| `GOOGLE_CLIENT_SECRET` | from Step 3 |
| `RESEND_API_KEY` *(optional)* | to actually send submitter emails |
| `EMAIL_FROM` *(optional)* | e.g. `dontworkhere <noreply@yourdomain>` |

Do **not** set `REACT_APP_BACKEND_URL` or `CORS_ORIGINS` (same-origin needs neither). Do **not**
set `COOKIE_SECURE` in production (it defaults to secure cookies over HTTPS).

## Step 4 — Seed data + make yourself a moderator

Run locally, pointed at Atlas (one-time):

```bash
cd backend
MONGO_URL="<your-atlas-url>" DB_NAME="dontworkhere" ./.venv/bin/python seed.py

# Register your moderator account (no separate "admin" role — moderators are admins):
mongosh "<your-atlas-url>" --eval '
  db.getSiblingDB("dontworkhere").moderators.updateOne(
    { email: "virajwork8@gmail.com" },
    { $set: { email: "virajwork8@gmail.com", name: "Viraj", active: true,
              added_by: "bootstrap", created_at: new Date().toISOString() } },
    { upsert: true })'
```

(Or skip the second command and just be the **first** to sign in at `/mod/login` — the first
Google login bootstraps the founding moderator.)

## Step 5 — Verify

- `https://your-app.vercel.app` loads with seeded entries; search / sort / tags work.
- `https://your-app.vercel.app/api/` → `{"message":"dontworkhere API"}`; `/sitemap.xml` → XML.
- An entry's `…/api/entries/<slug>/og.png` → a PNG.
- **Moderator login:** `/mod/login` → Continue with Google → sign in as `virajwork8@gmail.com`
  → you land on `/mod/dashboard`. (A non-moderator account bounces back with an error toast.)

---

## Caveats & troubleshooting

- **OAuth redirect mismatch** (`redirect_uri_mismatch`): the URI in Google Console must exactly
  equal `{PUBLIC_BASE_URL}/api/auth/google/callback`. Preview deployments have different URLs —
  register them too, or just test login on the production/custom domain.
- **Consent screen "access blocked":** while the app is in *Testing*, only emails listed under
  **Test users** can sign in. Add moderators there, or publish the consent screen.
- **Cold starts:** the function sleeps when idle; the first request after idle takes ~1–3s.
- **Motor + serverless:** if you ever see "event loop is closed" under load, make the Mongo
  client in `backend/app/db.py` lazy (per-request). Not expected at low traffic.
- **OG image fonts:** Vercel's runtime may lack the TrueType fonts `backend/app/og.py` looks
  for (falls back to a plain bitmap font). Commit a `.ttf` and add its path to `_FONT_CANDIDATES`
  for crisp images.
- **Function size:** keep `api/requirements.txt` lean — the full `backend/requirements.txt`
  exceeds Vercel's 250 MB limit (it is `.vercelignore`d).

## Custom domain

Vercel **Settings → Domains** → add your domain. Then **update `PUBLIC_BASE_URL`** to it, add
`https://yourdomain/api/auth/google/callback` to the Google OAuth redirect URIs, and redeploy.

## Local moderator login

The session cookie is `Secure`, so it won't persist over `http://localhost`. To test the full
Google flow locally, either run behind HTTPS, or set `COOKIE_SECURE=false` in `backend/.env`
and a Google OAuth client whose redirect URI points at your local backend. For everyday local
dev, seed a session + use a `Bearer` token instead (see `auth_testing.md`).

## Alternative: separate backend host

Prefer an always-on backend (no cold starts)? Deploy `backend/` to Render/Railway/Fly
(`uvicorn server:app --host 0.0.0.0 --port $PORT`) and keep the frontend on Vercel — then set
`REACT_APP_BACKEND_URL` + `CORS_ORIGINS`. Note cross-origin cookies are blocked by Safari, so
same-origin (all-on-Vercel) is the more robust default.
