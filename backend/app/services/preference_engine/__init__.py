"""Preference Engine — stores, updates, and applies recruiter preferences.

Handles two tiers of preferences:
1. Explicit: Hard rules set by recruiter (JSONB in DB)
2. Implicit: Learned patterns from recruiter actions (pgvector embedding)

Learning loop:
1. Recruiter reviews N candidates → approves/rejects
2. Preference Engine logs the action to preference_learning_events
3. Implicit preference vector is updated based on the action
4. Next ranking pass uses updated preferences

Supported learning triggers:
- approval: Recruiter approved a candidate
- rejection: Recruiter rejected a candidate (with optional reason)
- explicit_statement: Recruiter stated a preference in natural language
- outreach_edit: Recruiter edited an outreach draft (style learning)
- outreach_response: Candidate responded to outreach (engagement learning)
"""

import json
import logging
from datetime import datetime, timezone, timedelta
import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference_learning_event import PreferenceLearningEvent
from app.models.recruiter_preference import RecruiterPreference

logger = logging.getLogger(__name__)

# Learning rate for implicit preference updates
# Lower = slower learning (more stable), higher = faster learning (more reactive)
LEARNING_RATE = 0.1

# Minimum confidence threshold for implicit preference updates
# Only update if the action is confident enough
MIN_CONFIDENCE = 0.6

# Feature extraction mapping — maps candidate/job fields to preference dimensions
# These correspond to dimensions in the 1536-dim implicit preference vector
FEATURE_DIMENSIONS = {
    "cloud_experience": ["aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform"],
    "leadership_experience": ["lead", "senior", "manager", "principal", "architect", "team"],
    "startup_experience": ["startup", "early-stage", "series a", "series b"],
    "finance_experience": ["fintech", "banking", "finance", "trading", "hedge fund"],
    "healthcare_experience": ["healthcare", "health tech", "biotech", "medical"],
    "remote_experience": ["remote", "distributed", "work from home"],
    "contract_experience": ["contract", "freelance", "consultant", "1099"],
    "python_experience": ["python", "django", "flask", "fastapi", "celery"],
    "java_experience": ["java", "spring", "spring boot", "jakarta"],
    "javascript_experience": ["javascript", "typescript", "react", "vue", "angular", "node"],
    "data_experience": ["data science", "ml", "machine learning", "ai", "tensorflow", "pytorch"],
    "devops_experience": ["devops", "ci/cd", "jenkins", "github actions", "ansible"],
}


# --- Explicit Preference CRUD ---


async def get_explicit_preferences(
    db: AsyncSession,
    recruiter_id: str,
) -> dict[str, Any]:
    """Get explicit preferences for a recruiter.

    Creates a default preference profile if none exists.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.

    Returns:
        Dict of explicit preferences.
    """
    prefs = await _get_or_create_preference(db, recruiter_id)
    return dict(prefs.explicit_preferences)


async def set_explicit_preference(
    db: AsyncSession,
    recruiter_id: str,
    key: str,
    value: Any,
) -> dict[str, Any]:
    """Set a single explicit preference.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        key: Preference key (e.g., "required_visa_status").
        value: Preference value.

    Returns:
        Updated explicit preferences dict.
    """
    prefs = await _get_or_create_preference(db, recruiter_id)
    prefs.explicit_preferences[key] = value
    prefs.last_updated = datetime.now(timezone.utc)
    await db.flush()

    # Log the preference update
    await _log_learning_event(
        db,
        recruiter_id=recruiter_id,
        event_type="explicit_statement",
        preference_delta={"key": key, "value": value},
    )

    return dict(prefs.explicit_preferences)


