"""Tests for the Orchestrator intent classifier.

Tests rule-based classification, LLM classification, fallback,
and prompt generation.
"""

import pytest

from app.services.agent_orchestrator.intent_classifier import (
    INTENT_SOURCE_CANDIDATES,
    INTENT_CHECK_PIPELINE,
    INTENT_UPDATE_PREFERENCES,
    INTENT_SCHEDULE_INTERVIEW,
    INTENT_DRAFT_OUTREACH,
    INTENT_GENERAL_CONVERSATION,
    classify_intent_rule_based,
    classify_intent_llm,
    classify_intent,
    build_intent_prompt,
    INTENTS,
)
from app.services.agent_orchestrator.llm_provider import MockLLMProvider


class TestRuleBasedClassification:
    """Test rule-based keyword matching classification."""

    @pytest.mark.parametrize(
        "message,intent",
        [
            ("Find me a Java developer", INTENT_SOURCE_CANDIDATES),
            ("Search for Python candidates", INTENT_SOURCE_CANDIDATES),
            ("Who has React experience?", INTENT_SOURCE_CANDIDATES),
            ("Show me qualified engineers", INTENT_SOURCE_CANDIDATES),
            ("Check pipeline status", INTENT_CHECK_PIPELINE),
            ("Where are my submitted candidates?", INTENT_CHECK_PIPELINE),
            ("What's happening with the pipeline?", INTENT_CHECK_PIPELINE),
            ("Remember I prefer remote workers", INTENT_UPDATE_PREFERENCES),
            ("Always filter out contract roles", INTENT_UPDATE_PREFERENCES),
            ("Schedule an interview with Alex", INTENT_SCHEDULE_INTERVIEW),
            ("Book a meeting for tomorrow", INTENT_SCHEDULE_INTERVIEW),
            ("Draft outreach to Maria", INTENT_DRAFT_OUTREACH),
            ("Write an email to the candidates", INTENT_DRAFT_OUTREACH),
            ("Reach out to the top matches", INTENT_DRAFT_OUTREACH),
            ("Source top candidates for Senior Java Backend Engineer requiring Java, Spring Boot, AWS", INTENT_SOURCE_CANDIDATES),
            ("Active Session: New Conversation\n\nSource top candidates for Senior Java Backend Engineer requiring Java, Spring Boot, AWS", INTENT_SOURCE_CANDIDATES),
            ("Hello, how are you?", INTENT_GENERAL_CONVERSATION),
            ("What can you do?", INTENT_GENERAL_CONVERSATION),
        ],
    )
    def test_rule_based_classification(self, message: str, intent: str) -> None:
        assert classify_intent_rule_based(message) == intent

    def test_case_insensitive(self) -> None:
        assert classify_intent_rule_based("FIND ME JAVA DEVELOPERS") == INTENT_SOURCE_CANDIDATES
        assert classify_intent_rule_based("find me java developers") == INTENT_SOURCE_CANDIDATES

    def test_no_match_returns_general(self) -> None:
        assert classify_intent_rule_based("The weather is nice today") == INTENT_GENERAL_CONVERSATION


class TestLLMClassification:
    """Test LLM-based classification with MockLLMProvider."""

    @pytest.mark.anyio
    async def test_llm_classifies_source_candidates(self) -> None:
        provider = MockLLMProvider({"find": INTENT_SOURCE_CANDIDATES})
        # Temporarily replace the factory
        import app.services.agent_orchestrator.intent_classifier as ic
        original_factory = ic.get_llm_provider

        try:
            ic.get_llm_provider = lambda use_mock=False: provider
            result = await classify_intent_llm("Find me Java developers")
            assert result == INTENT_SOURCE_CANDIDATES
        finally:
            ic.get_llm_provider = original_factory

    @pytest.mark.anyio
    async def test_llm_unknown_intent_defaults_to_general(self) -> None:
        provider = MockLLMProvider({"foo": "unknown_intent"})
        import app.services.agent_orchestrator.intent_classifier as ic
        original_factory = ic.get_llm_provider

        try:
            ic.get_llm_provider = lambda use_mock=False: provider
            result = await classify_intent_llm("foo bar baz")
            assert result == INTENT_GENERAL_CONVERSATION
        finally:
            ic.get_llm_provider = original_factory

    @pytest.mark.anyio
    async def test_llm_classifies_pipeline(self) -> None:
        provider = MockLLMProvider({"pipeline": INTENT_CHECK_PIPELINE})
        import app.services.agent_orchestrator.intent_classifier as ic
        original_factory = ic.get_llm_provider

        try:
            ic.get_llm_provider = lambda use_mock=False: provider
            result = await classify_intent_llm("Check pipeline status")
            assert result == INTENT_CHECK_PIPELINE
        finally:
            ic.get_llm_provider = original_factory


class TestFallback:
    """Test LLM → rule-based fallback."""

    @pytest.mark.anyio
    async def test_fallback_to_rule_based_on_exception(self) -> None:
        import app.services.agent_orchestrator.intent_classifier as ic
        original_factory = ic.get_llm_provider

        def raise_error(*args, **kwargs):
            raise RuntimeError("LLM down")

        try:
            ic.get_llm_provider = raise_error
            result = await classify_intent("Find me Java developers")
            assert result == INTENT_SOURCE_CANDIDATES
        finally:
            ic.get_llm_provider = original_factory


class TestBuildIntentPrompt:
    """Test prompt generation for each intent."""

    def test_source_candidates_prompt(self) -> None:
        prompt = build_intent_prompt(INTENT_SOURCE_CANDIDATES, "Find Java devs", "job-123")
        assert "source_candidates" in prompt
        assert "Find Java devs" in prompt
        assert "job-123" in prompt
        assert "Search the candidate database" in prompt

    def test_general_conversation_prompt(self) -> None:
        prompt = build_intent_prompt(INTENT_GENERAL_CONVERSATION, "Hello")
        assert "general_conversation" in prompt
        assert "Hello" in prompt

    def test_unknown_intent_returns_general(self) -> None:
        prompt = build_intent_prompt("unknown_intent", "test")
        assert "general_conversation" in prompt

    def test_no_job_id(self) -> None:
        prompt = build_intent_prompt(INTENT_SOURCE_CANDIDATES, "Find Java devs", None)
        assert "Job context:" not in prompt
