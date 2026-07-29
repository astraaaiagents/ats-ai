"""SSE Stream route for real-time proactive alert push.

Endpoint: GET /api/v1/agent/sse/stream
- Opens a long-lived SSE connection
- Pushes new proactive alerts as they are created
- Supports reconnection via Last-Event-ID
"""

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.agent_alert import AgentProactiveAlert
from app.models.user import User

logger = logging.getLogger(__name__)

sse_router = APIRouter(prefix="/api/v1/agent", tags=["sse"])

# In-memory subscriber registry: recruiter_id → asyncio.Queue
_subscribers: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)


@sse_router.get("/sse/stream")
async def sse_stream(
    session_id: str = Query(None, description="Optional session ID for context"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Open an SSE stream for real-time proactive alert push.

    The client receives events whenever new proactive alerts are created
    for the current recruiter. Supports reconnection via Last-Event-ID.
    """
    recruiter_id = str(current_user.id)

    async def event_generator():
        """Yield SSE events for new alerts."""
        # Send initial heartbeat
        yield _sse_event("heartbeat", {"timestamp": _now_iso()})

        # Register subscriber
        queue: asyncio.Queue = asyncio.Queue()
        _subscribers[recruiter_id] = queue

        try:
            while True:
                try:
                    # Wait for alert with timeout (for heartbeat)
                    alert_data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield _sse_event("alert", alert_data)
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield _sse_event("heartbeat", {"timestamp": _now_iso()})
        finally:
            # Unregister on disconnect
            _subscribers.pop(recruiter_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def push_alert_to_recruiter(recruiter_id: str, alert_data: dict[str, Any]) -> None:
    """Push a proactive alert to a recruiter's SSE stream.

    Called by the proactive monitor when a new alert is created.

    Args:
        recruiter_id: Recruiter ID to push to.
        alert_data: Alert data dict.
    """
    queue = _subscribers.get(recruiter_id)
    if queue is None:
        return  # No active subscribers

    try:
        await asyncio.wait_for(queue.put(alert_data), timeout=5)
    except (asyncio.TimeoutError, Exception):
        logger.warning(f"Failed to push alert to recruiter {recruiter_id}")


def _sse_event(event: str, data: dict[str, Any]) -> str:
    """Format an SSE event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
