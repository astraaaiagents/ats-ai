"""Orchestrator LangGraph graph definition.

Defines the StateGraph that coordinates the Orchestrator workflow:
1. Classify intent (which specialist to call)
2. Route to specialist node(s) based on intent
3. Synthesize response from specialist outputs
4. Return structured response with cards and actions

The graph is compiled once at import time and reused for all requests.
"""

import logging
from langgraph.graph import END, START, StateGraph

from .state import OrchestratorState
from . import intent_classifier, sourcing_agent, ranking_agent, outreach_agent

logger = logging.getLogger(__name__)


# --- Node implementations ---


async def classify_intent_node(state: OrchestratorState) -> dict:
    """Classify the user's message into an intent.

    This is the first node in the graph. It determines which
    specialist agent(s) to delegate to.
    """
    intent = await intent_classifier.classify_intent(
        state["message"],
        job_id=state.get("job_id"),
    )
    logger.info(f"Intent classified: {intent} for message: {state['message'][:50]}...")
    return {"intent": intent}


async def source_candidates_node(state: OrchestratorState) -> dict:
    """Search the candidate database.

    Called when intent is "source_candidates".
    """
    query = state["message"]
    candidates = await sourcing_agent.search_candidates(
        db=state.get("_db"),  # Passed via invoke kwargs
        org_id=state["org_id"],
        recruiter_id=state["recruiter_id"],
        query=query,
        job_id=state.get("job_id"),
    )

    # Rank candidates
    ranked = await ranking_agent.compute_fit_scores(
        db=state.get("_db"),
        candidates=candidates,
        recruiter_id=state["recruiter_id"],
        job_id=state.get("job_id"),
        query=query,
    )

    # Build cards and actions
    cards = []
    actions = []
    for i, cand in enumerate(ranked[:5]):  # Top 5
        cards.append({
            "type": "candidate",
            "data": {
                "id": cand.get("id", ""),
                "first_name": cand.get("first_name", ""),
                "last_name": cand.get("last_name", ""),
                "current_title": cand.get("current_title", ""),
                "location": cand.get("location", ""),
                "skills": cand.get("skills", []),
            },
            "fitScore": cand.get("fit_score", 0.0),
            "strengths": cand.get("strengths", []),
            "gaps": cand.get("gaps", []),
        })
        actions.append({
            "id": f"approve_{i}",
            "label": "Approve",
            "type": "approve",
            "payload": {"candidate_id": cand.get("id", "")},
        })
        actions.append({
            "id": f"submit_{i}",
            "label": "Submit",
            "type": "submit",
            "payload": {"candidate_id": cand.get("id", "")},
            "confirmation": "Submit this candidate to the client?",
        })

    # Confidence: high if we have ranked candidates, low otherwise
    confidence = min(0.9, 0.5 + len(ranked) * 0.1)

    return {
        "candidates": candidates,
        "ranked_candidates": ranked,
        "cards": cards,
        "actions": actions,
        "confidence": confidence,
        "sources": [{"type": "internal_db", "identifier": "candidates", "timestamp": ""}],
    }


async def check_pipeline_node(state: OrchestratorState) -> dict:
    """Check candidate pipeline status.

    Called when intent is "check_pipeline".
    MVP placeholder: returns a generic response.
    """
    logger.info("Pipeline check requested — MVP placeholder")
    return {
        "response": "Pipeline checking is not yet implemented. This will show submitted, interviewed, and placed candidates.",
        "cards": [],
        "actions": [],
        "confidence": 0.3,
        "sources": [],
    }


async def update_preferences_node(state: OrchestratorState) -> dict:
    """Parse and apply preference update.

    Called when intent is "update_preferences".
    MVP placeholder: acknowledges the request.
    """
    logger.info("Preference update requested — MVP placeholder")
    return {
        "response": f"Preference update noted: {state['message']}. This will be parsed and applied in production.",
        "cards": [],
        "actions": [],
        "confidence": 0.4,
        "sources": [],
    }


