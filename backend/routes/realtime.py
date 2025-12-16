"""Real‑time streaming endpoints.

This router defines a simple Server‑Sent Events (SSE) endpoint to
demonstrate how real‑time data can be streamed to the frontend.  The
endpoint is designed to be self‑contained and not depend on the trading
engine or AI subsystems.  If the SSE feature is disabled via
`ENABLE_REALTIME=false` in the environment, this router can simply be
omitted from the server's include list.
"""

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/realtime", tags=["RealTime"])


async def _event_generator():
    """Yield periodic server‑sent events."""
    while True:
        # Emit a JSON timestamp event every 5 seconds.  Clients listening
        # to the /events endpoint will receive these messages.
        yield f"data: {{\"timestamp\": \"{datetime.now(timezone.utc).isoformat()}\"}}\n\n"
        await asyncio.sleep(5)


@router.get("/events")
async def realtime_events() -> StreamingResponse:
    """Server‑Sent Events endpoint for real‑time updates."""
    return StreamingResponse(_event_generator(), media_type="text/event-stream")