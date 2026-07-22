"""Candidate management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_session
from app.middleware.error_handler import AppException
from app.middleware.pagination import PaginationParams, paginated_response
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.candidate_timeline import CandidateTimeline
from app.models.user import User
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDocumentResponse,
    CandidateResponse,
    CandidateSkillInput,
    CandidateSkillResponse,
    CandidateStatusUpdate,
    CandidateTimelineEvent,
    CandidateUpdate,
    DedupCheckRequest,
    DedupCheckResponse,
)
from app.services.candidate import (
    change_candidate_status,
    check_duplicate,
    create_candidate,
    get_candidate,
    list_candidates,
    update_candidate,
)

candidates_router = APIRouter(prefix="/candidates", tags=["candidates"])


def _candidate_to_response(candidate: Candidate) -> CandidateResponse:
    """Convert Candidate model to response schema."""
    skills = [
        CandidateSkillResponse(
            id=str(s.id),
            skill_name=s.skill_name,
            proficiency=s.proficiency,
            years_experience=s.years_experience,
        )
        for s in candidate.skills
    ]
    documents = [
        CandidateDocumentResponse(
            id=str(d.id),
            document_type=d.document_type,
            file_name=d.file_name,
            file_size_bytes=d.file_size_bytes,
            s3_key=d.s3_key,
            created_at=d.created_at.isoformat(),
        )
        for d in candidate.documents
    ]
    timeline = [
        CandidateTimelineEvent(
            id=str(t.id),
            event_type=t.event_type,
            description=t.description,
            metadata=t.details,
            created_at=t.created_at.isoformat(),
        )
        for t in candidate.timeline
    ]

    return CandidateResponse(
        id=str(candidate.id),
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        current_title=candidate.current_title,
        current_employer=candidate.current_employer,
        location=candidate.location,
        salary_expectation_min=candidate.salary_expectation_min,
        salary_expectation_max=candidate.salary_expectation_max,
        visa_status=candidate.visa_status,
        notice_period_days=candidate.notice_period_days,
        source=candidate.source,
        status=candidate.status,
        owner_id=str(candidate.owner_id) if candidate.owner_id else None,
        ai_summary=candidate.ai_summary,
        ai_summary_generated_at=candidate.ai_summary_generated_at.isoformat() if candidate.ai_summary_generated_at else None,
        is_ai_summary_edited=candidate.is_ai_summary_edited,
        skills=skills,
        documents=documents,
        timeline=timeline,
        created_at=candidate.created_at.isoformat(),
        updated_at=candidate.updated_at.isoformat(),
    )


@candidates_router.post("", response_model=CandidateResponse, status_code=201)
async def create_candidate_endpoint(
    body: CandidateCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new candidate."""
    org_id = str(current_user.organization_id)
    owner_id = str(current_user.id)

    # Check for duplicate email
    is_dup, dups = await check_duplicate(
        db, org_id, email=body.email.lower()
    )
    if is_dup:
        raise AppException(
            code="DUPLICATE_CANDIDATE",
            message=f"Duplicate candidate found: {dups[0]['first_name']} {dups[0]['last_name']}",
            status_code=409,
        )

    candidate = await create_candidate(db, org_id, owner_id, body.model_dump())
    return _candidate_to_response(candidate)