async def draft_outreach_node(state: OrchestratorState) -> dict:
    """Generate outreach drafts.

    Called when intent is "draft_outreach".
    """
    # Need candidates to draft outreach — use ranked candidates from state
    candidates = state.get("ranked_candidates", [])
    if not candidates:
        return {
            "response": "I need candidates to draft outreach for. Could you first ask me to find candidates?",
            "cards": [],
            "actions": [],
            "confidence": 0.2,
            "sources": [],
        }

    drafts = await outreach_agent.generate_outreach(
        candidates=candidates,
        job_context={},  # TODO: Load job context
        recruiter_id=state["recruiter_id"],
    )

    cards = []
    for i, draft in enumerate(drafts):
        cards.append({
            "type": "outreach",
            "data": {
                "candidate_id": draft.get("candidate_id", ""),
                "subject": draft.get("subject", ""),
                "body": draft.get("body", ""),
                "cta": draft.get("cta", ""),
            },
        })

    return {
        "outreach_drafts": drafts,
        "cards": cards,
        "actions": [
            {"id": f"edit_{i}", "label": "Edit", "type": "edit_preference", "payload": {"draft_index": i}},
            {"id": f"approve_{i}", "label": "Approve", "type": "approve", "payload": {"draft_index": i}},
        ],
        "confidence": 0.5,
        "sources": [{"type": "internal_db", "identifier": "candidates", "timestamp": ""}],
    }


async def general_conversation_node(state: OrchestratorState) -> dict:
    """Handle general conversation.

    Called when intent doesn't match any specific category.
    Provides a helpful response and suggests relevant actions.
    """
    return {
        "response": (
            "I can help you source candidates, check pipeline status, "
            "update your preferences, or draft outreach messages. "
            "What would you like to do?"
        ),
        "cards": [],
        "actions": [
            {"id": "source", "label": "Find Candidates", "type": "approve", "payload": {"action": "source"}},
            {"id": "pipeline", "label": "Check Pipeline", "type": "approve", "payload": {"action": "pipeline"}},
            {"id": "preferences", "label": "Update Preferences", "type": "edit_preference", "payload": {"action": "preferences"}},
        ],
        "confidence": 0.6,
        "sources": [],
    }


async def synthesize_response_node(state: OrchestratorState) -> dict:
    """Synthesize the final response.

    Combines specialist outputs into a natural language response
    with structured cards and action buttons.

    In production, this node will use an LLM to generate a coherent
    response. For MVP, it uses a simple template.
    """
    intent = state.get("intent", "general_conversation")
    cards = state.get("cards", [])
    actions = state.get("actions", [])
    confidence = state.get("confidence", 0.5)

    # Build response based on intent
    responses = {
        "source_candidates": (
            f"I found {len(cards)} strong candidate matches. "
            f"Review the cards below and approve or submit as needed."
        ),
        "check_pipeline": state.get("response", "Pipeline check completed."),
        "update_preferences": state.get("response", "Preferences updated."),
        "draft_outreach": (
            f"I've drafted {len(cards)} outreach messages. "
            f"Review and approve the ones you'd like to send."
        ),
        "general_conversation": state.get("response", "How can I help you?"),
    }

    response = responses.get(intent, state.get("response", "I'm here to help."))

    return {
        "response": response,
        "cards": cards,
        "actions": actions,
        "confidence": confidence,
    }


# --- Graph construction ---


def build_graph() -> StateGraph:
    """Build and compile the Orchestrator StateGraph.

    Graph structure:
        START → classify_intent → route_by_intent → {specialist} → synthesize_response → END

    Conditional routing after classify_intent:
        - source_candidates → source_candidates_node
        - check_pipeline → check_pipeline_node
        - update_preferences → update_preferences_node
        - draft_outreach → draft_outreach_node
        - general_conversation → general_conversation_node
    """
    graph = StateGraph(OrchestratorState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("source_candidates", source_candidates_node)
    graph.add_node("check_pipeline", check_pipeline_node)
    graph.add_node("update_preferences", update_preferences_node)
    graph.add_node("draft_outreach", draft_outreach_node)
    graph.add_node("general_conversation", general_conversation_node)
    graph.add_node("synthesize_response", synthesize_response_node)

    # Add edges
    graph.add_edge(START, "classify_intent")

    # Conditional routing based on intent
    graph.add_conditional_edges(
        "classify_intent",
        lambda state: state.get("intent", "general_conversation"),
        {
            "source_candidates": "source_candidates",
            "check_pipeline": "check_pipeline",
            "update_preferences": "update_preferences",
            "draft_outreach": "draft_outreach",
            "general_conversation": "general_conversation",
        },
    )

    # All specialist nodes → synthesis
    graph.add_edge("source_candidates", "synthesize_response")
    graph.add_edge("check_pipeline", "synthesize_response")
    graph.add_edge("update_preferences", "synthesize_response")
    graph.add_edge("draft_outreach", "synthesize_response")
    graph.add_edge("general_conversation", "synthesize_response")

    # Synthesis → END
    graph.add_edge("synthesize_response", END)

    return graph.compile()


# Compiled graph — created once at import time
orchestrator_graph = build_graph()
