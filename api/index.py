"""Vercel Python serverless entry point.

Vercel's Python runtime serves the exported ASGI ``app`` object. The actual
application lives in ``backend/`` (server.py + the app/ package), which is
bundled into the function via ``includeFiles`` in vercel.json. We add it to
sys.path so ``from server import app`` resolves.
"""
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND_DIR)

from server import app  # noqa: E402  (ASGI app Vercel will serve)

__all__ = ["app"]
