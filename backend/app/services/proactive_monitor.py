"""Proactive Monitor — background service for candidate match alerts.

Runs a sourcing pulse every 30 minutes for each active recruiter:
1. Fetch open job requisitions
2. Fetch recruiter preferences (explicit + implicit)
3. Query new candidates since last pulse
4. Run RankingAgent on new candidates
5. If top match score > threshold → generate proactive alert
6. Store alert in agent_proactive_alerts table
7. Push alert to recruiter's Chat UI via SSE

Uses APScheduler for cron scheduling (ARQ is in maintenance-only mode).

Alert batching: max 3 alerts per hour per recruiter.
Graceful degradation: failures are logged and skipped (no retry).
Performance: parallel processing via asyncio.gather.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
import uuid
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.agent_alert import AgentProactiveAlert
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.user import User

logger = logging.getLogger(__name__)

# Sourcing pulse interval: 30 minutes
PULSE_INTERVAL_MINUTES = 30

# Alert batching: max alerts per recruiter per hour
MAX_ALERTS_PER_HOUR = 3

# Default fit score threshold for proactive alerts
DEFAULT_THRESHOLD = 0.85

# Scheduler instance (created at module level)
_scheduler: AsyncIOScheduler | None = None


def start_monitor() -> AsyncIOScheduler:
    """Start the proactive monitor scheduler.

    Adds a cron job that fires every 30 minutes to run the sourcing pulse.

    Returns:
        The APScheduler instance.
    """
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_sourcing_pulse,
        "interval",
        minutes=PULSE_INTERVAL_MINUTES,
        id="sourcing_pulse",
        name="Sourcing Pulse",
        max_instances=1,  # Prevent overlapping pulses
    )
    _scheduler.start()
    logger.info("Proactive Monitor started — sourcing pulse every %d minutes", PULSE_INTERVAL_MINUTES)
    return _scheduler


def stop_monitor() -> None:
    """Stop the proactive monitor scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Proactive Monitor stopped")


async def _run_sourcing_pulse() -> None:
    """Run the sourcing pulse for all active recruiters.

    Processes recruiters in parallel using asyncio.gather.
    Each recruiter's pulse is independent and runs concurrently.
    """
    logger.info("Starting sourcing pulse")
    start_time = datetime.now(timezone.utc)

    try:
        async with async_session_factory() as db:
            # Fetch all active recruiters
            result = await db.execute(
                select(User).where(
                    User.role == "recruiter",
                    User.is_active == True,  # noqa: E712
                )
            )
            recruiters = result.scalars().all()

        if not recruiters:
            logger.info("No active recruiters — skipping pulse")
            return

        # Run pulses in parallel
        tasks = [_process_recruiter_pulse(str(r.id)) for r in recruiters]
        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            "Sourcing pulse completed — %d recruiters in %.1fs",
            len(recruiters),
            elapsed,
        )
    except Exception:
        logger.error("Sourcing pulse failed", exc_info=True)
        # Graceful degradation: log and continue (don't crash the scheduler)


async def _process_recruiter_pulse(recruiter_id: str) -> None:
    """Process a single recruiter's sourcing pulse.

    1. Fetch open job requisitions
    2. Fetch recruiter preferences
    3. Query new candidates since last pulse
    4. Run RankingAgent on new candidates
    5. Generate alerts for top matches

    Args:
        recruiter_id: Recruiter ID to process.
    """
    try:
        async with async_session_factory() as db:
            # Check alert batching limit
            recent_count = await _count_recent_alerts(db, recruiter_id)
            if recent_count >= MAX_ALERTS_PER_HOUR:
                logger.debug(
                    "Recruiter %s has %d recent alerts — skipping pulse",
                    recruiter_id,
                    recent_count,
                )
                return

            # Fetch new candidates since last pulse
            last_pulse = await _get_last_pulse_time(db, recruiter_id)
            new_candidates = await _fetch_new_candidates(db, recruiter_id, last_pulse)

            if not new_candidates:
                logger.debug("Recruiter %s has no new candidates", recruiter_id)
                await _update_last_pulse_time(db, recruiter_id)
                return

            # TODO: Run RankingAgent on new candidates
            # For MVP, use placeholder scoring
            top_matches = await _score_new_candidates(
                db, recruiter_id, new_candidates
            )

            if top_matches:
                # Generate alert for top matches
                await _create_alert(
                    db, recruiter_id, top_matches
                )

            # Update last pulse time
            await _update_last_pulse_time(db, recruiter_id)

    except Exception:
        logger.error(
            "Recruiter %s pulse failed", recruiter_id, exc_info=True
        )
        # Graceful degradation: log and continue


