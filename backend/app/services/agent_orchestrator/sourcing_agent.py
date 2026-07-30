"""SourcingAgent — searches the candidate database with hybrid search.

Combines structured SQL filters, full-text search (tsvector), and
vector similarity search (pgvector) using Reciprocal Rank Fusion (RRF).

Returns ranked candidate profiles with fit metadata for the Orchestrator.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate

logger = logging.getLogger(__name__)

# RRF constant — standard value used in information retrieval
RRF_CONSTANT = 60


async def search_candidates(
    db: AsyncSession,
    org_id: str,
    recruiter_id: str,
    query: str,
    job_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search the candidate database with hybrid search.

    Combines three signals:
    1. Structured keyword match (title, location, employer)
    2. Full-text search on candidate profile fields (tsvector)
    3. Vector similarity on skill embeddings (pgvector)

    Ranks using Reciprocal Rank Fusion (RRF) to combine signals
    without needing to normalize scores across different scales.

    Args:
        db: SQLAlchemy async session.
        org_id: Organization ID for tenant scoping.
        recruiter_id: Recruiter ID for preference loading (not used in MVP).
        query: User's search query (natural language).
        job_id: Optional job requisition ID for context.
        limit: Maximum number of results to return.

    Returns:
        List of candidate dicts with keys:
        - id, first_name, last_name, current_title, location,
          current_employer, visa_status, notice_period_days,
          skills (list), fit_score (float), strengths (list), gaps (list)
    """
    import uuid
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except ValueError:
            pass

    # Step 1: Extract keywords from query for structured filtering
    keywords = _extract_keywords(query)

    # Step 2: Run three parallel search queries
    # Query A: Structured keyword search
    candidates_a = await _structured_search(db, org_id, keywords, limit * 3)

    # Query B: Full-text search (tsvector)
    candidates_b = await _fts_search(db, org_id, query, limit * 3)

    # Query C: Vector similarity search (pgvector)
    candidates_c = await _vector_search(db, org_id, query, limit * 3)

    # Step 3: Combine using RRF
    combined = _rrf_fusion([candidates_a, candidates_b, candidates_c], rrf_constant=RRF_CONSTANT)

    # Step 4: Enrich with skills and compute fit metadata
    enriched = await _enrich_candidates(db, combined[:limit], job_id)

    return enriched


def _ensure_uuid(val: Any) -> Any:
    if isinstance(val, str):
        try:
            return uuid.UUID(val)
        except ValueError:
            return val
    return val


async def _structured_search(
    db: AsyncSession,
    org_id: Any,
    keywords: list[str],
    limit: int,
) -> list[tuple[Candidate, float]]:
    """Search candidates using structured keyword matching.

    Matches keywords against title, location, employer, and skills fields.
    Returns candidates ranked by keyword match score.
    """
    from sqlalchemy import or_
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

    org_id = _ensure_uuid(org_id)

    if not keywords:
        # No keywords — return all candidates (low score)
        result = await db.execute(
            select(Candidate)
            .where(Candidate.organization_id == org_id)
            .where(Candidate.status != "archived")
            .limit(limit)
        )
        return [(c, 0.1) for c in result.scalars().all()]

    or_conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        or_conditions.append(Candidate.current_title.ilike(pattern))
        or_conditions.append(Candidate.location.ilike(pattern))
        or_conditions.append(Candidate.current_employer.ilike(pattern))
        or_conditions.append(
            Candidate.id.in_(
                select(CandidateSkill.candidate_id).where(
                    CandidateSkill.organization_id == org_id,
                    CandidateSkill.skill_name.ilike(pattern),
                )
            )
        )

    result = await db.execute(
        select(Candidate)
        .where(
            Candidate.organization_id == org_id,
            Candidate.status != "archived",
            or_(*or_conditions),
        )
        .order_by(Candidate.created_at.desc())
        .limit(limit)
    )
    candidates = result.scalars().all()
    return [(c, 1.0 / (i + 1)) for i, c in enumerate(candidates)]


