"""Intent classifier for the Orchestrator.

Classifies user messages into discrete intents that determine
which specialist agent(s) to delegate to.

Uses a hybrid approach:
1. LLM-based classification for accurate intent detection
2. Rule-based keyword matching as fallback (fast, no API cost)
"""

import json
import logging
from typing import Final

from .llm_provider import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)

# Valid intents
INTENT_SOURCE_CANDIDATES: Final = "source_candidates"
INTENT_CHECK_PIPELINE: Final = "check_pipeline"
INTENT_UPDATE_PREFERENCES: Final = "update_preferences"
INTENT_SCHEDULE_INTERVIEW: Final = "schedule_interview"
INTENT_DRAFT_OUTREACH: Final = "draft_outreach"
INTENT_GENERAL_CONVERSATION: Final = "general_conversation"

INTENTS = [
    INTENT_SOURCE_CANDIDATES,
    INTENT_CHECK_PIPELINE,
    INTENT_UPDATE_PREFERENCES,
    INTENT_SCHEDULE_INTERVIEW,
    INTENT_DRAFT_OUTREACH,
    INTENT_GENERAL_CONVERSATION,
]

# Rule-based patterns for fast classification.
# Each tuple: (intent, list_of_keywords/phrases)
# The first matching rule wins — order matters!
# More specific patterns come first to avoid false matches.
RULES: Final = [
    (INTENT_SCHEDULE_INTERVIEW, [
        "schedule an interview", "schedule interview", "book an interview",
        "book interview", "when are you free", "available on", "calendar",
        "book a meeting", "schedule a meeting",
    ]),
    (INTENT_DRAFT_OUTREACH, [
        "draft outreach", "draft an email", "draft an outreach",
        "reach out to", "write to", "invite to",
        "draft email", "draft message", "outreach message",
        "write an email", "send an email",
    ]),
    (INTENT_CHECK_PIPELINE, [
        "pipeline", "status", "progress", "tracking",
        "submitted", "shortlist", "shortlisted",
        "what's happening", "upcoming",
        "where are my", "pipeline status",
    ]),
    (INTENT_UPDATE_PREFERENCES, [
        "remember", "preference", "always", "never",
        "don't want", "don't like",
        "setting", "add rule", "remove rule", "filter rule",
    ]),
    (INTENT_SOURCE_CANDIDATES, [
        "source", "find", "search", "candidates", "candidate", "who has",
        "developer", "engineer", "qualified", "top matches", "top candidates",
        "java", "python", "react",
    ]),
]

# System prompt for LLM-based intent classification
INTENT_CLASSIFICATION_SYSTEM_PROMPT = """\
You are an intent classifier for a recruiting assistant agent.
Classify the user's message into exactly ONE of these intents:
- source_candidates: User wants to find/search for candidates
- check_pipeline: User wants to check pipeline status, progress, submitted candidates
- update_preferences: User wants to set/update preferences or rules
- schedule_interview: User wants to schedule/book an interview
- draft_outreach: User wants to draft outreach messages/emails
- general_conversation: Everything else (greetings, questions, etc.)

Respond with ONLY the intent name, nothing else. No explanation.
"""


async def classify_intent(message: str, job_id: str | None = None) -> str:
    """Classify the user's message into an intent.

    Uses LLM-based classification first, falls back to rule-based
    keyword matching if LLM is unavailable.

    Args:
        message: The user's message text.
        job_id: Optional job ID context (not used in classification).

    Returns:
        One of the INTENT_* constants.
    """
    try:
        return await classify_intent_llm(message)
    except Exception as exc:
        logger.warning(f"LLM classification failed ({exc}), falling back to rule-based")
        return classify_intent_rule_based(message)


async def classify_intent_llm(message: str) -> str:
    """Classify intent using the LLM.

    Args:
        message: The user's message text.

    Returns:
        One of the INTENT_* constants.

    Raises:
        Exception: If LLM call fails (caller should fall back to rule-based).
    """
    provider = get_llm_provider()
    raw = await provider.classify(
        prompt=message,
        system_prompt=INTENT_CLASSIFICATION_SYSTEM_PROMPT,
    )
    intent = raw.strip().lower()
    # Validate the intent is one of the known intents
    if intent in INTENTS:
        return intent
    logger.warning(f"LLM returned unknown intent '{intent}', defaulting to general_conversation")
    return INTENT_GENERAL_CONVERSATION


def classify_intent_rule_based(message: str) -> str:
    """Classify intent using rule-based keyword matching.

    Fast, deterministic, no API cost. Used as fallback when LLM is unavailable.

    Args:
        message: The user's message text.

    Returns:
        One of the INTENT_* constants.
    """
    lower = message.lower()

    for intent, patterns in RULES:
        for pattern in patterns:
            if pattern in lower:
                return intent

    return INTENT_GENERAL_CONVERSATION


def build_intent_prompt(intent: str, message: str, job_id: str | None = None) -> str:
    """Build a prompt for the LLM based on the classified intent.

    This prompt is sent to the LLM to guide the Orchestrator's response
    synthesis. It includes the intent and any relevant context.

    Args:
        intent: The classified intent.
        message: The original user message.
        job_id: Optional job ID context.

    Returns:
        A prompt string for the LLM.
    """
    prompts = {
        INTENT_SOURCE_CANDIDATES: (
            f"Intent: source_candidates\n"
            f"User message: {message}\n"
            f"{'Job context: ' + job_id if job_id else ''}\n"
            f"Action: Search the candidate database for matches. "
            f"Return ranked candidates with fit scores, strengths, and gaps."
        ),
        INTENT_CHECK_PIPELINE: (
            f"Intent: check_pipeline\n"
            f"User message: {message}\n"
            f"Action: Check the candidate pipeline status. "
            f"Return summary of submitted, interviewed, and placed candidates."
        ),
        INTENT_UPDATE_PREFERENCES: (
            f"Intent: update_preferences\n"
            f"User message: {message}\n"
            f"Action: Parse the user's preference statement and update "
            f"their explicit preferences. Confirm the update to the user."
        ),
        INTENT_SCHEDULE_INTERVIEW: (
            f"Intent: schedule_interview\n"
            f"User message: {message}\n"
            f"Action: Acknowledge the request. Note: actual scheduling "
            f"requires Google Calendar integration (Phase 4+). "
            f"Tell the user this is noted for when scheduling is available."
        ),
        INTENT_DRAFT_OUTREACH: (
            f"Intent: draft_outreach\n"
            f"User message: {message}\n"
            f"Action: Draft personalized outreach messages for the "
            f"selected candidates. Include subject line, body, and CTA."
        ),
        INTENT_GENERAL_CONVERSATION: (
            f"Intent: general_conversation\n"
            f"User message: {message}\n"
            f"Action: Provide a helpful response. If the user seems to "
            f"want to source candidates, check pipeline, or update "
            f"preferences, suggest the relevant action."
        ),
    }
    return prompts.get(intent, prompts[INTENT_GENERAL_CONVERSATION])
