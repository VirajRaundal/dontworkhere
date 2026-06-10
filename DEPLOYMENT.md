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

Frontend and API share one origin, so the moderator session cookie is first-party (no CORS,
no third-party-cookie issues). The Google OAuth is portable — it redirects back to whatever
origin you're served from.

## Already configured in the repo

- `vercel.json` — builds the frontend, exposes `api/index.py` as a function, routes `/api/*`
  + `/sitemap.xml` to it, and falls back all other routes to the SPA `index.html`.
- `api/index.py` — Vercel entry that serves the FastAPI ASGI `app` (bundles `backend/**`).
- `api/requirements.txt` — lean dependency set for the function.
- `.vercelignore` — keeps the upload small.

You only need to do the steps below — no code changes.

---

## Step 1 — MongoDB Atlas (database)

1. Create a free account at https://www.mongodb.com/atlas and a free **M0** cluster.
2. **Database Access** → add a database user (username + password).
3. **Network Access** → add IP `0.0.0.0/0` (Vercel functions have dynamic IPs).
4. **Connect** → "Drivers" → copy the connection string, e.g.
   `mongodb+srv://USER:PASSWORD@cluster0.xxxx.mongodb.net/?retryWrites=true&w=majority`
   This is your `MONGO_URL`. Pick any `DB_NAME` (e.g. `dontworkhere`).

## Step 2 — Push the repo to GitHub

```bash
git push -u origin claude/gracious-pike-2b2e77      # or merge to main and push that
```

## Step 3 — Import into Vercel

1. https://vercel.com → **Add New… → Project** → import the GitHub repo.
2. **Root Directory:** repo root (leave as-is — `vercel.json` lives here).
3. **Framework Preset:** *Other* (the `vercel.json` drives the build).
4. Leave Build/Output settings empty — `vercel.json` provides them.

## Step 4 — Environment variables

In the Vercel project → **Settings → Environment Variables**, add (Production + Preview):

| Variable | Value |
|---|---|
| `MONGO_URL` | your Atlas connection string |
| `DB_NAME` | `dontworkhere` |
| `PUBLIC_BASE_URL` | `https://your-app.vercel.app` (set after you know the domain) |
| `RESEND_API_KEY` *(optional)* | a Resend key, to actually send submitter emails |
| `EMAIL_FROM` *(optional)* | e.g. `dontworkhere <noreply@yourdomain>` |

Do **not** set `REACT_APP_BACKEND_URL` — leaving it unset makes the frontend call the
same-origin `/api`. Do **not** set `CORS_ORIGINS` — same-origin needs no CORS.

## Step 5 — Deploy

Click **Deploy**. Vercel builds the frontend and the Python function. When it finishes,
note the domain and update `PUBLIC_BASE_URL` to match, then redeploy.

## Step 6 — Seed data + make yourself a moderator

Run these locally, pointed at Atlas (one-time):

```bash
# sample entries
cd backend
MONGO_URL="<your-atlas-url>" DB_NAME="dontworkhere" ./.venv/bin/python seed.py

# register your moderator account (there is no separate "admin" role — moderators are admins)
mongosh "<your-atlas-url>" --eval '
  db.getSiblingDB("dontworkhere").moderators.updateOne(
    { email: "virajwork8@gmail.com" },
    { $set: { email: "virajwork8@gmail.com", name: "Viraj", active: true,
              added_by: "bootstrap", created_at: new Date().toISOString() } },
    { upsert: true })'
```

(Alternatively: skip the moderator command and just be the **first** person to log in at
`/mod/login` — the first-ever Google login auto-becomes the founding moderator.)

## Step 7 — Verify

- `https://your-app.vercel.app` loads, shows seeded entries, search/sort/tags work.
- `https://your-app.vercel.app/api/` returns `{"message":"dontworkhere API"}`.
- `https://your-app.vercel.app/sitemap.xml` returns XML.
- An entry's `…/api/entries/<slug>/og.png` returns a PNG.
- **Moderator login:** go to `/mod/login` → Continue with Google → sign in as
  `virajwork8@gmail.com` → you land on `/mod/dashboard`. ⚠️ See the OAuth note below.

---

## Caveats & troubleshooting

- **⚠️ OAuth redirect (verify first):** login redirects to `auth.emergentagent.com` and back
  to your Vercel origin. This is an Emergent-managed service; it works from arbitrary origins
  in the app's design. If sign-in fails to return to your domain, Emergent is restricting the
  redirect — you'd then swap `handleLogin` in `frontend/src/pages/ModLogin.jsx` and
  `backend/app/auth.py` for your own Google OAuth client. Verify this before relying on it.
- **Cold starts:** the serverless function sleeps when idle; the first request after idle
  takes ~1–3s (Mongo connect + import). Fine for this traffic profile.
- **Motor + serverless:** if you ever see "event loop is closed" errors under load, switch the
  Mongo client in `backend/app/db.py` to be created lazily per request. Not expected at low traffic.
- **OG image fonts:** Vercel's runtime may lack the TrueType fonts `backend/app/og.py` looks
  for, so images fall back to a plain bitmap font. To make them crisp, commit a `.ttf` into the
  repo and add its path to `_FONT_CANDIDATES` in `og.py`.
- **Function size:** keep `api/requirements.txt` lean — the full `backend/requirements.txt`
  (litellm/pandas/etc.) would exceed Vercel's 250 MB unzipped limit. It is `.vercelignore`d.
- **Atlas connection refused:** confirm Network Access allows `0.0.0.0/0` and the user/password
  in `MONGO_URL` are URL-encoded.

## Custom domain

Vercel **Settings → Domains** → add your domain. Then update `PUBLIC_BASE_URL` to it and
redeploy. Because the API is same-origin, nothing else changes.

## Alternative: separate backend host

If you prefer the backend as a always-on server (no cold starts), deploy `backend/` to
Render/Railway/Fly with start command `uvicorn server:app --host 0.0.0.0 --port $PORT` and
keep only the frontend on Vercel. You'd then set `REACT_APP_BACKEND_URL` to the backend URL
and `CORS_ORIGINS` to the Vercel origin — but note cross-origin cookies are blocked by Safari,
so same-origin (all-on-Vercel) is the more robust default.
