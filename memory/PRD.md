# PRD — dontworkhere.xyz (Community Accountability Directory)

## Original Problem Statement
A fun, community-powered website listing companies whose founders/leaders publicly said
objectionable things about work culture. Visitors search & browse "Red Flags"; anyone can
submit; moderators approve/reject before entries go public. Design: "Pixar meets Corporate
Satire" — navy (#0D1B2A) / coral (#FF4D4D) / cream (#FFF8F0) / gold (#FFD700), 🚩 motif.

## User Choices (locked)
- Auth: Emergent-managed Google OAuth (moderator-only). First login = founding moderator (bootstrap).
- Seed ~8 fictional/satirical sample entries.
- Mods can invite/remove other mods from the dashboard.
- Homepage browsing: infinite scroll.

## Architecture
- Frontend: React 19 + react-router 7 + Tailwind + framer-motion + sonner. Fonts: Nunito (display), DM Sans (body).
- Backend: FastAPI (`/api` prefix) + Motor/MongoDB. Session cookie (httpOnly, secure, samesite=none) or Bearer.
- Single `entries` collection with status (pending/approved/rejected); `moderators`; `user_sessions`.
- Logos: Clearbit (`logo.clearbit.com/{domain}`) with 🏢 fallback. Slugs: {person}-{company}-{year}, uniqueness-suffixed.

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

## Backlog
- P1: Email notification to submitter on approve/reject (Resend/SendGrid).
- P1: Dedicated rejected-reason field surfaced to public "appeal" flow; audit log of mod actions.
- P2: Categories/tags & filter chips; sort (newest / highest score); per-entry view counts.
- P2: OG image generation for shareable entry cards; sitemap for SEO.
- P2: Split server.py into routes/auth/models modules; 404 on unknown moderator delete.

## Next Tasks
- Gather user feedback on the MVP; prioritize email notifications + sorting/filtering next.