@candidates_router.get("", response_model=dict)
async def list_candidates_endpoint(
    pagination: PaginationParams = Depends(),
    status: str | None = Query(None),
    source: str | None = Query(None),
    owner_id: str | None = Query(None),
    skill: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List candidates with filters and pagination."""
    org_id = str(current_user.organization_id)

    candidates, total = await list_candidates(
        db, org_id, pagination.limit, pagination.cursor,
        status, source, owner_id, skill, search,
    )

    data = [_candidate_to_response(c) for c in candidates]
    return paginated_response(data, total, pagination.limit, pagination.sort)


@candidates_router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate_endpoint(
    candidate_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get candidate by ID with skills, documents, and timeline."""
    candidate = await get_candidate(db, candidate_id)
    return _candidate_to_response(candidate)


@candidates_router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate_endpoint(
    candidate_id: str,
    body: CandidateUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update candidate fields."""
    candidate = await get_candidate(db, candidate_id)
    update_data = body.model_dump(exclude_unset=True)
    candidate = await update_candidate(db, candidate, update_data)
    return _candidate_to_response(candidate)


@candidates_router.patch("/{candidate_id}/status", response_model=CandidateResponse)
async def update_candidate_status_endpoint(
    candidate_id: str,
    body: CandidateStatusUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Change candidate status with state machine validation."""
    candidate = await get_candidate(db, candidate_id)
    candidate = await change_candidate_status(
        db, candidate, body.status, current_user.role, body.reason
    )
    return _candidate_to_response(candidate)


@candidates_router.post("/dedup-check", response_model=DedupCheckResponse)
async def check_duplicate_endpoint(
    body: DedupCheckRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Check for duplicate candidates."""
    org_id = str(current_user.organization_id)
    is_dup, dups = await check_duplicate(
        db, org_id,
        email=body.email,
        phone=body.phone,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    return DedupCheckResponse(is_duplicate=is_dup, candidates=dups)


@candidates_router.get("/{candidate_id}/timeline", response_model=dict)
async def get_candidate_timeline(
    candidate_id: str,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get candidate timeline events with pagination."""
    await get_candidate(db, candidate_id)  # Verify candidate exists

    org_id = str(current_user.organization_id)
    count_result = await db.execute(
        select(func.count()).where(
            CandidateTimeline.candidate_id == UUID(candidate_id),
            CandidateTimeline.organization_id == UUID(org_id),
        )
    )
    total = count_result.scalar() or 0

    query = (
        select(CandidateTimeline)
        .where(
            CandidateTimeline.candidate_id == UUID(candidate_id),
            CandidateTimeline.organization_id == UUID(org_id),
        )
        .order_by(CandidateTimeline.created_at.desc())
        .limit(pagination.limit + 1)
    )

    result = await db.execute(query)
    events = result.scalars().all()

    has_more = len(events) > pagination.limit
    if has_more:
        events = events[:pagination.limit]

    data = [
        CandidateTimelineEvent(
            id=str(e.id),
            event_type=e.event_type,
            description=e.description,
            metadata=e.metadata,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]

    return paginated_response(data, total, pagination.limit, pagination.sort)


@candidates_router.post("/{candidate_id}/skills", response_model=CandidateSkillResponse)
async def add_candidate_skill(
    candidate_id: str,
    body: CandidateSkillInput,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add a skill to a candidate."""
    candidate = await get_candidate(db, candidate_id)
    org_id = str(current_user.organization_id)

    # Check for duplicate skill
    existing = await db.execute(
        select(CandidateSkill).where(
            CandidateSkill.candidate_id == UUID(candidate_id),
            CandidateSkill.skill_name == body.skill_name,
        )
    )
    if existing.scalar_one_or_none():
        raise AppException(
            code="DUPLICATE_SKILL",
            message=f"Skill '{body.skill_name}' already exists for this candidate",
            status_code=409,
        )

    skill = CandidateSkill(
        organization_id=UUID(org_id),
        candidate_id=UUID(candidate_id),
        skill_name=body.skill_name,
        proficiency=body.proficiency,
        years_experience=body.years_experience,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    return CandidateSkillResponse(
        id=str(skill.id),
        skill_name=skill.skill_name,
        proficiency=skill.proficiency,
        years_experience=skill.years_experience,
    )


@candidates_router.delete("/{candidate_id}/skills/{skill_name}")
async def remove_candidate_skill(
    candidate_id: str,
    skill_name: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Remove a skill from a candidate."""
    await get_candidate(db, candidate_id)
    org_id = str(current_user.organization_id)

    result = await db.execute(
        select(CandidateSkill).where(
            CandidateSkill.candidate_id == UUID(candidate_id),
            CandidateSkill.skill_name == skill_name,
            CandidateSkill.organization_id == UUID(org_id),
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise AppException(
            code="NOT_FOUND",
            message="Skill not found",
            status_code=404,
        )

    await db.delete(skill)
    await db.commit()

    return {"message": "Skill removed"}


@candidates_router.delete("/{candidate_id}", response_model=CandidateResponse)
async def archive_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Archive a candidate (soft-delete)."""
    candidate = await get_candidate(db, candidate_id)
    candidate.status = "archived"
    await db.commit()
    await db.refresh(candidate)
    return _candidate_to_response(candidate)
