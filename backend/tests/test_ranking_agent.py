"""Tests for the RankingAgent.

Tests fit scores, explicit filters, skill match, experience match,
and strengths/gaps computation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.agent_orchestrator.ranking_agent import (
    compute_fit_scores,
    _apply_explicit_filters,
    _compute_skill_match,
    _compute_experience_match,
    _compute_preference_alignment,
    _apply_implicit_weights,
    _identify_strengths,
    _identify_gaps,
)


class TestFitScores:
    """Test overall fit score computation."""

    @pytest.mark.anyio
    async def test_compute_fit_scores_basic(self) -> None:
        mock_db = AsyncMock()
        mock_prefs = MagicMock()
        mock_prefs.explicit_preferences = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)

        candidates = [
            {
                "id": "c1",
                "first_name": "Alex",
                "last_name": "Johnson",
                "current_title": "Senior Java Developer",
                "skills": ["Java", "Spring", "AWS"],
                "notice_period_days": 14,
            },
        ]

        result = await compute_fit_scores(
            db=mock_db,
            candidates=candidates,
            recruiter_id="recruiter-1",
        )

        assert len(result) == 1
        assert "fit_score" in result[0]
        assert "strengths" in result[0]
        assert "gaps" in result[0]

    @pytest.mark.anyio
    async def test_empty_candidates(self) -> None:
        from unittest.mock import AsyncMock
        mock_db = MagicMock()
        mock_prefs = MagicMock()
        mock_prefs.explicit_preferences = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_prefs
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        result = await compute_fit_scores(
            db=mock_db,
            candidates=[],
            recruiter_id="recruiter-1",
        )
        assert result == []


class TestSkillMatch:
    """Test skill matching logic."""

    def test_perfect_skill_match(self) -> None:
        candidate = {"skills": ["Java", "Spring", "AWS"]}
        job_reqs = {"required_skills": ["Java", "Spring", "AWS"]}
        score = _compute_skill_match(candidate, job_reqs)
        assert score == 1.0

    def test_partial_skill_match(self) -> None:
        candidate = {"skills": ["Java", "Spring", "AWS"]}
        job_reqs = {"required_skills": ["Java", "Python", "AWS"]}
        score = _compute_skill_match(candidate, job_reqs)
        # 2/3 = 0.67
        assert 0.6 <= score <= 0.7

    def test_no_skill_match(self) -> None:
        candidate = {"skills": ["Ruby", "Rails"]}
        job_reqs = {"required_skills": ["Java", "Python"]}
        score = _compute_skill_match(candidate, job_reqs)
        assert score == 0.0

    def test_no_requirements(self) -> None:
        candidate = {"skills": ["Java", "Spring"]}
        job_reqs = {}
        score = _compute_skill_match(candidate, job_reqs)
        assert score == 0.5  # No requirements = neutral

    def test_empty_candidate(self) -> None:
        candidate = {"skills": []}
        job_reqs = {"required_skills": ["Java"]}
        score = _compute_skill_match(candidate, job_reqs)
        assert score == 0.0


class TestExperienceMatch:
    """Test experience matching logic."""

    def test_experience_exceeds(self) -> None:
        candidate = {"current_title": "Senior Java Developer"}
        job_reqs = {"experience_required": 5}
        score = _compute_experience_match(candidate, job_reqs)
        # Senior = 7 years >= 5
        assert score == 1.0

    def test_experience_below(self) -> None:
        candidate = {"current_title": "Junior Developer"}
        job_reqs = {"experience_required": 5}
        score = _compute_experience_match(candidate, job_reqs)
        # Junior = 2 years, diff = 3, score = max(0, 1 - 1.5) = 0
        assert score == 0.0

    def test_no_requirement(self) -> None:
        candidate = {"current_title": "Developer"}
        job_reqs = {}
        score = _compute_experience_match(candidate, job_reqs)
        assert score == 0.5


class TestPreferenceAlignment:
    """Test preference alignment scoring."""

    def test_no_preferences(self) -> None:
        candidate = {"skills": ["Java"]}
        score = _compute_preference_alignment(candidate, {}, {})
        assert score == 0.5

    def test_cloud_preference_match(self) -> None:
        candidate = {"skills": ["AWS", "Docker"]}
        explicit = {}
        implicit = {"cloud_experience": 0.8}
        score = _compute_preference_alignment(candidate, explicit, implicit)
        assert score > 0.5

    def test_no_cloud_preference_match(self) -> None:
        candidate = {"skills": ["Ruby", "Rails"]}
        explicit = {}
        implicit = {"cloud_experience": 0.8}
        score = _compute_preference_alignment(candidate, explicit, implicit)
        assert score <= 0.5


class TestImplicitWeights:
    """Test implicit weight application."""

    def test_default_weights(self) -> None:
        weights = _apply_implicit_weights(
            {"skill_match": 0.4, "experience_match": 0.25, "preference_alignment": 0.35},
            {},
        )
        assert weights["skill_match"] == 0.4

    def test_cloud_boost(self) -> None:
        weights = _apply_implicit_weights(
            {"skill_match": 0.4, "experience_match": 0.25, "preference_alignment": 0.35},
            {"cloud_experience": 0.8},
        )
        assert weights["skill_match"] > 0.4
        assert weights["preference_alignment"] < 0.35


class TestStrengthsGaps:
    """Test strengths and gaps computation."""

    def test_strengths_from_experience(self) -> None:
        candidate = {"current_title": "Principal Engineer", "skills": ["Java"]}
        job_reqs = {"experience_required": 5, "required_skills": ["Java"]}
        strengths = _identify_strengths(candidate, job_reqs)
        assert len(strengths) > 0

    def test_gaps_from_missing_skills(self) -> None:
        candidate = {"current_title": "Developer", "skills": ["Java"]}
        job_reqs = {"experience_required": 5, "required_skills": ["Java", "AWS", "K8s"]}
        gaps = _identify_gaps(candidate, job_reqs)
        assert len(gaps) > 0
        assert any("AWS" in g for g in gaps)

    def test_perfect_match(self) -> None:
        candidate = {"current_title": "Senior Developer", "skills": ["Java", "AWS"]}
        job_reqs = {"experience_required": 5, "required_skills": ["Java", "AWS"]}
        gaps = _identify_gaps(candidate, job_reqs)
        # Senior = 7 years >= 5, has all skills
        assert len(gaps) == 0


class TestExplicitFilters:
    """Test explicit filter application."""

    def test_visa_filter(self) -> None:
        candidate = {"visa_status": "H1B"}
        preferences = {"required_visa_status": "US_Citizen"}
        assert _apply_explicit_filters(candidate, preferences) is True

    def test_notice_period_filter(self) -> None:
        candidate = {"notice_period_days": 60}
        preferences = {"max_notice_period_days": 30}
        assert _apply_explicit_filters(candidate, preferences) is True

    def test_required_skills_filter(self) -> None:
        candidate = {"skills": ["Java"]}
        preferences = {"required_skills": ["Java", "AWS"]}
        assert _apply_explicit_filters(candidate, preferences) is True

    def test_no_filter_applied(self) -> None:
        candidate = {"skills": ["Java", "AWS"], "notice_period_days": 14}
        preferences = {}
        assert _apply_explicit_filters(candidate, preferences) is False
