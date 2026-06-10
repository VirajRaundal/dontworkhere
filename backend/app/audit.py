"""Append-only audit log of moderator actions."""
import uuid
from typing import List, Optional

from .db import db
from .utils import now_iso


async def record_action(
    actor: str,
    action: str,
    target_type: str = "entry",
    target_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> None:
    """Record a single moderator action. Best-effort: never raise into a request."""
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor": actor,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "meta": meta or {},
            "created_at": now_iso(),
        })
    except Exception:
        # Auditing must not break the underlying operation.
        pass


async def list_actions(limit: int = 100) -> List[dict]:
    return await db.audit_log.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
