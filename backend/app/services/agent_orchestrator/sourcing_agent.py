"""SourcingAgent — searches the candidate database with hybrid search.

Combines structured SQL filters, full-text search (tsvector), and
vector similarity search (pgvector) using Reciprocal Rank Fusion (RRF).

Returns ranked candidate profiles with fit metadata for the Orchestrator.
"""

import logging
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

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
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

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


async def _structured_search(
    db: AsyncSession,
    org_id: str,
    keywords: list[str],
    limit: int,
) -> list[tuple[Candidate, float]]:
    """Search candidates using structured keyword matching.

    Matches keywords against title, location, employer fields.
    Returns candidates ranked by keyword match score.
    """
    from app.models.candidate import Candidate

    if not keywords:
        # No keywords — return all candidates (low score)
        result = await db.execute(
            select(Candidate)
            .where(Candidate.organization_id == org_id)
            .where(Candidate.status != "archived")
            .limit(limit)
        )
        return [(c, 0.1) for c in result.scalars().all()]

    # Build OR clause for keyword matching (embedded as raw SQL, not a param)
    or_parts = [f"POSITION(:kw{i} IN current_title) > 0 OR POSITION(:kw{i} IN location) > 0 OR POSITION(:kw{i} IN current_employer) > 0" for i in range(len(keywords))]
    or_sql = " OR ".join(f"({part})" for part in or_parts)

    params = {"org_id": org_id}
    for i, kw in enumerate(keywords):
        params[f"kw{i}"] = kw

    # First, get matching candidate IDs
    id_query = text(f"""
        SELECT id
        FROM candidates
        WHERE organization_id = :org_id
          AND status != 'archived'
          AND (
              {or_sql}
          )
        ORDER BY created_at
        LIMIT :limit
    """)

    id_result = await db.execute(id_query, {**params, "limit": limit})
    candidate_ids = [row[0] for row in id_result.all()]

    if not candidate_ids:
        return []

    # Fetch full candidate records for matching IDs
    result = await db.execute(
        select(Candidate)
        .where(
            Candidate.organization_id == org_id,
            Candidate.id.in_(candidate_ids),
            Candidate.status != "archived",
        )
    )
    candidates = result.scalars().all()

    # Return (Candidate, score) tuples — score is the RRF rank position
    return [(c, 1.0 / (i + 1)) for i, c in enumerate(candidates)]


async def _fts_search(
    db: AsyncSession,
    org_id: str,
    query: str,
    limit: int,
) -> list[tuple[Candidate, float]]:
    """Search candidates using PostgreSQL full-text search (tsvector).

    Combines tsvector ranking with keyword matching across candidate
    profile fields (title, employer, location).
    """
    from app.models.candidate import Candidate

    # Use ts_rank for full-text search ranking
    # In production, create a tsvector column on candidates table
    # For MVP, use a simpler approach with ILIKE
    result = await db.execute(
        select(Candidate)
        .where(
            Candidate.organization_id == org_id,
            Candidate.status != "archived",
            text("""
                to_tsvector('english',
                    COALESCE(current_title, '') || ' ' ||
                    COALESCE(current_employer, '') || ' ' ||
                    COALESCE(location, '')
                ) @@ plainto_tsquery('english', :query)
            """),
        )
        .limit(limit),
        {"query": query},
    )
    candidates = result.scalars().all()
    return [(c, 1.0 / (i + 1)) for i, c in enumerate(candidates)]


async def _vector_search(
    db: AsyncSession,
    org_id: str,
    query: str,
    limit: int,
) -> list[tuple[Candidate, float]]:
    """Search candidates using pgvector skill embeddings.

    Uses cosine similarity on candidate skill embeddings to find
    candidates with semantically similar skills to the query.

    Falls back to ILIKE skill name matching if no embeddings exist.
    """
    from app.models.candidate import Candidate
    from app.models.candidate_skill import CandidateSkill

    try:
        # Try pgvector cosine similarity search
        # First, we need to embed the query — for MVP, we use the first
        # skill keyword from the query as a proxy
        query_skill = query.split()[0] if query else ""

        # Find skills matching the query keyword, then get their embeddings
        skills_result = await db.execute(
            select(CandidateSkill.skill_embedding)
            .where(
                CandidateSkill.organization_id == org_id,
                CandidateSkill.skill_embedding.isnot(None),
                CandidateSkill.skill_name.ilike(f"%{query_skill}%"),
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
                candidate_ids = list(candidate_scores.keys())[:limit]
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

    # Fallback: ILIKE skill name matching
    result = await db.execute(
        select(CandidateSkill)
        .where(
            CandidateSkill.organization_id == org_id,
            CandidateSkill.skill_name.ilike(f"%{query.split()[0]}%") if query else False,
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
    candidate_ids = list(candidate_scores.keys())[:limit]
    result = await db.execute(
        select(Candidate).where(
            Candidate.organization_id == org_id,
            Candidate.id.in_(candidate_ids),
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
            item_id = str(getattr(item, "id", item.get("id", "")))
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


async def get_job_details(db: AsyncSession, org_id: str, job_id: str) -> dict[str, Any] | None:
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
    stop_words = {
        "me", "for", "the", "a", "an", "is", "are", "was", "were",
        "find", "search", "show", "get", "i", "want", "need", "can",
        "you", "your", "that", "this", "with", "have", "has", "had",
        "what", "which", "who", "how", "where", "when", "why", "do",
        "did", "does", "would", "could", "should", "may", "might",
        "but", "and", "or", "not", "no", "be", "it", "its",
    }

    words = query.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)

    return unique
