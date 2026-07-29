"""OutreachAgent — drafts personalized outreach messages.

Called by the Orchestrator when intent is "draft_outreach".
Generates personalized email/message drafts for each candidate
using LLM-based generation with recruiter style preferences.
"""

import json
import logging
from typing import Any

from .llm_provider import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)

OUTREACH_GENERATION_SYSTEM_PROMPT = """\
You are a recruiting assistant that writes personalized outreach messages.
Write professional, engaging outreach messages for candidates.

Rules:
- Keep subject lines under 60 characters
- Personalize the body with the candidate's specific skills and background
- Reference the job role and why it fits the candidate
- Include a clear call to action
- Keep tone professional but warm
- Do NOT include any placeholder text like [link] or [name]
"""


async def generate_outreach(
    candidates: list[dict[str, Any]],
    job_context: dict[str, Any],
    recruiter_id: str,
) -> list[dict[str, Any]]:
    """Generate personalized outreach drafts for candidates.

    Uses LLM to generate personalized subject, body, and CTA for each
    candidate, incorporating their skills and the job context.

    Args:
        candidates: List of candidate dicts (from RankingAgent).
        job_context: Job requisition dict (title, client, requirements).
        recruiter_id: Recruiter ID for style preference loading.

    Returns:
        List of outreach draft dicts with keys:
        - candidate_id, subject, body, cta, tone
    """
    drafts = []
    for cand in candidates[:3]:  # Top 3 candidates
        draft = await _generate_single_outreach(cand, job_context)
        if draft:
            drafts.append(draft)
        else:
            # Fallback to template-based draft
            drafts.append(_template_outreach(cand, job_context))

    return drafts


async def _generate_single_outreach(
    candidate: dict[str, Any],
    job_context: dict[str, Any],
) -> dict[str, Any] | None:
    """Generate a single outreach draft using the LLM.

    Args:
        candidate: Candidate dict with skills, name, title.
        job_context: Job requisition dict.

    Returns:
        Draft dict with subject, body, cta, or None on failure.
    """
    first_name = candidate.get("first_name", "there")
    current_title = candidate.get("current_title", "")
    skills = candidate.get("skills", [])
    job_title = job_context.get("title", "a role")
    client = job_context.get("client", "")

    prompt = (
        f"Write an outreach message for this candidate:\n"
        f"Name: {first_name}\n"
        f"Title: {current_title}\n"
        f"Skills: {', '.join(skills[:5]) if skills else 'None listed'}\n"
        f"Job: {job_title}"
        + (f" at {client}" if client else "")
        + (f"\nStrengths: {', '.join(candidate.get('strengths', [])[:3])}" if candidate.get("strengths") else "")
        + (f"\nGaps: {', '.join(candidate.get('gaps', [])[:3])}" if candidate.get("gaps") else "")
        + "\n\nWrite a concise, personalized message. Include subject, body, and a single CTA."
    )

    try:
        provider = get_llm_provider()
        raw = await provider.generate(
            prompt=prompt,
            system_prompt=OUTREACH_GENERATION_SYSTEM_PROMPT,
        )
        return _parse_outreach_response(raw, candidate.get("id", ""), first_name)
    except Exception as exc:
        logger.warning(f"LLM outreach generation failed ({exc}), using template")
        return None


def _parse_outreach_response(raw: str, candidate_id: str, first_name: str) -> dict[str, Any]:
    """Parse LLM outreach response into structured draft.

    Tries JSON first, falls back to heuristic parsing.

    Args:
        raw: Raw LLM text response.
        candidate_id: Candidate ID.
        first_name: Candidate first name.

    Returns:
        Structured draft dict.
    """
    raw = raw.strip()

    # Try parsing as JSON
    try:
        data = json.loads(raw)
        return {
            "candidate_id": candidate_id,
            "subject": data.get("subject", f"Opportunity: {data.get('job_title', 'new role')}"),
            "body": data.get("body", f"Hi {first_name}, I have an opportunity for you."),
            "cta": data.get("cta", "Let me know if you're interested."),
            "tone": data.get("tone", "professional"),
        }
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: heuristic parsing
    lines = raw.split("\n")
    subject = ""
    body_lines = []
    cta = ""
    in_body = False

    for line in lines:
        lower = line.lower().strip()
        if lower.startswith(("subject:", "subject line:", "re:")):
            subject = line.split(":", 1)[-1].strip()
            in_body = False
        elif lower.startswith(("cta:", "call to action:", "next step:")):
            cta = line.split(":", 1)[-1].strip()
            in_body = False
        elif lower.startswith(("hi ", "hello ", "dear ", "hey ")):
            in_body = True
            body_lines.append(line)
        elif in_body:
            body_lines.append(line)

    if not subject:
        subject = f"Opportunity for {first_name}"
    if not body_lines:
        body_lines = [f"Hi {first_name}, I came across your profile and wanted to share an opportunity."]
    if not cta:
        cta = "Would you be open to a quick conversation?"

    body = "\n".join(body_lines).strip()

    return {
        "candidate_id": candidate_id,
        "subject": subject,
        "body": body,
        "cta": cta,
        "tone": "professional",
    }


def _template_outreach(candidate: dict, job_context: dict) -> dict[str, Any]:
    """Template-based fallback outreach draft.

    Used when LLM generation fails.

    Args:
        candidate: Candidate dict.
        job_context: Job requisition dict.

    Returns:
        Template outreach draft dict.
    """
    first_name = candidate.get("first_name", "")
    current_title = candidate.get("current_title", "")
    skills = candidate.get("skills", [])
    job_title = job_context.get("title", "a new role")
    client = job_context.get("client", "")

    return {
        "candidate_id": candidate.get("id", ""),
        "subject": f"Opportunity: {job_title}" + (f" at {client}" if client else ""),
        "body": (
            f"Hi {first_name},\n\n"
            f"I came across your profile and was impressed by your experience as a "
            f"{current_title}"
            + (f" with skills in {', '.join(skills[:3])}" if skills else "")
            + f". We have a {job_title}"
            + (f" opening at {client}" if client else "")
            + f" that seems like a great fit.\n\n"
            f"Would you be open to a quick conversation?"
        ),
        "cta": "Reply to this message or book a call here.",
        "tone": "professional",
    }


async def get_email_templates(db, org_id: str) -> list[dict[str, Any]]:
    """Get available email templates for outreach.

    MVP placeholder: returns empty list.
    Production implementation will query templates from the database.

    Args:
        db: SQLAlchemy async session.
        org_id: Organization ID for tenant scoping.

    Returns:
        List of template dicts with keys: id, name, subject_template, body_template.
    """
    logger.warning(
        "OutreachAgent.get_email_templates called — MVP placeholder."
    )
    return []
