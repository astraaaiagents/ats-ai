"""Orchestrator service — entry point for the Agent Gateway.

This module provides the run_orchestrator() function that the
Agent Gateway API calls to process user messages.

Usage:
    from app.services.agent_orchestrator import run_orchestrator

    result = await run_orchestrator(
        message="Find me Java candidates for the TCS role",
        session=session,
        preferences=prefs,
        db=db,
        org_id="org-123",
        recruiter_id="user-456",
        session_id="session-789",
    )
"""

import logging
from typing import Any

from .graph import orchestrator_graph
from .state import OrchestratorState

logger = logging.getLogger(__name__)


async def run_orchestrator(
    message: str,
    db,
    org_id: str,
    recruiter_id: str,
    session_id: str,
    job_id: str | None = None,
    preferences: Any = None,
) -> dict[str, Any]:
    """Run the Orchestrator to process a user message.

    This is the main entry point called by the Agent Gateway API.
    It invokes the LangGraph StateGraph and returns the synthesized
    response with cards and actions.

    Args:
        message: The user's message.
        db: SQLAlchemy async session.
        org_id: Organization ID for tenant scoping.
        recruiter_id: Recruiter ID for preference loading.
        session_id: Conversation session ID.
        job_id: Optional job requisition ID.
        preferences: RecruiterPreference model instance.

    Returns:
        Dict with keys:
        - response: str (natural language response)
        - cards: list[dict] (structured cards for UI)
        - actions: list[dict] (action buttons for UI)
        - sources: list[dict] (data provenance)
        - confidence: float (0.0 - 1.0)
        - intent: str (classified intent)
    """
    initial_state: OrchestratorState = {
        "message": message,
        "messages": [],  # Will be populated by LangGraph message handling
        "intent": "",
        "candidates": [],
        "ranked_candidates": [],
        "outreach_drafts": [],
        "response": "",
        "cards": [],
        "actions": [],
        "sources": [],
        "confidence": 0.0,
        "error": None,
        "recruiter_id": recruiter_id,
        "session_id": session_id,
        "org_id": org_id,
        "job_id": job_id,
    }

    # Inject DB session into state for specialist agents
    initial_state["_db"] = db

    try:
        result = await orchestrator_graph.ainvoke(initial_state)
        return {
            "response": result.get("response", ""),
            "cards": result.get("cards", []),
            "actions": result.get("actions", []),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "intent": result.get("intent", ""),
        }
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        return {
            "response": "I'm sorry, I encountered an error processing your request. Please try again.",
            "cards": [],
            "actions": [],
            "sources": [],
            "confidence": 0.0,
            "intent": "",
            "error": str(e),
        }
