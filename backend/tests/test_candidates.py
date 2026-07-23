"""Integration tests for Candidate management endpoints.

Tests cover:
- Candidate CRUD (create, read, update, archive)
- Status state machine transitions
- Skill management (add, remove)
- Duplicate detection
- Timeline events
- Role-based access control
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.database import get_session
from app.main import create_app


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_user_token(org_id: str, role: str = "recruiter", user_id: uuid.UUID | None = None) -> str:
    sub = str(user_id) if user_id else str(uuid.uuid4())
    return create_access_token({
        "sub": sub,
        "org_id": org_id,
        "role": role,
        "token_version": 0,
    })


def _make_current_user(role: str, org_id: str | None = None) -> Mock:
    user = Mock()
    user.id = uuid.uuid4()
    user.email = f"{role}@example.com"
    user.role = role
    user.organization_id = uuid.UUID(org_id) if org_id else None
    user.is_active = True
    user.token_version = 0
    return user


def _make_mock_candidate(candidate_uuid: uuid.UUID, status: str = "sourced", **kwargs) -> Mock:
    """Create a mock candidate with all fields set to valid values for Pydantic validation."""
    c = Mock()
    c.id = candidate_uuid
    c.first_name = kwargs.get("first_name", "John")
    c.last_name = kwargs.get("last_name", "Doe")
    c.email = kwargs.get("email", "john@example.com")
    c.phone = kwargs.get("phone", None)
    c.current_title = kwargs.get("current_title", None)
    c.current_employer = kwargs.get("current_employer", None)
    c.location = kwargs.get("location", None)
    c.salary_expectation_min = kwargs.get("salary_expectation_min", None)
    c.salary_expectation_max = kwargs.get("salary_expectation_max", None)
    c.visa_status = kwargs.get("visa_status", None)
    c.notice_period_days = kwargs.get("notice_period_days", None)
    c.source = kwargs.get("source", None)
    c.status = status
    c.owner_id = None
    c.ai_summary = None
    c.ai_summary_generated_at = None
    c.is_ai_summary_edited = False
    c.skills = kwargs.get("skills", [])
    c.documents = kwargs.get("documents", [])
    c.timeline = kwargs.get("timeline", [])
    c.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    c.updated_at = datetime(2025, 1, 1, tzinfo=UTC)
    return c


def _make_session_with_user(user: Mock, extra_executes: list | None = None):
    """Create a session override that returns a mock user for get_current_user,
    plus optional extra execute results for route logic."""
    mock_blacklist_result = Mock()
    mock_blacklist_result.scalar_one_or_none.return_value = None

    mock_user_result = Mock()
    mock_user_result.scalar_one_or_none.return_value = user

    executes = [mock_blacklist_result, mock_user_result]
    if extra_executes:
        executes.extend(extra_executes)

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=executes)
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


# ── Candidate CRUD ───────────────────────────────────────────────────────────


class TestCandidateEndpoints:
    """POST, GET, PUT, DELETE /candidates"""

    @pytest.mark.anyio
    async def test_create_candidate_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_dup_result = Mock()
        mock_dup_result.scalar_one_or_none.return_value = None
        mock_dup_result.scalars.return_value.all.return_value = []

        mock_session = _make_session_with_user(current_user, [mock_dup_result])

        async def refresh_side_effect(obj):
            obj.id = candidate_uuid
            obj.first_name = "John"
            obj.last_name = "Doe"
            obj.email = "john@example.com"
            obj.status = "sourced"
            obj.created_at = datetime(2025, 1, 1, tzinfo=UTC)
            obj.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/candidates",
                json={
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "current_title": "Software Engineer",
                    "skills": [{"skill_name": "Python", "proficiency": 5}],
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["first_name"] == "John"
        assert body["last_name"] == "Doe"
        assert body["status"] == "sourced"

    @pytest.mark.anyio
    async def test_create_candidate_duplicate_email_returns_409(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        existing = Mock()
        existing.id = uuid.uuid4()
        existing.first_name = "Jane"
        existing.last_name = "Smith"

        mock_dup_result = Mock()
        mock_dup_result.scalar_one_or_none.return_value = existing
        mock_dup_result.scalars.return_value.all.return_value = [existing]

        mock_session = _make_session_with_user(current_user, [mock_dup_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/candidates",
                json={
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "jane@example.com",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "DUPLICATE_CANDIDATE"

    @pytest.mark.anyio
    async def test_get_candidate_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/candidates/{candidate_uuid}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["first_name"] == "John"
        assert body["email"] == "john@example.com"

    @pytest.mark.anyio
    async def test_get_candidate_not_found_returns_404(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/candidates/{uuid.uuid4()}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_update_candidate_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.current_title = "Senior Engineer"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/candidates/{candidate_uuid}",
                json={"current_title": "Senior Engineer"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["current_title"] == "Senior Engineer"

    @pytest.mark.anyio
    async def test_archive_candidate(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.status = "archived"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/candidates/{candidate_uuid}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "archived"

    @pytest.mark.anyio
    async def test_create_candidate_requires_auth(self):
        app = create_app()
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/candidates",
                json={"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
            )

        assert response.status_code == 401


# ── Status State Machine ─────────────────────────────────────────────────────


class TestCandidateStatusTransitions:
    """PATCH /candidates/:id/status"""

    @pytest.mark.anyio
    async def test_transition_sourced_to_in_review_recruiter(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid, status="sourced")
        mock_candidate.organization_id = uuid.UUID(org_id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.status = "in_review"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/candidates/{candidate_uuid}/status",
                json={"status": "in_review"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "in_review"

    @pytest.mark.anyio
    async def test_transition_sourced_to_submitted_denied_recruiter(self):
        """Recruiter cannot skip directly to submitted."""
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid, status="sourced")
        mock_candidate.organization_id = uuid.UUID(org_id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/candidates/{candidate_uuid}/status",
                json={"status": "submitted"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_TRANSITION"

    @pytest.mark.anyio
    async def test_transition_terminal_state_denied(self):
        """Placed/rejected/archived candidates cannot transition."""
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid, status="placed")
        mock_candidate.organization_id = uuid.UUID(org_id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/candidates/{candidate_uuid}/status",
                json={"status": "rejected"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_TRANSITION"

    @pytest.mark.anyio
    async def test_any_role_can_reject(self):
        """Any role can reject a candidate."""
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid, status="in_review")
        mock_candidate.organization_id = uuid.UUID(org_id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_candidate

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.status = "rejected"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/candidates/{candidate_uuid}/status",
                json={"status": "rejected"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"


# ── Skill Management ─────────────────────────────────────────────────────────


class TestCandidateSkills:
    """POST, DELETE /candidates/:id/skills"""

    @pytest.mark.anyio
    async def test_add_skill_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()
        skill_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid)

        mock_candidate_result = Mock()
        mock_candidate_result.scalar_one_or_none.return_value = mock_candidate

        mock_skill_result = Mock()
        mock_skill_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_candidate_result, mock_skill_result])

        async def refresh_side_effect(obj):
            obj.id = skill_uuid
            obj.skill_name = "Python"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/candidates/{candidate_uuid}/skills",
                json={"skill_name": "Python", "proficiency": 5},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["skill_name"] == "Python"

    @pytest.mark.anyio
    async def test_add_duplicate_skill_returns_409(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid)

        mock_candidate_result = Mock()
        mock_candidate_result.scalar_one_or_none.return_value = mock_candidate

        existing_skill = Mock()
        existing_skill.id = uuid.uuid4()
        mock_skill_result = Mock()
        mock_skill_result.scalar_one_or_none.return_value = existing_skill

        mock_session = _make_session_with_user(current_user, [mock_candidate_result, mock_skill_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/candidates/{candidate_uuid}/skills",
                json={"skill_name": "Python"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "DUPLICATE_SKILL"


# ── Dedup Check ──────────────────────────────────────────────────────────────


class TestDedupCheck:
    """POST /candidates/dedup-check"""

    @pytest.mark.anyio
    async def test_dedup_check_no_duplicates(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/candidates/dedup-check",
                json={"email": "new@example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["is_duplicate"] is False

    @pytest.mark.anyio
    async def test_dedup_check_with_duplicates(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        dup_candidate = Mock()
        dup_candidate.id = uuid.uuid4()
        dup_candidate.first_name = "Jane"
        dup_candidate.last_name = "Smith"
        dup_candidate.email = "jane@example.com"
        dup_candidate.status = "in_review"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [dup_candidate]

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/candidates/dedup-check",
                json={"email": "jane@example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["is_duplicate"] is True
        assert len(body["candidates"]) == 1
        assert body["candidates"][0]["match_reason"] == "email_exact"


# ── Timeline ─────────────────────────────────────────────────────────────────


class TestCandidateTimeline:
    """GET /candidates/:id/timeline"""

    @pytest.mark.anyio
    async def test_get_timeline_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_candidate = _make_mock_candidate(candidate_uuid)

        mock_candidate_result = Mock()
        mock_candidate_result.scalar_one_or_none.return_value = mock_candidate

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        mock_event = Mock()
        mock_event.id = uuid.uuid4()
        mock_event.event_type = "status_changed"
        mock_event.description = "Status changed from sourced to in_review"
        mock_event.details = {"from_status": "sourced", "to_status": "in_review"}
        mock_event.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        # Ensure details is a real dict (not a Mock)
        mock_event.details = {"from_status": "sourced", "to_status": "in_review"}

        mock_events_result = Mock()
        mock_events_result.scalars.return_value.all.return_value = [mock_event]

        mock_session = _make_session_with_user(current_user, [
            mock_candidate_result, mock_count_result, mock_events_result
        ])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/candidates/{candidate_uuid}/timeline",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["pagination"]["total"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0]["event_type"] == "status_changed"
