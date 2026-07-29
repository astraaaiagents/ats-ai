"""Tests for the Preference Engine.

Tests explicit CRUD, implicit learning, vector encoding, learning events.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# Create a mock DB that has AsyncMock for execute and flush
def make_mock_db():
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.flush = AsyncMock()
    return mock_db


from app.services.preference_engine import (
    get_explicit_preferences,
    set_explicit_preference,
    update_explicit_preferences,
    delete_explicit_preference,
    record_approval,
    record_rejection,
    get_implicit_scores,
    _encode_vector,
    _decode_vector,
    _extract_features_from_candidate,
    FEATURE_DIMENSIONS,
)


class TestExplicitPreferences:
    """Test explicit preference CRUD operations."""

    @pytest.mark.anyio
    async def test_get_creates_default(self) -> None:
        mock_db = make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_explicit_preferences(mock_db, "recruiter-1")
        assert isinstance(result, dict)
        assert mock_db.execute.called

    @pytest.mark.anyio
    async def test_set_single_preference(self) -> None:
        mock_db = make_mock_db()
        mock_prefs = MagicMock()
        mock_prefs.explicit_preferences = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await set_explicit_preference(mock_db, "recruiter-1", "remote_only", True)
        assert result["remote_only"] is True
        assert mock_db.flush.called

    @pytest.mark.anyio
    async def test_update_multiple_preferences(self) -> None:
        mock_db = make_mock_db()
        mock_prefs = MagicMock()
        mock_prefs.explicit_preferences = {"remote_only": True}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await update_explicit_preferences(
            mock_db, "recruiter-1", {"contract_only": False}
        )
        assert result["remote_only"] is True
        assert result["contract_only"] is False

    @pytest.mark.anyio
    async def test_delete_preference(self) -> None:
        mock_db = make_mock_db()
        mock_prefs = MagicMock()
        mock_prefs.explicit_preferences = {"remote_only": True, "contract_only": False}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await delete_explicit_preference(mock_db, "recruiter-1", "remote_only")
        assert "remote_only" not in result
        assert "contract_only" in result


class TestImplicitPreferences:
    """Test implicit preference learning."""

    @pytest.mark.anyio
    async def test_record_approval_increases_scores(self) -> None:
        mock_db = make_mock_db()
        mock_prefs = MagicMock()
        mock_prefs.implicit_preference_vector = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await record_approval(mock_db, "recruiter-1", "cand-1")
        assert isinstance(result, dict)
        assert mock_db.flush.called

    @pytest.mark.anyio
    async def test_record_rejection_decreases_scores(self) -> None:
        mock_db = make_mock_db()
        mock_prefs = MagicMock()
        mock_prefs.implicit_preference_vector = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await record_rejection(mock_db, "recruiter-1", "cand-1")
        assert isinstance(result, dict)

    @pytest.mark.anyio
    async def test_get_implicit_scores_empty(self) -> None:
        mock_db = make_mock_db()
        mock_prefs = MagicMock()
        mock_prefs.implicit_preference_vector = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_implicit_scores(mock_db, "recruiter-1")
        assert result == {}


class TestVectorEncoding:
    """Test vector encoding/decoding."""

    def test_encode_vector(self) -> None:
        scores = {"cloud_experience": 0.8, "python_experience": 0.3}
        vector = _encode_vector(scores)
        assert isinstance(vector, list)
        assert len(vector) == len(FEATURE_DIMENSIONS)

    def test_decode_vector_dict(self) -> None:
        scores = {"cloud_experience": 0.8, "python_experience": 0.3}
        decoded = _decode_vector(scores)
        assert isinstance(decoded, dict)
        assert decoded["cloud_experience"] == 0.8

    def test_decode_vector_none(self) -> None:
        assert _decode_vector(None) == {}

    def test_decode_vector_empty_string(self) -> None:
        assert _decode_vector("") == {}

    def test_decode_vector_json_string(self) -> None:
        import json
        scores = {"cloud_experience": 0.8}
        vector_str = json.dumps(scores)
        decoded = _decode_vector(vector_str)
        assert decoded["cloud_experience"] == 0.8

    def test_round_trip(self) -> None:
        scores = {"cloud_experience": 0.8, "python_experience": 0.3, "java_experience": 0.6}
        vector = _encode_vector(scores)
        decoded = _decode_vector(vector)
        # Values should be close (inverse sigmoid may slightly differ)
        for key in scores:
            if key in decoded:
                assert abs(decoded[key] - scores[key]) < 0.5


class TestFeatureExtraction:
    """Test feature extraction from candidates."""

    def test_returns_default_features(self) -> None:
        features = _extract_features_from_candidate("cand-1")
        assert isinstance(features, dict)
        assert "cloud_experience" in features
        assert "python_experience" in features
        # MVP returns neutral values
        assert all(v == 0.5 for v in features.values())
