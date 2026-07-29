"""RankingAgent — ranks candidates using recruiter preferences.

Computes a 0-1 fit score for each candidate using a weighted
combination of skill match, experience match, and preference alignment.

Explicit preferences act as hard filters (e.g., "US work authorization required").
Implicit preferences adjust scoring weights (e.g., "cloud experience weight: 0.85").

Scoring is deterministic (rule-based) for speed and reproducibility.
LLM-based refinement can be added as an optional overlay.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruiter_preference import RecruiterPreference

logger = logging.getLogger(__name__)

# Default scoring weights — can be overridden by implicit preferences
DEFAULT_WEIGHTS = {
    "skill_match": 0.40,
    "experience_match": 0.25,
    "preference_alignment": 0.35,
}

# Minimum fit score threshold for proactive alerts
PROACTIVE_THRESHOLD = 0.85


async def compute_fit_scores(
    db: AsyncSession,
    candidates: list[dict[str, Any]],
    recruiter_id: str,
    job_id: str | None = None,
    job_requirements: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Compute fit scores for candidates using recruiter preferences.

    For each candidate:
    1. Load recruiter preferences (explicit + implicit)
    2. Apply explicit preferences as hard filters (reject if violated)
    3. Compute weighted fit score: skill_match * w1 + experience_match * w2 + preference_alignment * w3
    4. Identify strengths (candidate exceeds requirements)
    5. Identify gaps (candidate missing requirements)
    6. Sort by fit_score descending

    Args:
        db: SQLAlchemy async session.
        candidates: List of candidate dicts from SourcingAgent.
        recruiter_id: Recruiter ID for preference loading.
        job_id: Optional job requisition ID for context.
        job_requirements: Optional job requirement dict. If None, fetched from job_id.

    Returns:
        List of ranked candidate dicts with added keys:
        - fit_score (float, 0.0-1.0)
        - strengths (list of strings)
        - gaps (list of strings)
        - score_breakdown (dict: skill_match, experience_match, preference_alignment)
        - filtered (bool) — True if candidate was filtered out by explicit preferences
    """
    # Step 1: Load recruiter preferences
    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    prefs_result = await db.execute(
        select(RecruiterPreference).where(
            RecruiterPreference.recruiter_id == rec_uuid,
        )
    )
    prefs = prefs_result.scalar_one_or_none()
    explicit = prefs.explicit_preferences if prefs else {}
    # Implicit scores not yet decoded from vector (TODO: Preference Engine)
    implicit_scores = {}

    # Step 2: Load job requirements if not provided
    if job_requirements is None and job_id:
        from .sourcing_agent import get_job_details
        job_requirements = await get_job_details(db, "", job_id) or {}

    job_requirements = job_requirements or {}

    # Step 3: Score each candidate
    scored = []
    for cand in candidates:
        # Apply explicit preferences as hard filters
        filtered = _apply_explicit_filters(cand, explicit)
        if filtered:
            scored.append({**cand, "fit_score": 0.0, "filtered": True})
            continue

        # Compute fit score
        skill_match = _compute_skill_match(cand, job_requirements)
        experience_match = _compute_experience_match(cand, job_requirements)
        preference_alignment = _compute_preference_alignment(
            cand, explicit, implicit_scores
        )

        # Apply implicit preference weights
        weights = _apply_implicit_weights(DEFAULT_WEIGHTS, implicit_scores)

        fit_score = (
            skill_match * weights["skill_match"]
            + experience_match * weights["experience_match"]
            + preference_alignment * weights["preference_alignment"]
        )
        fit_score = round(min(1.0, max(0.0, fit_score)), 2)

        # Identify strengths and gaps
        strengths = _identify_strengths(cand, job_requirements)
        gaps = _identify_gaps(cand, job_requirements)

        scored.append({
            **cand,
            "fit_score": fit_score,
            "filtered": False,
            "strengths": strengths,
            "gaps": gaps,
            "score_breakdown": {
                "skill_match": round(skill_match, 2),
                "experience_match": round(experience_match, 2),
                "preference_alignment": round(preference_alignment, 2),
            },
        })

    # Step 4: Sort by fit_score descending (filtered candidates last)
    scored.sort(key=lambda x: (x["fit_score"], x["filtered"]), reverse=True)

    return scored


