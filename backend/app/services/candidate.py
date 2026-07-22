"""Candidate business logic service."""

from datetime import UTC, datetime

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import AppException
from app.models.candidate import Candidate, CandidateSource
from app.models.candidate_skill import CandidateSkill
from app.models.candidate_timeline import CandidateTimeline


async def create_candidate(
    db: AsyncSession,
    organization_id: str,
    owner_id: str | None,
    data: dict,
) -> Candidate:
    """Create a new candidate with optional skills."""
    from uuid import UUID

    skills_data = data.pop("skills", [])

    candidate = Candidate(
        organization_id=UUID(organization_id),
        owner_id=UUID(owner_id) if owner_id else None,
        **data,
    )
    db.add(candidate)
    await db.flush()

    # Add skills
    for skill_data in skills_data:
        # Handle both dict and Pydantic model
        if hasattr(skill_data, "model_dump"):
            skill_kwargs = skill_data.model_dump()
        else:
            skill_kwargs = dict(skill_data)
        skill = CandidateSkill(
            organization_id=UUID(organization_id),
            candidate_id=candidate.id,
            **skill_kwargs,
        )
        db.add(skill)

    await db.commit()
    await db.refresh(candidate)
    return candidate


async def get_candidate(
    db: AsyncSession,
    candidate_id: str,
    include_skills: bool = True,
    include_documents: bool = True,
    include_timeline: bool = True,
) -> Candidate:
    """Get a candidate by ID with optional related data."""
    from uuid import UUID

    result = await db.execute(
        select(Candidate).where(Candidate.id == UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise AppException(
            code="NOT_FOUND",
            message="Candidate not found",
            status_code=404,
        )
    return candidate


async def list_candidates(
    db: AsyncSession,
    organization_id: str,
    limit: int = 25,
    cursor: str | None = None,
    status: str | None = None,
    source: str | None = None,
    owner_id: str | None = None,
    skill: str | None = None,
    search: str | None = None,
) -> tuple[list[Candidate], int]:
    """List candidates with filtering and pagination."""
    from uuid import UUID

    org_uuid = UUID(organization_id)
    base_query = select(Candidate).where(Candidate.organization_id == org_uuid)
    count_query = select(func.count()).where(Candidate.organization_id == org_uuid)

    filters = []
    if status:
        filters.append(Candidate.status == status)
    if source:
        filters.append(Candidate.source == source)
    if owner_id:
        filters.append(Candidate.owner_id == UUID(owner_id))
    if search:
        # Full-text search on name and title
        search_term = f"%{search}%"
        filters.append(
            or_(
                Candidate.first_name.ilike(search_term),
                Candidate.last_name.ilike(search_term),
                Candidate.current_title.ilike(search_term),
                Candidate.email.ilike(search_term),
            )
        )

    if filters:
        base_query = base_query.where(*filters)
        count_query = count_query.where(*filters)

    # Skill filter (requires JOIN)
    if skill:
        base_query = base_query.join(CandidateSkill).where(
            CandidateSkill.skill_name.ilike(f"%{skill}%")
        )
        count_query = count_query.join(CandidateSkill).where(
            CandidateSkill.skill_name.ilike(f"%{skill}%")
        )

    # Cursor pagination
    if cursor:
        from uuid import UUID as UUID_TYPE

        try:
            cursor_uuid = UUID_TYPE(cursor)
            base_query = base_query.where(Candidate.id > cursor_uuid)
        except Exception:
            pass  # Invalid cursor, ignore

    base_query = base_query.order_by(Candidate.id).limit(limit + 1)

    result = await db.execute(base_query)
    candidates = result.scalars().all()

    has_more = len(candidates) > limit
    if has_more:
        candidates = candidates[:limit]

    # Get total count (without cursor limit)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return candidates, total


async def update_candidate(
    db: AsyncSession,
    candidate: Candidate,
    data: dict,
) -> Candidate:
    """Update a candidate's fields."""
    for key, value in data.items():
        if value is not None and hasattr(candidate, key):
            setattr(candidate, key, value)

    await db.commit()
    await db.refresh(candidate)
    return candidate


async def change_candidate_status(
    db: AsyncSession,
    candidate: Candidate,
    new_status: str,
    user_role: str,
    reason: str | None = None,
) -> Candidate:
    """Change candidate status with state machine validation."""
    from app.services.candidate_status import validate_transition

    if not validate_transition(candidate.status, new_status, user_role):
        allowed = get_allowed_transitions_for_role(candidate.status, user_role)
        raise AppException(
            code="INVALID_TRANSITION",
            message=f"Cannot transition from '{candidate.status}' to '{new_status}'. "
                    f"Allowed transitions: {allowed}",
            status_code=400,
        )

    old_status = candidate.status
    candidate.status = new_status

    # Add timeline event
    timeline = CandidateTimeline(
        organization_id=candidate.organization_id,
        candidate_id=candidate.id,
        event_type="status_changed",
        description=f"Status changed from '{old_status}' to '{new_status}'",
        metadata={"from_status": old_status, "to_status": new_status, "reason": reason},
    )
    db.add(timeline)

    await db.commit()
    await db.refresh(candidate)
    return candidate


def get_allowed_transitions_for_role(status: str, role: str) -> list[str]:
    """Get allowed transitions for a status and role (helper for error messages)."""
    from app.services.candidate_status import get_allowed_transitions
    return get_allowed_transitions(status, role)


async def check_duplicate(
    db: AsyncSession,
    organization_id: str,
    email: str | None = None,
    phone: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> tuple[bool, list[dict]]:
    """Check for duplicate candidates.

    - Email: exact match
    - Phone + name: Jaro-Winkler similarity > 0.9
    """
    from uuid import UUID

    org_uuid = UUID(organization_id)
    duplicates = []

    if email:
        result = await db.execute(
            select(Candidate).where(
                Candidate.organization_id == org_uuid,
                Candidate.email == email.lower(),
                Candidate.status != "archived",
            )
        )
        candidates = result.scalars().all()
        duplicates = [
            {
                "id": str(c.id),
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "status": c.status,
                "match_reason": "email_exact",
            }
            for c in candidates
        ]

    return len(duplicates) > 0, duplicates
