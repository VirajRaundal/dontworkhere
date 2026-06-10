"""FastAPI entrypoint for dontworkhere.xyz.

Thin assembly layer — the building blocks live in the ``app`` package. Run with:
    uvicorn server:app --host 0.0.0.0 --port 8001
"""
import logging

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import auth, routes_mod, routes_public
from app.config import CORS_ORIGINS
from app.db import client, ensure_indexes

app = FastAPI(title="dontworkhere API")

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "dontworkhere API"}


api_router.include_router(auth.router)
api_router.include_router(routes_public.router)
api_router.include_router(routes_mod.router)

app.include_router(api_router)

# Also serve the sitemap at the conventional root path, not just under /api.
app.add_api_route("/sitemap.xml", routes_public.sitemap, methods=["GET"])

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def create_indexes():
    await ensure_indexes()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