async def _fts_search(
    db: AsyncSession,
    org_id: Any,
    query: str,
    limit: int,
) -> list[tuple[Candidate, float]]:
    """Search candidates using full-text search (tsvector on Postgres, ilike on SQLite).

    Combines ranking with keyword matching across candidate
    profile fields (title, employer, location) and candidate skills.
    """
    import re
    from sqlalchemy import or_
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

    org_id = _ensure_uuid(org_id)

    keywords = _extract_keywords(query)
    if not keywords:
        return []

    sanitized = [re.sub(r'[^a-zA-Z0-9]', '', kw) for kw in keywords if re.sub(r'[^a-zA-Z0-9]', '', kw)]
    if not sanitized:
        return []

    is_postgres = False
    try:
        bind = db.get_bind()
        dialect = getattr(bind, "dialect", None)
        if dialect and getattr(dialect, "name", "") == "postgresql":
            is_postgres = True
    except Exception:
        is_postgres = False

    if is_postgres:
        ts_query_str = " | ".join(sanitized)
        result = await db.execute(
            select(Candidate)
            .where(
                Candidate.organization_id == org_id,
                Candidate.status != "archived",
                text("""
                    (
                        to_tsvector('english',
                            COALESCE(current_title, '') || ' ' ||
                            COALESCE(current_employer, '') || ' ' ||
                            COALESCE(location, '')
                        ) @@ to_tsquery('english', :ts_query)
                        OR EXISTS (
                            SELECT 1 FROM candidate_skills cs
                            WHERE cs.candidate_id = candidates.id
                              AND to_tsvector('english', cs.skill_name) @@ to_tsquery('english', :ts_query)
                        )
                    )
                """),
            )
            .limit(limit),
            {"ts_query": ts_query_str},
        )
        candidates = result.scalars().all()
        return [(c, 1.0 / (i + 1)) for i, c in enumerate(candidates)]

    # Fallback for SQLite / non-Postgres: ILIKE keyword search
    or_conditions = []
    for kw in sanitized:
        pattern = f"%{kw}%"
        or_conditions.append(Candidate.current_title.ilike(pattern))
        or_conditions.append(Candidate.location.ilike(pattern))
        or_conditions.append(Candidate.current_employer.ilike(pattern))
        or_conditions.append(
            Candidate.id.in_(
                select(CandidateSkill.candidate_id).where(
                    CandidateSkill.organization_id == org_id,
                    CandidateSkill.skill_name.ilike(pattern),
                )
            )
        )

    result = await db.execute(
        select(Candidate)
        .where(
            Candidate.organization_id == org_id,
            Candidate.status != "archived",
            or_(*or_conditions),
        )
        .limit(limit)
    )
    candidates = result.scalars().all()
    return [(c, 1.0 / (i + 1)) for i, c in enumerate(candidates)]


async def _vector_search(
    db: AsyncSession,
    org_id: Any,
    query: str,
    limit: int,
) -> list[tuple[Candidate, float]]:
    """Search candidates using pgvector skill embeddings.

    Uses cosine similarity on candidate skill embeddings to find
    candidates with semantically similar skills to the query.

    Falls back to ILIKE skill name matching if no embeddings exist.
    """
    from sqlalchemy import or_
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

    org_id = _ensure_uuid(org_id)

    keywords = _extract_keywords(query)
    if not keywords:
        return []

    try:
        # Try pgvector cosine similarity search using extracted keywords
        skill_conditions = [CandidateSkill.skill_name.ilike(f"%{kw}%") for kw in keywords]

        skills_result = await db.execute(
            select(CandidateSkill.skill_embedding)
            .where(
                CandidateSkill.organization_id == org_id,
                CandidateSkill.skill_embedding.isnot(None),
                or_(*skill_conditions),
            )
            .limit(10)
        )
        embeddings = [row[0] for row in skills_result.all() if row[0]]

        if embeddings:
            # Use the average embedding of matching skills as the query vector
            import numpy as np
            avg_embedding = np.mean(embeddings, axis=0).tolist()

            # Cosine similarity search using pgvector <=> operator
            # Lower distance = higher similarity
            result = await db.execute(
                select(CandidateSkill.candidate_id, func.greatest(
                    1.0 - CandidateSkill.skill_embedding.cosine_distance(avg_embedding),
                    0.0
                ).label("similarity"))
                .where(
                    CandidateSkill.organization_id == org_id,
                    CandidateSkill.skill_embedding.isnot(None),
                )
                .order_by(CandidateSkill.skill_embedding.cosine_distance(avg_embedding).asc())
                .limit(limit * 3)
            )
            rows = result.all()

            # Group by candidate (max similarity across all their skills)
            candidate_scores: dict[str, float] = {}
            for cid, sim in rows:
                cid_str = str(cid)
                candidate_scores[cid_str] = max(candidate_scores.get(cid_str, 0.0), float(sim))

            if candidate_scores:
                candidate_ids = [_ensure_uuid(cid) for cid in list(candidate_scores.keys())[:limit]]
                result = await db.execute(
                    select(Candidate).where(
                        Candidate.organization_id == org_id,
                        Candidate.id.in_(candidate_ids),
                        Candidate.status != "archived",
                    )
                )
                candidates = result.scalars().all()
                return [(c, candidate_scores.get(str(c.id), 0.1)) for c in candidates]

    except Exception as exc:
        logger.warning(f"pgvector search failed ({exc}), falling back to ILIKE")

    # Fallback: ILIKE skill name matching for all extracted keywords
    skill_conditions = [CandidateSkill.skill_name.ilike(f"%{kw}%") for kw in keywords]
    result = await db.execute(
        select(CandidateSkill)
        .where(
            CandidateSkill.organization_id == org_id,
            or_(*skill_conditions),
        )
        .limit(limit * 5)
    )
    skills = result.scalars().all()

    # Group by candidate and count matches
    candidate_scores: dict[str, float] = {}
    for skill in skills:
        cid = str(skill.candidate_id)
        candidate_scores[cid] = candidate_scores.get(cid, 0) + (1.0 / (list(candidate_scores.keys()).index(cid) + 1) if cid in candidate_scores else 1.0)

    if not candidate_scores:
        return []

    # Fetch full candidate records
    candidate_ids = [_ensure_uuid(cid) for cid in list(candidate_scores.keys())[:limit]]
    result = await db.execute(
        select(Candidate).where(
            Candidate.organization_id == org_id,
            Candidate.id.in_(candidate_ids),
            Candidate.status != "archived",
        )
    )
    candidates = result.scalars().all()

    return [(c, candidate_scores.get(str(c.id), 0.1)) for c in candidates]