async def _count_recent_alerts(
    db: AsyncSession, recruiter_id: str
) -> int:
    """Count alerts created in the last hour for a recruiter.

    Used for alert batching (max 3 per hour).
    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    result = await db.execute(
        select(func.count(AgentProactiveAlert.id)).where(
            AgentProactiveAlert.recruiter_id == rec_uuid,
            AgentProactiveAlert.created_at >= one_hour_ago,
        )
    )
    return result.scalar() or 0


async def _get_last_pulse_time(
    db: AsyncSession, recruiter_id: str
) -> datetime | None:
    """Get the timestamp of the last sourcing pulse for a recruiter.

    Uses the most recent proactive alert's creation time as a proxy.
    Returns None if no alerts exist (all candidates are "new").
    """
    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    result = await db.execute(
        select(AgentProactiveAlert.created_at)
        .where(AgentProactiveAlert.recruiter_id == rec_uuid)
        .order_by(AgentProactiveAlert.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _fetch_new_candidates(
    db: AsyncSession,
    recruiter_id: str,
    since: datetime | None,
) -> list[Candidate]:
    """Fetch candidates created/updated since the last pulse.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID (for org scoping).
        since: Timestamp of last pulse. None = all candidates.

    Returns:
        List of new Candidate records.
    """
    # Get recruiter's organization
    try:
        rec_uuid = uuid.UUID(recruiter_id) if isinstance(recruiter_id, str) else recruiter_id
    except ValueError:
        rec_uuid = recruiter_id
    result = await db.execute(
        select(User).where(User.id == rec_uuid)
    )
    user = result.scalar_one_or_none()
    if not user or not user.organization_id:
        return []

    org_id = user.organization_id

    query = select(Candidate).where(
        Candidate.organization_id == org_id,
        Candidate.status != "archived",
    )
    if since:
        query = query.where(
            Candidate.created_at >= since
        )

    query = query.order_by(Candidate.created_at.desc()).limit(50)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _score_new_candidates(
    db: AsyncSession,
    recruiter_id: str,
    candidates: list[Candidate],
) -> list[dict[str, Any]]:
    """Score new candidates against recruiter preferences.

    MVP placeholder: uses simple heuristic scoring.
    Production: calls RankingAgent.compute_fit_scores().

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        candidates: List of new candidates.

    Returns:
        List of top-matching candidate dicts with fit scores.
    """
    from app.services.agent_orchestrator.ranking_agent import (
        compute_fit_scores,
        DEFAULT_THRESHOLD,
    )

    # Convert Candidate models to dicts for RankingAgent
    candidate_dicts = []
    for c in candidates:
        candidate_dicts.append({
            "id": str(c.id),
            "first_name": c.first_name,
            "last_name": c.last_name,
            "current_title": c.current_title,
            "location": c.location,
            "current_employer": c.current_employer,
            "visa_status": c.visa_status,
            "notice_period_days": c.notice_period_days,
            "skills": [],  # Would fetch from CandidateSkill
        })

    # TODO: Fetch skills for each candidate
    # for cd in candidate_dicts:
    #     skills_result = await db.execute(
    #         select(CandidateSkill).where(
    #             CandidateSkill.candidate_id == UUID(cd["id"])
    #         )
    #     )
    #     cd["skills"] = [s.skill_name for s in skills_result.scalars().all()]

    # Run RankingAgent
    ranked = await compute_fit_scores(
        db=db,
        candidates=candidate_dicts,
        recruiter_id=recruiter_id,
    )

    # Filter to top matches above threshold
    top_matches = [
        c for c in ranked
        if c.get("fit_score", 0) >= DEFAULT_THRESHOLD and not c.get("filtered", False)
    ]

    return top_matches[:3]  # Top 3 matches


async def _create_alert(
    db: AsyncSession,
    recruiter_id: str,
    matches: list[dict[str, Any]],
) -> None:
    """Create a proactive alert for top candidate matches.

    Args:
        db: SQLAlchemy async session.
        recruiter_id: Recruiter ID.
        matches: List of top-matching candidate dicts.
    """
    if not matches:
        return

    # Build alert body
    match_names = [
        f"{m['first_name']} {m['last_name']} ({m['fit_score']:.0%})"
        for m in matches
    ]
    body = ", ".join(match_names)

    alert = AgentProactiveAlert(
        recruiter_id=recruiter_id,
        alert_type="new_match",
        title=f"{len(matches)} strong match{'es' if len(matches) > 1 else ''} for your open roles",
        body=body,
        data={
            "candidates": [
                {
                    "id": m["id"],
                    "name": f"{m['first_name']} {m['last_name']}",
                    "fit_score": m["fit_score"],
                    "strengths": m.get("strengths", []),
                    "gaps": m.get("gaps", []),
                }
                for m in matches
            ]
        },
        is_read=False,
    )
    db.add(alert)
    await db.flush()

    logger.info(
        "Created proactive alert for recruiter %s: %d matches",
        recruiter_id,
        len(matches),
    )

    # Push alert to SSE stream for real-time delivery
    alert_data = {
        "id": str(alert.id),
        "alert_type": alert.alert_type,
        "title": alert.title,
        "body": alert.body,
        "data": alert.data,
        "is_read": alert.is_read,
        "created_at": alert.created_at.isoformat(),
    }
    try:
        from app.routes.sse import push_alert_to_recruiter
        await push_alert_to_recruiter(recruiter_id, alert_data)
    except Exception:
        logger.warning("Failed to push SSE alert for recruiter %s", recruiter_id)


# --- Public API for manual pulse trigger (testing, admin) ---


async def trigger_pulse_manually() -> dict[str, Any]:
    """Manually trigger a sourcing pulse (for testing/admin).

    This bypasses the scheduler and runs the pulse immediately.

    Returns:
        Summary of the pulse execution.
    """
    logger.info("Manual sourcing pulse triggered")
    start_time = datetime.now(timezone.utc)

    try:
        await _run_sourcing_pulse()
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        return {
            "status": "completed",
            "elapsed_seconds": round(elapsed, 2),
            "scheduled": False,
        }
    except Exception as e:
        logger.error("Manual pulse failed", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "elapsed_seconds": round(
                (datetime.now(timezone.utc) - start_time).total_seconds(), 2
            ),
        }
