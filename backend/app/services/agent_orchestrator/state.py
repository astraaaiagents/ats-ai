"""Orchestrator state schema.

Defines the shared state that flows through the LangGraph StateGraph.
All nodes read/write this state to communicate.
"""

from typing import Any, TypedDict

from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class OrchestratorState(TypedDict):
    """Shared state for the Orchestrator agent graph.

    This state flows through all nodes in the graph. Each node reads
    relevant fields and writes its outputs for downstream nodes.
    """

    # --- User input ---
    # The user's original message
    message: str

    # --- Conversation context ---
    # Annotated with add_messages for automatic message merging
    messages: Annotated[list, add_messages]

    # --- Intent classification ---
    # Detected intent: "source_candidates", "check_pipeline",
    # "update_preferences", "schedule_interview", "draft_outreach",
    # "general_conversation"
    intent: str

    # --- Sourcing results ---
    # List of candidate dicts from SourcingAgent
    candidates: list[dict[str, Any]]

    # --- Ranking results ---
    # Ranked candidates with fit scores, strengths, gaps
    ranked_candidates: list[dict[str, Any]]

    # --- Outreach results ---
    # Drafted outreach messages
    outreach_drafts: list[dict[str, Any]]

    # --- Response synthesis ---
    # Final natural language response
    response: str

    # --- Structured cards for UI ---
    # Candidate cards, job cards, alert cards, etc.
    cards: list[dict[str, Any]]

    # --- Action buttons for UI ---
    actions: list[dict[str, Any]]

    # --- Data provenance ---
    sources: list[dict[str, str]]

    # --- Confidence score (0.0 - 1.0) ---
    confidence: float

    # --- Error handling ---
    # Error message if any node fails
    error: str | None

    # --- Metadata ---
    recruiter_id: str
    session_id: str
    org_id: str
    job_id: str | None  # Optional: specific job context

    # --- Internal: DB session (injected at runtime, not part of persistence) ---
    _db: Any | None