async def update_explicit_preferences(
    db: AsyncSession,
    recruiter_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Update multiple explicit preferences at once.

    Merges updates with existing preferences (doesn't replace).

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        updates: Dict of preference key-value pairs to update.

    Returns:
        Updated explicit preferences dict.
    """
    prefs = await _get_or_create_preference(db, recruiter_id)
    prefs.explicit_preferences = {**prefs.explicit_preferences, **updates}
    prefs.last_updated = datetime.now(timezone.utc)
    await db.flush()

    # Log each update
    for key, value in updates.items():
        await _log_learning_event(
            db,
            recruiter_id=recruiter_id,
            event_type="explicit_statement",
            preference_delta={"key": key, "value": value},
        )

    return dict(prefs.explicit_preferences)


async def delete_explicit_preference(
    db: AsyncSession,
    recruiter_id: str,
    key: str,
) -> dict[str, Any]:
    """Delete a single explicit preference.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        key: Preference key to delete.

    Returns:
        Updated explicit preferences dict.
    """
    prefs = await _get_or_create_preference(db, recruiter_id)
    prefs.explicit_preferences.pop(key, None)
    prefs.last_updated = datetime.now(timezone.utc)
    await db.flush()

    return dict(prefs.explicit_preferences)


# --- Implicit Preference Learning ---


async def record_approval(
    db: AsyncSession,
    recruiter_id: str,
    candidate_id: str,
    job_id: str | None = None,
    features: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a candidate approval and update implicit preferences.

    When a recruiter approves a candidate, the engine extracts features
    from the candidate profile and boosts the corresponding implicit
    preference dimensions.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        candidate_id: Approved candidate ID.
        job_id: Optional job ID context.
        features: Optional pre-extracted features. If None, features are
                  extracted from the candidate_id (looked up by ID).

    Returns:
        Updated implicit scores dict.
    """
    # Extract features from candidate
    if features is None:
        features = _extract_features_from_candidate(candidate_id)

    # Get current implicit preferences
    prefs = await _get_or_create_preference(db, recruiter_id)
    implicit = _decode_vector(prefs.implicit_preference_vector) if prefs.implicit_preference_vector else {}

    # Update implicit preferences based on approved features
    for feature, value in features.items():
        current = implicit.get(feature, 0.5)
        implicit[feature] = min(1.0, current + LEARNING_RATE * value)

    # Update the preference record
    prefs.implicit_preference_vector = _encode_vector(implicit)
    prefs.last_updated = datetime.now(timezone.utc)
    await db.flush()

    # Log the learning event
    await _log_learning_event(
        db,
        recruiter_id=recruiter_id,
        event_type="approval",
        candidate_id=candidate_id,
        job_id=job_id,
        features_before={},
        features_after=features,
        preference_delta={k: v for k, v in implicit.items() if v > 0.5},
    )

    return implicit


async def record_rejection(
    db: AsyncSession,
    recruiter_id: str,
    candidate_id: str,
    job_id: str | None = None,
    reason: str | None = None,
    features: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a candidate rejection and update implicit preferences.

    When a recruiter rejects a candidate, the engine extracts features
    and reduces the corresponding implicit preference dimensions.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        candidate_id: Rejected candidate ID.
        job_id: Optional job ID context.
        reason: Optional rejection reason (e.g., "not enough leadership experience").
        features: Optional pre-extracted features.

    Returns:
        Updated implicit scores dict.
    """
    if features is None:
        features = _extract_features_from_candidate(candidate_id)

    prefs = await _get_or_create_preference(db, recruiter_id)
    implicit = _decode_vector(prefs.implicit_preference_vector) if prefs.implicit_preference_vector else {}

    # Rejection reduces preference weights
    for feature, value in features.items():
        current = implicit.get(feature, 0.5)
        implicit[feature] = max(0.0, current - LEARNING_RATE * value)

    prefs.implicit_preference_vector = _encode_vector(implicit)
    prefs.last_updated = datetime.now(timezone.utc)
    await db.flush()

    await _log_learning_event(
        db,
        recruiter_id=recruiter_id,
        event_type="rejection",
        candidate_id=candidate_id,
        job_id=job_id,
        features_before={},
        features_after=features,
        preference_delta={k: v for k, v in implicit.items() if v < 0.5},
    )

    return implicit


async def get_implicit_scores(
    db: AsyncSession,
    recruiter_id: str,
) -> dict[str, float]:
    """Get decoded implicit preference scores.

    Decodes the pgvector embedding into human-readable preference
    dimension scores.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.

    Returns:
        Dict mapping preference dimension names to scores (0.0 - 1.0).
    """
    prefs = await _get_or_create_preference(db, recruiter_id)
    return _decode_vector(prefs.implicit_preference_vector) if prefs.implicit_preference_vector else {}


# --- Learning Events ---


async def get_learning_events(
    db: AsyncSession,
    recruiter_id: str,
    limit: int = 50,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """Get preference learning events for a recruiter.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        limit: Maximum number of events to return.
        event_type: Optional filter by event type.

    Returns:
        List of learning event dicts.
    """
    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    query = select(PreferenceLearningEvent).where(
        PreferenceLearningEvent.recruiter_id == rec_uuid,
    )
    if event_type:
        query = query.where(PreferenceLearningEvent.event_type == event_type)
    query = query.order_by(
        PreferenceLearningEvent.created_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "candidate_id": str(e.candidate_id) if e.candidate_id else None,
            "job_id": str(e.job_id) if e.job_id else None,
            "features_before": e.features_before,
            "features_after": e.features_after,
            "preference_delta": e.preference_delta,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


async def get_weekly_digest(
    db: AsyncSession,
    recruiter_id: str,
) -> dict[str, Any]:
    """Generate a weekly learning digest.

    Summarizes the past week's preference learning activity:
    - Number of approvals/rejections
    - Top preference changes
    - Summary of what the agent learned

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.

    Returns:
        Digest dict with summary, approvals, rejections, top_changes.
    """
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    result = await db.execute(
        select(PreferenceLearningEvent).where(
            PreferenceLearningEvent.recruiter_id == rec_uuid,
            PreferenceLearningEvent.created_at >= one_week_ago,
        )
    )
    events = result.scalars().all()

    approvals = sum(1 for e in events if e.event_type == "approval")
    rejections = sum(1 for e in events if e.event_type == "rejection")
    explicit_updates = sum(1 for e in events if e.event_type == "explicit_statement")

    # Collect all preference deltas
    all_deltas = {}
    for e in events:
        if e.preference_delta:
            for k, v in e.preference_delta.items():
                if isinstance(v, float):
                    all_deltas[k] = v

    # Top changes (sorted by absolute value)
    top_changes = sorted(
        all_deltas.items(),
        key=lambda x: abs(x[1] - 0.5),
        reverse=True,
    )[:5]

    return {
        "period": "past_7_days",
        "summary": f"This week you approved {approvals} candidates and rejected {rejections}. "
                   f"{'You updated ' + str(explicit_updates) + ' explicit preferences. ' if explicit_updates else ''}"
                   f"Your preferences have been updated based on your review patterns.",
        "approvals": approvals,
        "rejections": rejections,
        "explicit_updates": explicit_updates,
        "top_changes": [
            {"dimension": k, "score": round(v, 2)}
            for k, v in top_changes
        ],
    }


# --- GDPR Compliance ---


async def delete_recruiter_preferences(
    db: AsyncSession,
    recruiter_id: str,
) -> None:
    """Delete all preference data for a recruiter (GDPR right to erasure).

    Deletes:
    - Preference profile (explicit + implicit)
    - All learning events
    - Note: Conversation history and action logs are separate tables
      and must be deleted via separate endpoints

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
    """
    prefs = await _get_or_create_preference(db, recruiter_id)
    await db.delete(prefs)

    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    events_result = await db.execute(
        select(PreferenceLearningEvent).where(
            PreferenceLearningEvent.recruiter_id == rec_uuid,
        )
    )
    for event in events_result.scalars().all():
        await db.delete(event)

    await db.flush()
    logger.info(f"Deleted preferences for recruiter {recruiter_id}")


# --- Internal Helpers ---


async def _get_or_create_preference(
    db: AsyncSession,
    recruiter_id: str,
) -> RecruiterPreference:
    """Get or create a preference profile."""
    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    result = await db.execute(
        select(RecruiterPreference).where(
            RecruiterPreference.recruiter_id == rec_uuid,
        )
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = RecruiterPreference(recruiter_id=rec_uuid)
        db.add(prefs)
        await db.flush()
    return prefs


async def _log_learning_event(
    db: AsyncSession,
    recruiter_id: str,
    event_type: str,
    candidate_id: str | None = None,
    job_id: str | None = None,
    features_before: dict | None = None,
    features_after: dict | None = None,
    preference_delta: dict | None = None,
) -> None:
    """Log a preference learning event."""
    event = PreferenceLearningEvent(
        recruiter_id=recruiter_id,
        event_type=event_type,
        candidate_id=candidate_id,
        job_id=job_id,
        features_before=features_before or {},
        features_after=features_after or {},
        preference_delta=preference_delta or {},
    )
    db.add(event)
    await db.flush()


def _extract_features_from_candidate(candidate_id: str) -> dict[str, float]:
    """Extract preference-relevant features from a candidate.

    Looks up the candidate's skills and profile fields, then maps them
    to FEATURE_DIMENSIONS using keyword matching.

    Args:
        candidate_id: Candidate ID to look up.

    Returns:
        Dict mapping feature names to values (0.0 - 1.0).
    """
    # MVP: Return neutral features when we can't look up the candidate
    # In production, this would query the DB for the candidate's skills
    # and profile fields, then match against FEATURE_DIMENSIONS keywords.
    return {
        "cloud_experience": 0.5,
        "leadership_experience": 0.5,
        "python_experience": 0.5,
        "java_experience": 0.5,
        "javascript_experience": 0.5,
    }


def _decode_vector(vector_data: Any) -> dict[str, float]:
    """Decode a pgvector embedding into human-readable preference scores.

    Handles multiple storage formats:
    - List of floats (raw pgvector)
    - JSON string (legacy format)
    - dict (in-memory format)

    Args:
        vector_data: The implicit_preference_vector from DB.

    Returns:
        Dict mapping dimension names to scores (0.0 - 1.0).
    """
    if vector_data is None:
        return {}

    # Already a dict (in-memory or parsed)
    if isinstance(vector_data, dict):
        return {k: float(v) for k, v in vector_data.items()}

    # List of floats — map to FEATURE_DIMENSIONS
    if isinstance(vector_data, (list, tuple)):
        return _map_vector_to_features(list(vector_data))

    # JSON string (legacy format)
    if isinstance(vector_data, str):
        try:
            parsed = json.loads(vector_data)
            if isinstance(parsed, dict):
                return {k: float(v) for k, v in parsed.items()}
            if isinstance(parsed, (list, tuple)):
                return _map_vector_to_features(list(parsed))
        except (json.JSONDecodeError, TypeError):
            pass

    logger.warning(f"Unknown vector format: {type(vector_data).__name__}")
    return {}


def _map_vector_to_features(vector: list[float]) -> dict[str, float]:
    """Map a raw pgvector list to FEATURE_DIMENSIONS names.

    Uses the first N dimensions corresponding to FEATURE_DIMENSIONS keys.
    In production, this would use a trained projection matrix.

    Args:
        vector: Raw pgvector list of floats.

    Returns:
        Dict mapping feature names to scores.
    """
    result = {}
    feature_keys = list(FEATURE_DIMENSIONS.keys())
    for i, key in enumerate(feature_keys):
        if i < len(vector):
            # Sigmoid to map [-inf, inf] → [0, 1]
            val = vector[i]
            result[key] = 1.0 / (1.0 + __import__("math").exp(-val))
    return result


def _encode_vector(scores: dict[str, float]) -> list[float]:
    """Encode preference scores into a pgvector-compatible list.

    Maps FEATURE_DIMENSIONS scores into a fixed-length vector.
    In production, this would use OpenAI embeddings for the full 1536 dims.

    Args:
        scores: Dict mapping dimension names to scores.

    Returns:
        List of floats suitable for pgvector storage.
    """
    vector: list[float] = []
    for key in FEATURE_DIMENSIONS:
        val = scores.get(key, 0.5)
        # Inverse sigmoid to map [0, 1] → [-inf, inf] for pgvector
        import math
        # Clamp to avoid overflow
        clamped = max(-20.0, min(20.0, (val - 0.5) * 4))
        vector.append(clamped)
    return vector
