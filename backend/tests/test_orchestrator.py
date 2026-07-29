"""Tests for the Orchestrator LangGraph graph and entry point.

Tests graph structure, node execution, run_orchestrator() with mock LLM,
and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.services.agent_orchestrator.graph import (
    build_graph,
    classify_intent_node,
    source_candidates_node,
    check_pipeline_node,
    update_preferences_node,
    draft_outreach_node,
    general_conversation_node,
    synthesize_response_node,
    orchestrator_graph,
)
from app.services.agent_orchestrator.state import OrchestratorState


class TestGraphStructure:
    """Test the LangGraph StateGraph structure."""

    def test_graph_is_compiled(self) -> None:
        assert orchestrator_graph is not None

    def test_graph_has_all_nodes(self) -> None:
        node_names = list(orchestrator_graph.nodes.keys())
        assert "classify_intent" in node_names
        assert "source_candidates" in node_names
        assert "check_pipeline" in node_names
        assert "update_preferences" in node_names
        assert "draft_outreach" in node_names
        assert "general_conversation" in node_names
        assert "synthesize_response" in node_names

    def test_graph_build_reproducible(self) -> None:
        graph = build_graph()
        assert graph is not None
        assert len(graph.nodes) >= 7


class TestClassifyIntentNode:
    """Test the classify_intent_node."""

    @pytest.mark.anyio
    async def test_classify_intent_returns_intent(self) -> None:
        state: OrchestratorState = {
            "message": "Find me Java developers",
            "org_id": "org-1",
            "recruiter_id": "recruiter-1",
        }
        result = await classify_intent_node(state)
        assert "intent" in result
        assert isinstance(result["intent"], str)


class TestSpecialistNodes:
    """Test specialist agent nodes."""

    @pytest.mark.anyio
    async def test_check_pipeline_returns_placeholder(self) -> None:
        state: OrchestratorState = {
            "message": "Check pipeline",
            "org_id": "org-1",
            "recruiter_id": "recruiter-1",
        }
        result = await check_pipeline_node(state)
        assert "response" in result
        assert "not yet implemented" in result["response"].lower()
        assert result["cards"] == []
        assert result["actions"] == []

    @pytest.mark.anyio
    async def test_update_preferences_returns_placeholder(self) -> None:
        state: OrchestratorState = {
            "message": "Remember I prefer remote",
            "org_id": "org-1",
            "recruiter_id": "recruiter-1",
        }
        result = await update_preferences_node(state)
        assert "response" in result
        assert "preference update noted" in result["response"].lower()

    @pytest.mark.anyio
    async def test_draft_outreach_no_candidates(self) -> None:
        state: OrchestratorState = {
            "message": "Draft outreach",
            "org_id": "org-1",
            "recruiter_id": "recruiter-1",
        }
        result = await draft_outreach_node(state)
        assert "need candidates" in result["response"].lower()

    @pytest.mark.anyio
    async def test_general_conversation_returns_suggestions(self) -> None:
        state: OrchestratorState = {
            "message": "Hello",
            "org_id": "org-1",
            "recruiter_id": "recruiter-1",
        }
        result = await general_conversation_node(state)
        assert "source candidates" in result["response"].lower()
        assert len(result["actions"]) > 0

    @pytest.mark.anyio
    async def test_draft_outreach_with_candidates(self) -> None:
        state: OrchestratorState = {
            "message": "Draft outreach",
            "org_id": "org-1",
            "recruiter_id": "recruiter-1",
            "ranked_candidates": [
                {"id": "c1", "first_name": "Alex", "skills": ["Java"]},
            ],
        }
        result = await draft_outreach_node(state)
        assert "outreach_drafts" in result
        assert len(result["cards"]) > 0


class TestSynthesizeResponseNode:
    """Test the response synthesis node."""

    @pytest.mark.anyio
    async def test_synthesize_source_candidates(self) -> None:
        state: OrchestratorState = {
            "intent": "source_candidates",
            "cards": [{"type": "candidate"}],
            "actions": [],
            "confidence": 0.8,
        }
        result = await synthesize_response_node(state)
        assert "3 strong candidate matches" not in result["response"]  # 1 card, not 3
        assert "1 strong candidate matches" in result["response"]

    @pytest.mark.anyio
    async def test_synthesize_general_conversation(self) -> None:
        state: OrchestratorState = {
            "intent": "general_conversation",
            "response": "How can I help?",
            "cards": [],
            "actions": [],
            "confidence": 0.6,
        }
        result = await synthesize_response_node(state)
        assert result["response"] == "How can I help?"

    @pytest.mark.anyio
    async def test_synthesize_draft_outreach(self) -> None:
        state: OrchestratorState = {
            "intent": "draft_outreach",
            "cards": [{"type": "outreach"}, {"type": "outreach"}],
            "actions": [],
            "confidence": 0.5,
        }
        result = await synthesize_response_node(state)
        assert "2 outreach messages" in result["response"]


class TestRunOrchestrator:
    """Test the run_orchestrator entry point."""

    @pytest.mark.anyio
    async def test_run_orchestrator_returns_dict(self) -> None:
        from app.services.agent_orchestrator import run_orchestrator

        mock_db = MagicMock()

        result = await run_orchestrator(
            message="Find Java developers",
            db=mock_db,
            org_id="org-1",
            recruiter_id="recruiter-1",
            session_id="session-1",
            job_id=None,
            preferences={},
        )

        assert isinstance(result, dict)
        assert "response" in result
        assert "cards" in result
        assert "actions" in result
        assert "confidence" in result
        assert "intent" in result
