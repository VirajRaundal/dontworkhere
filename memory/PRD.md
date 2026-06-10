# PRD — dontworkhere.xyz (Community Accountability Directory)

## Original Problem Statement
A fun, community-powered website listing companies whose founders/leaders publicly said
objectionable things about work culture. Visitors search & browse "Red Flags"; anyone can
submit; moderators approve/reject before entries go public. Design: "Pixar meets Corporate
Satire" — navy (#0D1B2A) / coral (#FF4D4D) / cream (#FFF8F0) / gold (#FFD700), 🚩 motif.

## User Choices (locked)
- Auth: self-owned Google OAuth (moderator-only), server-side Authorization Code flow. First login = founding moderator (bootstrap).
- Seed ~8 fictional/satirical sample entries.
- Mods can invite/remove other mods from the dashboard.
- Homepage browsing: infinite scroll.

## Architecture
- Frontend: React 19 + react-router 7 + Tailwind + framer-motion + sonner. Fonts: Nunito (display), DM Sans (body).
- Backend: FastAPI (`/api` prefix) + Motor/MongoDB. Session cookie (httpOnly, secure, samesite=none) or Bearer.
  Split into an `app/` package: `config`, `db`, `models`, `utils`, `auth`, `audit`, `notify`, `og`,
  `routes_public`, `routes_mod`. `server.py` stays the uvicorn entrypoint (`server:app`).
- Collections: `entries` (status pending/approved/rejected; carries `tags[]` + `views`); `moderators`;
  `user_sessions`; `audit_log` (every mod action); `appeals` (public correction requests).
- Logos: Clearbit (`logo.clearbit.com/{domain}`) with 🏢 fallback. Slugs: {person}-{company}-{year}, uniqueness-suffixed.
- OG share images rendered server-side with Pillow at `/api/entries/{slug}/og.png`; `sitemap.xml` at root + `/api`.

## Environment variables (backend/.env)
- Required: `MONGO_URL`, `DB_NAME`. Optional: `CORS_ORIGINS` (csv), `PUBLIC_BASE_URL` (frontend origin for
  sitemap/share/email links — defaults to first CORS origin then localhost:3000).
- Email (optional; no-op + logged if unset): `RESEND_API_KEY` **or** `SENDGRID_API_KEY`, plus `EMAIL_FROM`.
- Frontend `.env`: `REACT_APP_BACKEND_URL`.

## User Personas
1. Visitor — browse/search the directory.
2. Submitter — report a quote (no login).
3. Moderator — Google-authed; approve/reject/edit/score, manage mods.

## Implemented (2026-06-08)
- Public homepage: hero "Know Before You Go.", confetti flags, live debounced search, infinite scroll, Red Flag cards.
- Submission form: dynamic add/remove sources (max 10), validation (quote ≥20, ≥1 http(s) source), date picker, confirmation screen.
- Entry detail `/entry/:slug`: big italic quote, logo, score, source link-buttons (new tab), share/copy.
- Moderator: Google login `/mod/login`, protected `/mod/dashboard` with stats, tabs (pending/approved/rejected/moderators), approve+score / reject+reason / edit modal / unpublish, add/remove moderators.
- 8 seeded fictional entries. Tested: 22/22 backend + all frontend flows pass.

## Implemented (2026-06-10) — backlog + cleanup sweep
- Backend refactor: monolithic `server.py` (445 lines) split into the `app/` package (see Architecture).
- Browse: `sort` (newest / highest / most_viewed / oldest) + `tag` filter on `GET /api/entries`;
  `GET /api/tags` (tag + count) powers homepage filter chips. Sort dropdown + chips on Home.
- Tags: free-form (max 6) on submit + editor; shown on cards and entry detail; curated suggestions.
- Per-entry view counts: `$inc` on entry fetch; surfaced on cards + detail.
- Audit log: `audit_log` records approve/reject/unpublish/edit/add-mod/remove-mod/reactivate/resolve;
  `GET /api/mod/audit` + dashboard "Activity Log" tab.
- Email notifications: provider-agnostic (Resend → SendGrid → log no-op) on approve/reject; never blocks moderation.
- Appeals: public `POST /api/entries/{slug}/appeal`; `GET /api/mod/appeals` + dashboard "Appeals" tab with resolve;
  rejection reason delivered to submitter via the rejection email.
- OG image: Pillow-rendered 1200×630 PNG per entry; `og:image`/twitter meta injected on the detail page.
- Sitemap: `GET /sitemap.xml` (+ `/api/sitemap.xml`).
- Cleanup: 404 on unknown-moderator delete; `{reactivated: true}` on mod reactivation; `Z`-suffix datetime hardening.
- Tested: 32/32 backend (10 new) + production build clean; new UI verified in the running app.

## Backlog
- P1: Wire a real email provider key in prod (Resend/SendGrid) and verify deliverability end-to-end.
- P2: True crawler-facing OG/SEO — meta tags are injected client-side; add SSR/prerender so unfurlers see them.
- P2: Rate-limit / spam-guard public submissions + appeals; audit-log pagination & filters.
- P2: Per-entry view-count dedupe (currently increments every fetch); sort by trending.

## Next Tasks
- Gather user feedback on the MVP; prioritize prod email keys + SSR for OG/SEO next.
