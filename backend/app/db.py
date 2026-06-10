"""MongoDB connection (shared async client + database handle)."""
import logging

from motor.motor_asyncio import AsyncIOMotorClient

from .config import DB_NAME, MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

logger = logging.getLogger(__name__)


async def ensure_indexes():
    """Create the indexes the app relies on. Idempotent; safe to run on every startup."""
    try:
        # slug is unique among published entries (pending entries have slug=null)
        await db.entries.create_index(
            "slug", unique=True, partialFilterExpression={"slug": {"$type": "string"}}
        )
        await db.entries.create_index([("status", 1), ("approved_at", -1)])  # public listing
        await db.entries.create_index([("status", 1), ("created_at", -1)])   # mod queue
        await db.entries.create_index([("status", 1), ("tags", 1)])          # tag facets/filter
        await db.user_sessions.create_index("session_token", unique=True)    # every authed request
        await db.moderators.create_index("email", unique=True)
        await db.audit_log.create_index([("created_at", -1)])
        await db.appeals.create_index([("status", 1), ("created_at", -1)])
    except Exception as e:  # never block startup on index creation
        logger.warning("ensure_indexes: %s", e)
