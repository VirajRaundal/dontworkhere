"""dontworkhere backend application package.

The FastAPI app is assembled in ``server.py`` (kept as the uvicorn entrypoint,
``server:app``). This package holds the building blocks:

- ``config``        — environment + constants
- ``db``            — Mongo client/handle
- ``models``        — pydantic request/response models
- ``utils``         — slug/date/serialization helpers
- ``auth``          — session auth dependency + auth router
- ``audit``         — moderator action audit log
- ``notify``        — submitter email notifications (env-gated, optional)
- ``og``            — Open Graph share-image generation
- ``routes_public`` — public + submitter routes
- ``routes_mod``    — moderator-only routes
"""