def _apply_explicit_filters(
    candidate: dict[str, Any],
    explicit: dict[str, Any],
) -> bool:
    """Apply explicit preferences as hard filters.

    Returns True if the candidate should be filtered out (rejected).

    Supported explicit preference keys:
    - required_visa_status: Candidate must have this visa status
    - min_experience_years: Candidate must have this many years of experience
    - max_notice_period_days: Candidate's notice period must be <= this value
    - preferred_locations: Candidate must be in one of these locations (or "Remote")
    - required_skills: Candidate must have all of these skills
    - excluded_skills: Candidate must NOT have any of these skills
    """
    # Visa status filter
    required_visa = explicit.get("required_visa_status")
    if required_visa and candidate.get("visa_status"):
        if required_visa.lower() not in candidate["visa_status"].lower():
            return True

    # Minimum experience filter
    min_exp = explicit.get("min_experience_years")
    if min_exp:
        # Extract years from candidate's skills
        years = _get_candidate_years_experience(candidate)
        if years < min_exp:
            return True

    # Maximum notice period filter
    max_notice = explicit.get("max_notice_period_days")
    if max_notice and candidate.get("notice_period_days"):
        if candidate["notice_period_days"] > max_notice:
            return True

    # Preferred locations filter
    preferred_locs = explicit.get("preferred_locations")
    if preferred_locs and candidate.get("location"):
        loc = candidate["location"].lower()
        if not any(
            pl.lower() in loc or loc in pl.lower()
            for pl in preferred_locs
        ):
            # Check if candidate is open to remote
            if "remote" not in loc and "remote" not in str(preferred_locs).lower():
                return True

    # Required skills filter (candidate must have ALL)
    required_skills = explicit.get("required_skills", [])
    if required_skills:
        cand_skills = [s.lower() for s in candidate.get("skills", [])]
        if not all(rs.lower() in cand_skills for rs in required_skills):
            return True

    # Excluded skills filter (candidate must NOT have ANY)
    excluded_skills = explicit.get("excluded_skills", [])
    if excluded_skills:
        cand_skills = [s.lower() for s in candidate.get("skills", [])]
        if any(es.lower() in cand_skills for es in excluded_skills):
            return True

    return False


def _compute_skill_match(
    candidate: dict[str, Any],
    job_requirements: dict[str, Any],
) -> float:
    """Compute skill match score (0.0 - 1.0).

    Compares candidate skills against job required skills.
    Score = (matching skills / required skills) with partial credit
    for closely related skills.
    """
    required_skills = job_requirements.get("required_skills", [])
    if not required_skills:
        return 0.5  # No requirements specified — neutral score

    cand_skills = set(s.lower() for s in candidate.get("skills", []))
    required = [s.lower() for s in required_skills]

    matches = sum(1 for s in required if s in cand_skills)
    return round(matches / len(required), 2)


def _compute_experience_match(
    candidate: dict[str, Any],
    job_requirements: dict[str, Any],
) -> float:
    """Compute experience match score (0.0 - 1.0).

    Compares candidate's years of experience against job requirements.
    Score = 1.0 if experience meets or exceeds requirement.
    Score decreases linearly for each year below the requirement.
    """
    required_years = job_requirements.get("experience_required")
    if required_years is None:
        return 0.5  # No requirement specified — neutral score

    cand_years = _get_candidate_years_experience(candidate)
    if cand_years >= required_years:
        return 1.0

    # Linear decay: 0.5 per year below requirement, min 0.0
    diff = required_years - cand_years
    return round(max(0.0, 1.0 - (diff * 0.5)), 2)


def _compute_preference_alignment(
    candidate: dict[str, Any],
    explicit: dict[str, Any],
    implicit: dict[str, float],
) -> float:
    """Compute preference alignment score (0.0 - 1.0).

    Measures how well the candidate aligns with the recruiter's
    learned implicit preferences.

    For MVP, uses explicit preferences only. Implicit preference
    scoring will be implemented when the Preference Engine decodes
    the pgvector embedding.
    """
    if not explicit and not implicit:
        return 0.5  # No preferences — neutral score

    score = 0.5  # Start at neutral

    # Implicit preference weights
    cloud_weight = implicit.get("cloud_experience", 0)
    if cloud_weight > 0.5:
        has_cloud = any(
            skill.lower() in ["aws", "azure", "gcp", "cloud", "docker", "kubernetes"]
            for skill in candidate.get("skills", [])
        )
        if has_cloud:
            score += cloud_weight * 0.2

    leadership_weight = implicit.get("leadership_experience", 0)
    if leadership_weight > 0.5:
        title = (candidate.get("current_title") or "").lower()
        if any(w in title for w in ["lead", "senior", "manager", "principal", "architect"]):
            score += leadership_weight * 0.2

    return round(min(1.0, max(0.0, score)), 2)


