"""System routes for basic ping and status endpoints.

This module defines a minimal router that exposes system‑wide ping endpoints.  Having a
dedicated file ensures that the server can mount `/api/system/ping` without
conflicting with other route prefixes and satisfies health checks used by
deployment scripts.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

# Prefix ensures final paths begin with /api/system when mounted without an
# additional prefix.
router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/ping")
async def system_ping() -> dict:
    """Return a simple heartbeat response for system health checks."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }