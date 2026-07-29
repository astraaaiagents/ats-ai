"""Agent Gateway service layer.

Handles session management, preference CRUD, action logging,
and orchestrator invocation for the agent-first recruiter portal.
"""

import hashlib
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_action import AgentAction
from app.models.agent_alert import AgentProactiveAlert
from app.models.agent_conversation import AgentConversationMessage, AgentConversationSession
from app.models.preference_learning_event import PreferenceLearningEvent
from app.models.recruiter_preference import RecruiterPreference
from app.schemas.agent import (
    ActionLogEntry,
    ActionLogResponse,
    AgentActionResponse,
    AgentMessageResponse,
    ConversationHistoryResponse,
    PreferenceResponse,
    ProactiveAlertResponse,
    ProactiveAlertsResponse,
    SourceRefResponse,
)


# --- Pseudonymization ---

# PII fields that are hashed before storage in agent_actions.
# SHA-256 is used for one-way pseudonymization: the original value
# cannot be recovered from the hash, but the same value always
# produces the same hash (enabling deduplication in audit logs).
PII_FIELDS = {"first_name", "last_name", "email", "phone", "current_employer"}


def pseudonymize(text: str) -> str:
    """Replace PII values with SHA-256 hashes.

    Expects text to be a JSON object with known PII field names.
    Fields in PII_FIELDS are replaced with their SHA-256 hash.
    Non-PII fields are left unchanged.
    """
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # Not JSON — return as-is (shouldn't happen for structured data)
        return text

    if isinstance(data, dict):
        for key in PII_FIELDS:
            if key in data and isinstance(data[key], str) and data[key]:
                data[key] = hashlib.sha256(data[key].encode()).hexdigest()[:16]
    elif isinstance(data, list):
        cleaned = []
        for item in data:
            if isinstance(item, dict):
                for key in PII_FIELDS:
                    if key in item and isinstance(item[key], str) and item[key]:
                        item[key] = hashlib.sha256(item[key].encode()).hexdigest()[:16]
            cleaned.append(item)
        data = cleaned

    return json.dumps(data, ensure_ascii=False)


# --- Session Management ---


async def get_or_create_session(
    db: AsyncSession,
    recruiter_id: str,
    session_id: str | None,
    title: str | None = None,
) -> AgentConversationSession:
    """Get existing session or create a new one."""
    if session_id:
        result = await db.execute(
            select(AgentConversationSession).where(
                AgentConversationSession.id == uuid.UUID(session_id),
                AgentConversationSession.recruiter_id == uuid.UUID(recruiter_id),
            )
        )
        session = result.scalar_one_or_none()
        if session:
            return session

    # Create new session
    session = AgentConversationSession(
        recruiter_id=uuid.UUID(recruiter_id),
        title=title or "New conversation",
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_messages(
    db: AsyncSession,
    session_id: str,
) -> list[AgentConversationMessage]:
    """Get all messages for a session, ordered by creation time."""
    result = await db.execute(
        select(AgentConversationMessage)
        .where(AgentConversationMessage.session_id == uuid.UUID(session_id))
        .order_by(AgentConversationMessage.created_at.asc())
    )
    return list(result.scalars().all())


# --- Preference CRUD ---


async def get_preferences(
    db: AsyncSession,
    recruiter_id: str,
) -> RecruiterPreference:
    """Get or create a preference profile for a recruiter."""
    result = await db.execute(
        select(RecruiterPreference).where(
            RecruiterPreference.recruiter_id == uuid.UUID(recruiter_id),
        )
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = RecruiterPreference(recruiter_id=uuid.UUID(recruiter_id))
        db.add(prefs)
        await db.flush()
    return prefs


async def update_preferences(
    db: AsyncSession,
    recruiter_id: str,
    explicit: dict,
) -> RecruiterPreference:
    """Update explicit preferences for a recruiter."""
    prefs = await get_preferences(db, recruiter_id)
    prefs.explicit_preferences = {**prefs.explicit_preferences, **explicit}
    prefs.last_updated = datetime.now(timezone.utc)
    await db.flush()
    return prefs


async def get_implicit_scores(
    db: AsyncSession,
    recruiter_id: str,
) -> dict[str, float]:
    """Extract implicit preference scores from the preference vector.

    The implicit_preference_vector is a 1536-dim pgvector embedding.
    This method returns a simplified view: the top-weighted dimensions
    mapped to human-readable preference names.

    In production, this would decode the vector using a mapping learned
    during training. For now, returns an empty dict — the vector is
    stored raw and decoded by the Preference Engine service.
    """
    # TODO: Implement vector decoding in Preference Engine
    # For now, return empty dict; scores are computed at ranking time
    return {}


# --- Action Logging ---


async def log_action(
    db: AsyncSession,
    recruiter_id: str,
    session_id: str | None,
    action_type: str,
    agent_name: str,
    input_data: str,
    output_data: str,
) -> AgentAction:
    """Log an agent action to the EU AI Act audit trail."""
    action = AgentAction(
        recruiter_id=uuid.UUID(recruiter_id),
        session_id=uuid.UUID(session_id) if session_id else None,
        action_type=action_type,
        agent_name=agent_name,
        input_pseudonymized=pseudonymize(input_data),
        output_pseudonymized=pseudonymize(output_data),
    )
    db.add(action)
    await db.flush()
    return action


# --- Message Conversion ---


def _message_to_response(msg: AgentConversationMessage) -> AgentMessageResponse:
    """Convert a message model to an API response."""
    actions = []
    if msg.actions:
        for a in msg.actions:
            actions.append(AgentActionResponse(
                id=str(a.get("id", "")),
                label=a.get("label", ""),
                type=a.get("type", ""),
                payload=a.get("payload", {}),
                confirmation=a.get("confirmation"),
            ))

    sources = []
    if msg.sources:
        for s in msg.sources:
            sources.append(SourceRefResponse(
                type=s.get("type", ""),
                identifier=s.get("identifier", ""),
                timestamp=s.get("timestamp", ""),
            ))

    return AgentMessageResponse(
        id=str(msg.id),
        role=msg.role,
        content=msg.content,
        cards=msg.cards or [],
        actions=actions,
        sources=sources,
        confidence=float(msg.confidence) if msg.confidence else None,
        is_proactive=msg.is_proactive,
        created_at=msg.created_at.isoformat(),
    )


# --- Query Builders ---

def _action_log_query(
    recruiter_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    action_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Build the action log query with optional filters."""
    from app.models.agent_action import AgentAction

    query = select(AgentAction).where(
        AgentAction.recruiter_id == uuid.UUID(recruiter_id),
    )

    if start_date:
        query = query.where(AgentAction.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(AgentAction.created_at <= datetime.fromisoformat(end_date))
    if action_type:
        query = query.where(AgentAction.action_type == action_type)

    query = query.order_by(AgentAction.created_at.desc()).limit(limit).offset(offset)
    return query


def _action_log_count_query(
    recruiter_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    action_type: str | None = None,
):
    """Build the action log count query."""
    from app.models.agent_action import AgentAction
    from sqlalchemy import func

    query = select(func.count(AgentAction.id)).where(
        AgentAction.recruiter_id == uuid.UUID(recruiter_id),
    )

    if start_date:
        query = query.where(AgentAction.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(AgentAction.created_at <= datetime.fromisoformat(end_date))
    if action_type:
        query = query.where(AgentAction.action_type == action_type)

    return query