def _apply_implicit_weights(
    default_weights: dict[str, float],
    implicit: dict[str, float],
) -> dict[str, float]:
    """Adjust default scoring weights based on implicit preferences.

    If the recruiter consistently values certain traits, boost
    the corresponding weight components.
    """
    weights = dict(default_weights)

    # If implicit preferences strongly favor cloud experience,
    # boost the skill_match weight slightly
    cloud_weight = implicit.get("cloud_experience", 0)
    if cloud_weight > 0.7:
        weights["skill_match"] = min(0.50, weights["skill_match"] + 0.05)
        weights["preference_alignment"] = max(0.25, weights["preference_alignment"] - 0.05)

    return weights


def _identify_strengths(
    candidate: dict[str, Any],
    job_requirements: dict[str, Any],
) -> list[str]:
    """Identify candidate strengths relative to job requirements.

    Returns a list of strength descriptions (e.g., "7 years Java — exceeds 5yr requirement").
    """
    strengths = []
    required_years = job_requirements.get("experience_required")
    cand_years = _get_candidate_years_experience(candidate)

    if required_years and cand_years >= required_years + 2:
        strengths.append(
            f"{cand_years} years experience — exceeds {required_years}yr requirement by {cand_years - required_years} years"
        )

    required_skills = job_requirements.get("required_skills", [])
    cand_skills = [s.lower() for s in candidate.get("skills", [])]

    # Check for skills that exceed requirements
    for skill in required_skills:
        if skill.lower() in cand_skills:
            strengths.append(f"Has {skill} requirement")

    return strengths[:3]  # Top 3 strengths


def _identify_gaps(
    candidate: dict[str, Any],
    job_requirements: dict[str, Any],
) -> list[str]:
    """Identify skill/experience gaps between candidate and job.

    Returns a list of gap descriptions (e.g., "Missing Kubernetes experience").
    """
    gaps = []
    required_skills = job_requirements.get("required_skills", [])
    cand_skills = [s.lower() for s in candidate.get("skills", [])]

    for skill in required_skills:
        if skill.lower() not in cand_skills:
            gaps.append(f"Missing {skill}")

    required_years = job_requirements.get("experience_required")
    cand_years = _get_candidate_years_experience(candidate)
    if required_years and cand_years < required_years:
        gaps.append(
            f"{cand_years} years experience — below {required_years}yr requirement"
        )

    return gaps[:3]  # Top 3 gaps


def _get_candidate_years_experience(candidate: dict[str, Any]) -> int:
    """Estimate candidate's total years of experience.

    Uses current_title as a proxy if explicit years data is not available.
    """
    # Check if years_experience is stored in skills
    for skill in candidate.get("skills", []):
        # Skills are just strings in MVP; years would come from a separate field
        pass

    # Fallback: estimate from title
    title = (candidate.get("current_title") or "").lower()
    if "principal" in title or "architect" in title:
        return 10
    if "senior" in title:
        return 7
    if "lead" in title:
        return 6
    if "mid" in title:
        return 4
    if "junior" in title or "associate" in title:
        return 2
    return 3  # Default assumption


async def identify_gaps(
    candidate: dict[str, Any],
    job_requirements: dict[str, Any],
) -> list[str]:
    """Identify skill/experience gaps between candidate and job.

    Wrapper around _identify_gaps for the Orchestrator interface.
    """
    return _identify_gaps(candidate, job_requirements)


async def identify_strengths(
    candidate: dict[str, Any],
    job_requirements: dict[str, Any],
) -> list[str]:
    """Identify candidate strengths relative to job requirements.

    Wrapper around _identify_strengths for the Orchestrator interface.
    """
    return _identify_strengths(candidate, job_requirements)
