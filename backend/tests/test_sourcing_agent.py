"""Tests for the SourcingAgent.

Tests structured search, FTS search, vector search, RRF fusion,
and keyword extraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.services.agent_orchestrator.sourcing_agent import (
    search_candidates,
    _structured_search,
    _fts_search,
    _vector_search,
    _rrf_fusion,
    _extract_keywords,
    get_job_details,
    RRF_CONSTANT,
)


class TestKeywordExtraction:
    """Test keyword extraction from natural language queries."""

    def test_extracts_meaningful_words(self) -> None:
        keywords = _extract_keywords("Find me a Java developer with AWS experience")
        assert "java" in keywords
        assert "developer" in keywords
        assert "aws" in keywords

    def test_filters_stop_words(self) -> None:
        keywords = _extract_keywords("Find me the Java developer")
        assert "find" not in keywords
        assert "me" not in keywords
        assert "the" not in keywords
        assert "java" in keywords

    def test_filters_short_words(self) -> None:
        keywords = _extract_keywords("Java a dev")
        assert "a" not in keywords  # 1 char, filtered

    def test_deduplicates(self) -> None:
        keywords = _extract_keywords("Java Java Java")
        assert keywords.count("java") == 1

    def test_empty_query(self) -> None:
        assert _extract_keywords("") == []

    def test_preserves_order(self) -> None:
        keywords = _extract_keywords("Python Java Golang Rust")
        assert keywords.index("python") < keywords.index("java")
        assert keywords.index("java") < keywords.index("golang")


class TestRRFFusion:
    """Test Reciprocal Rank Fusion combining."""

    def test_combines_single_list(self) -> None:
        items = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}, {"id": "c", "name": "C"}]
        ranked = [(item, 1.0 / (i + 1)) for i, item in enumerate(items)]
        result = _rrf_fusion([ranked])
        assert len(result) == 3
        # First item should have highest score
        assert result[0][0]["id"] == "a"

    def test_combines_multiple_lists(self) -> None:
        list_a = [{"id": "x", "name": "X"}, {"id": "y", "name": "Y"}]
        list_b = [{"id": "x", "name": "X"}, {"id": "z", "name": "Z"}]
        ranked_a = [(item, 1.0 / (i + 1)) for i, item in enumerate(list_a)]
        ranked_b = [(item, 1.0 / (i + 1)) for i, item in enumerate(list_b)]
        result = _rrf_fusion([ranked_a, ranked_b])
        # x appears in both lists, should rank highest
        assert result[0][0]["id"] == "x"

    def test_empty_lists(self) -> None:
        result = _rrf_fusion([])
        assert result == []

    def test_rrf_constant_applied(self) -> None:
        """Verify RRF constant affects ranking."""
        list_a = [{"id": "a", "name": "A"}]
        list_b = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]
        ranked_a = [(item, 1.0) for item in list_a]
        ranked_b = [(item, 1.0 / (i + 1)) for i, item in enumerate(list_b)]
        result = _rrf_fusion([ranked_a, ranked_b])
        # a appears in both lists, should rank higher than b
        assert result[0][0]["id"] == "a"
        assert result[1][0]["id"] == "b"


class TestStructuredSearch:
    """Test structured keyword search."""

    @pytest.mark.anyio
    async def test_returns_empty_for_no_keywords(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await _structured_search(mock_db, "org-1", [], 10)
        assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_executes_sql_query(self) -> None:
        mock_db = AsyncMock()
        mock_id_result = MagicMock()
        mock_id_result.all.return_value = [("cand-1",), ("cand-2",)]
        mock_db.execute = AsyncMock(side_effect=[mock_id_result, MagicMock()])

        # Mock the second execute (full candidate fetch)
        mock_cand_result = MagicMock()
        mock_cand = MagicMock()
        mock_cand.id = "cand-1"
        mock_cand_result.scalars().all.return_value = [mock_cand]
        mock_db.execute.side_effect = [
            mock_id_result,
            mock_cand_result,
        ]

        result = await _structured_search(mock_db, "org-1", ["java"], 10)
        assert mock_db.execute.called


class TestFTSSearch:
    """Test full-text search."""

    @pytest.mark.anyio
    async def test_uses_tsvector(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await _fts_search(mock_db, "org-1", "java developer", 10)
        assert isinstance(result, list)
        assert mock_db.execute.called


class TestVectorSearch:
    """Test vector similarity search."""

    @pytest.mark.anyio
    async def test_fallback_to_ilike(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await _vector_search(mock_db, "org-1", "java", 10)
        assert isinstance(result, list)


class TestGetJobDetails:
    """Test job details retrieval."""

    @pytest.mark.anyio
    async def test_returns_none_for_missing_job(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_job_details(mock_db, "org-1", "nonexistent")
        assert result is None

    @pytest.mark.anyio
    async def test_returns_job_dict_for_found_job(self) -> None:
        mock_db = AsyncMock()
        mock_contact = MagicMock()
        mock_contact.id = "job-1"
        mock_contact.title = "Java Lead"
        mock_contact.organization_name = "TCS"
        mock_contact.location = "SF"
        mock_contact.description = "Java role"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_job_details(mock_db, "org-1", "job-1")
        assert result is not None
        assert result["title"] == "Java Lead"
        assert result["client"] == "TCS"
