import json
import logging

"""Agent Gateway API routes.

Endpoints for the agent-first recruiter portal:
- POST /api/v1/agent/conversation — send message, stream response via SSE
- GET /api/v1/agent/conversation/{session_id} — retrieve conversation history
- GET /api/v1/agent/preferences — read recruiter preferences
- PUT /api/v1/agent/preferences — update explicit preferences
- GET /api/v1/agent/proactive/alerts — get proactive alerts
- GET /api/v1/agent/action-log — EU AI Act audit trail
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.middleware.error_handler import AppException
from app.middleware.pagination import PaginationParams, paginated_response
from app.models.agent_action import AgentAction
from app.models.agent_alert import AgentProactiveAlert
from app.models.agent_conversation import AgentConversationMessage, AgentConversationSession
from app.models.recruiter_preference import RecruiterPreference
from app.models.user import User
from app.schemas.agent import (
    ActionLogEntry,
    ActionLogResponse,
    AgentMessageResponse,
    ConversationHistoryResponse,
    ConversationRequest,
    ErrorResponse,
    PreferenceResponse,
    PreferenceUpdate,
    ProactiveAlertResponse,
    ProactiveAlertsResponse,
)
from app.services import agent as agent_service

agent_router = APIRouter(prefix="/agent", tags=["agent"])


# --- POST /conversation (SSE streaming) ---


def sse_event(event: str, data: dict) -> str:
    """Format a SSE event."""
    import json
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def conversation_stream(
    body: ConversationRequest,
    db: AsyncSession,
    current_user: User,
) -> AsyncGenerator[str, None]:
    """Stream agent response via Server-Sent Events.

    Event sequence:
    1. message_start — session ID and timestamp
    2. content — text chunks (may be multiple)
    3. card — structured cards (candidate, job, alert, summary, preference)
    4. action — action buttons
    5. message_end — confidence, sources, message ID
    """
    from datetime import datetime, timezone

    recruiter_id = str(current_user.id)
    org_id = str(current_user.organization_id)

    # Step 1: Get or create session
    session = await agent_service.get_or_create_session(
        db, recruiter_id, body.session_id,
    )
    session_id = str(session.id)

    # Emit message_start
    yield sse_event("message_start", {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Step 2: Save user message
    user_msg = AgentConversationMessage(
        session_id=session.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    # Step 3: Log action
    await agent_service.log_action(
        db=db,
        recruiter_id=recruiter_id,
        session_id=session_id,
        action_type="intent_parse",
        agent_name="orchestrator",
        input_data=json.dumps({"message": body.message[:500]}),
        output_data=json.dumps({"status": "processing"}),
    )

    # Step 4: Load preferences
    prefs = await agent_service.get_preferences(db, recruiter_id)

    # Step 5: Call Orchestrator agent
    from app.services.agent_orchestrator import run_orchestrator

    try:
        orchestrator_result = await run_orchestrator(
            message=body.message,
            db=db,
            org_id=org_id,
            recruiter_id=recruiter_id,
            session_id=session_id,
            job_id=None,
            preferences=prefs,
        )
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.error(f"Orchestrator error: {exc}", exc_info=True)
        # Graceful degradation: return a fallback response
        orchestrator_result = {
            "response": "AI temporarily unavailable — please use manual search.",
            "cards": [],
            "actions": [],
            "sources": [],
            "confidence": 0.0,
            "intent": "general_conversation",
        }

    agent_content = orchestrator_result.get("response", "I'm here to help.")
    cards = orchestrator_result.get("cards", [])
    actions = orchestrator_result.get("actions", [])
    confidence = orchestrator_result.get("confidence", 0.5)
    sources = orchestrator_result.get("sources", [])
    if not sources:
        sources = [{"type": "internal_db", "identifier": "orchestrator", "timestamp": datetime.now(timezone.utc).isoformat()}]

    # Emit content token by token to simulate true streaming
    import asyncio
    words = agent_content.split(" ")
    for i, word in enumerate(words):
        token = word + (" " if i < len(words) - 1 else "")
        yield sse_event("content", {"type": "text", "content": token})
        await asyncio.sleep(0.01)

    # Emit cards
    for card in cards:
        yield sse_event("card", card)

    # Emit actions
    for action in actions:
        yield sse_event("action", action)

    # Save agent message
    agent_msg = AgentConversationMessage(
        session_id=session.id,
        role="agent",
        content=agent_content,
        cards=cards,
        actions=actions,
        sources=sources,
        confidence=confidence,
    )
    db.add(agent_msg)
    await db.flush()

    # Log agent action
    await agent_service.log_action(
        db=db,
        recruiter_id=recruiter_id,
        session_id=session_id,
        action_type="source",
        agent_name="orchestrator",
        input_data=json.dumps({"message": body.message[:500]}),
        output_data=json.dumps({"content": agent_content[:500], "cards": len(cards)}),
    )

    # Emit message_end
    yield sse_event("message_end", {
        "confidence": confidence,
        "sources": sources,
        "message_id": str(agent_msg.id),
    })


@agent_router.post(
    "/conversation",
    responses={200: {"content": {"text/event-stream": {}}}, 400: {"model": ErrorResponse}},
)
async def conversation(
    body: ConversationRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the agent and receive a streamed response via SSE.

    If session_id is provided, the message is added to that session.
    If session_id is null, a new session is created automatically.
    """
    if not body.message or not body.message.strip():
        raise AppException(
            code="INVALID_INPUT",
            message="Message cannot be empty",
            status_code=400,
        )

    return StreamingResponse(
        conversation_stream(body, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )


# --- GET /conversation/{session_id} ---


@agent_router.get(
    "/conversation/{session_id}",
    response_model=ConversationHistoryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve conversation history for a session."""
    # Verify session belongs to current user
    result = await db.execute(
        select(AgentConversationSession).where(
            AgentConversationSession.id == UUID(session_id),
            AgentConversationSession.recruiter_id == UUID(str(current_user.id)),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise AppException(
            code="NOT_FOUND",
            message="Conversation session not found",
            status_code=404,
        )

    messages = await agent_service.get_session_messages(db, session_id)
    return ConversationHistoryResponse(
        session_id=session_id,
        title=session.title,
        messages=[agent_service._message_to_response(m) for m in messages],
    )


# --- GET /preferences ---


@agent_router.get(
    "/preferences",
    response_model=PreferenceResponse,
)
async def get_preferences(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Read recruiter preferences (explicit + implicit scores)."""
    recruiter_id = str(current_user.id)
    prefs = await agent_service.get_preferences(db, recruiter_id)
    implicit_scores = await agent_service.get_implicit_scores(db, recruiter_id)

    return PreferenceResponse(
        explicit=prefs.explicit_preferences,
        implicit_scores=implicit_scores,
        last_updated=prefs.last_updated.isoformat(),
    )


# --- PUT /preferences ---


@agent_router.put(
    "/preferences",
    response_model=PreferenceResponse,
    responses={400: {"model": ErrorResponse}},
)
async def update_preferences(
    body: PreferenceUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update explicit preferences for the current recruiter."""
    recruiter_id = str(current_user.id)
    prefs = await agent_service.update_preferences(db, recruiter_id, body.explicit)

    # Log the preference update action
    await agent_service.log_action(
        db=db,
        recruiter_id=recruiter_id,
        session_id=None,
        action_type="preference_update",
        agent_name="preference_engine",
        input_data=f"explicit: {len(body.explicit)} fields",
        output_data=json.dumps({"updated": list(body.explicit.keys())}),
    )

    implicit_scores = await agent_service.get_implicit_scores(db, recruiter_id)
    return PreferenceResponse(
        explicit=prefs.explicit_preferences,
        implicit_scores=implicit_scores,
        last_updated=prefs.last_updated.isoformat(),
    )


# --- GET /proactive/alerts ---


@agent_router.get(
    "/proactive/alerts",
    response_model=ProactiveAlertsResponse,
)
async def get_proactive_alerts(
    unread_only: bool = Query(False, description="Only return unread alerts"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get proactive alerts for the current recruiter."""
    recruiter_id = str(current_user.id)
    query = select(AgentProactiveAlert).where(
        AgentProactiveAlert.recruiter_id == UUID(recruiter_id),
    )
    if unread_only:
        query = query.where(AgentProactiveAlert.is_read == False)  # noqa: E712

    query = query.order_by(AgentProactiveAlert.created_at.desc()).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return ProactiveAlertsResponse(
        alerts=[
            ProactiveAlertResponse(
                id=str(a.id),
                alert_type=a.alert_type,
                title=a.title,
                body=a.body,
                data=a.data,
                is_read=a.is_read,
                created_at=a.created_at.isoformat(),
            )
            for a in alerts
        ],
    )


# --- GET /action-log ---


@agent_router.get(
    "/action-log",
    response_model=dict,
)
async def get_action_log(
    start_date: str | None = Query(None, description="ISO 8601 start date filter"),
    end_date: str | None = Query(None, description="ISO 8601 end date filter"),
    action_type: str | None = Query(None, description="Filter by action type"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """EU AI Act compliant audit trail.

    All agent actions are logged with pseudonymized input/output.
    PII fields (names, emails, phones) are replaced with SHA-256 hashes.
    """
    recruiter_id = str(current_user.id)

    # Get total count
    count_query = agent_service._action_log_count_query(
        recruiter_id, start_date, end_date, action_type,
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = agent_service._action_log_query(
        recruiter_id, start_date, end_date, action_type,
        pagination.limit, 0,
    )
    result = await db.execute(query)
    actions = result.scalars().all()

    data = [
        ActionLogEntry(
            id=str(a.id),
            action_type=a.action_type,
            agent_name=a.agent_name,
            input_pseudonymized=a.input_pseudonymized,
            output_pseudonymized=a.output_pseudonymized,
            created_at=a.created_at.isoformat(),
        )
        for a in actions
    ]

    return paginated_response(data, total, pagination.limit, pagination.sort)