def _rrf_fusion(
    lists: list[list],
    rrf_constant: int = RRF_CONSTANT,
) -> list[tuple[Any, float]]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion.

    For each item, compute: sum(1 / (rrf_constant + rank_in_list))
    across all lists. Items with higher combined scores rank higher.

    Args:
        lists: List of ranked lists (each is list[tuple[Item, float]]).
        rrf_constant: RRF constant (60 is standard).

    Returns:
        Combined ranked list sorted by RRF score.
    """
    scores: dict[str, float] = {}
    items: dict[str, Any] = {}

    for lst in lists:
        for rank, (item, _score) in enumerate(lst, start=1):
            if hasattr(item, "id"):
                item_id = str(item.id)
            elif isinstance(item, dict):
                item_id = str(item.get("id", ""))
            else:
                item_id = str(item)
            scores[item_id] = scores.get(item_id, 0) + (1.0 / (rrf_constant + rank))
            items[item_id] = item

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(items[item_id], score) for item_id, score in ranked]


async def _enrich_candidates(
    db: AsyncSession,
    candidates: list[tuple[Candidate, float]],
    job_id: str | None = None,
) -> list[dict[str, Any]]:
    """Enrich candidates with skills and compute fit metadata.

    Args:
        db: SQLAlchemy async session.
        candidates: List of (Candidate, score) tuples from RRF fusion.
        job_id: Optional job requisition ID for gap analysis.

    Returns:
        List of enriched candidate dicts.
    """
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

    enriched = []
    for candidate, score in candidates:
        # Fetch skills
        result = await db.execute(
            select(CandidateSkill).where(
                CandidateSkill.candidate_id == candidate.id,
            )
        )
        skills = result.scalars().all()

        skill_names = [s.skill_name for s in skills]

        # Compute fit score from RRF score
        fit_score = round(min(1.0, max(0.0, score)), 2)

        enriched.append({
            "id": str(candidate.id),
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "current_title": candidate.current_title,
            "location": candidate.location,
            "current_employer": candidate.current_employer,
            "visa_status": candidate.visa_status,
            "notice_period_days": candidate.notice_period_days,
            "skills": skill_names,
            "fit_score": fit_score,
            "strengths": [],  # Computed by RankingAgent
            "gaps": [],  # Computed by RankingAgent
        })

    return enriched


async def get_job_details(db: AsyncSession, org_id: Any, job_id: Any) -> dict[str, Any] | None:
    """Fetch full job requisition details for context-aware sourcing.

    Queries the client_contacts table for job requisitions.

    Args:
        db: SQLAlchemy async session.
        org_id: Organization ID for tenant scoping.
        job_id: Job requisition ID.

    Returns:
        Job dict with keys: id, title, client, required_skills,
        location, experience_required, visa_required, description.
        Returns None if job not found.
    """
    from app.models.client_contact import ClientContact

    org_id = _ensure_uuid(org_id)
    job_id = _ensure_uuid(job_id)

    result = await db.execute(
        select(ClientContact).where(
            ClientContact.id == job_id,
            ClientContact.organization_id == org_id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return None

    return {
        "id": str(contact.id),
        "title": contact.title or "Untitled Position",
        "client": contact.organization_name or "Unknown Client",
        "required_skills": [],  # Would come from a separate job_requirements table
        "location": contact.location,
        "experience_required": None,
        "visa_required": False,
        "description": contact.description or "",
    }


def _extract_keywords(query: str) -> list[str]:
    """Extract relevant keywords from a natural language query.

    Filters out stop words and returns meaningful tokens for
    structured search.

    Args:
        query: Natural language query.

    Returns:
        List of keywords (lowercase, no stop words).
    """
    import re

    stop_words = {
        "me", "for", "the", "a", "an", "is", "are", "was", "were",
        "find", "search", "show", "get", "i", "want", "need", "can",
        "you", "your", "that", "this", "with", "have", "has", "had",
        "what", "which", "who", "how", "where", "when", "why", "do",
        "did", "does", "would", "could", "should", "may", "might",
        "but", "and", "or", "not", "no", "be", "it", "its",
        "source", "candidate", "candidates", "top", "requiring", "require",
        "requires", "required", "looking", "seeking", "role", "position",
        "job", "skills", "skill", "experience", "strong", "match", "matches",
        "please", "give", "list", "bring", "fetch", "who", "have", "has",
    }

    words = query.lower().split()
    cleaned_words = []
    for w in words:
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', w)
        if cleaned:
            cleaned_words.append(cleaned)

    keywords = [w for w in cleaned_words if w not in stop_words and len(w) > 1]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)

    return unique
