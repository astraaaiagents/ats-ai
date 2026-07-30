import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.database import get_session
from app.main import create_app


def _make_user_token(org_id: str, role: str = "admin", user_id: uuid.UUID | None = None) -> str:
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


def _make_session_with_user(user: Mock, extra_executes: list | None = None):
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
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


class TestNewFeatures:

    @pytest.mark.anyio
    async def test_create_candidate_flow(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        candidate_uuid = uuid.uuid4()

        mock_dup_result = Mock()
        mock_dup_result.scalar_one_or_none.return_value = None
        mock_dup_result.scalars.return_value.all.return_value = []

        mock_session = _make_session_with_user(current_user, [mock_dup_result])

        async def refresh_side_effect(obj):
            obj.id = candidate_uuid
            obj.first_name = "Showcase"
            obj.last_name = "Candidate"
            obj.email = "showcase@example.com"
            obj.status = "sourced"
            obj.created_at = datetime(2026, 1, 1, tzinfo=UTC)
            obj.updated_at = datetime(2026, 1, 1, tzinfo=UTC)

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/candidates",
                json={
                    "first_name": "Showcase",
                    "last_name": "Candidate",
                    "email": "showcase@example.com",
                    "current_title": "Lead AI Engineer",
                    "status": "sourced",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["first_name"] == "Showcase"
        assert body["status"] == "sourced"

    @pytest.mark.anyio
    async def test_create_client_contact_flow(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        contact_uuid = uuid.uuid4()

        mock_dup_result = Mock()
        mock_dup_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_dup_result])

        async def refresh_side_effect(obj):
            obj.id = contact_uuid
            obj.email = "hiring@acme.ai"
            obj.first_name = "Hiring"
            obj.last_name = "Manager"
            obj.organization_name = "Acme AI Corp"
            obj.title = "Staff Machine Learning Engineer"
            obj.location = "San Francisco, CA"
            obj.phone = None
            obj.description = None
            obj.status = "healthy"
            obj.is_active = True
            obj.created_at = datetime(2026, 1, 1, tzinfo=UTC)
            obj.updated_at = datetime(2026, 1, 1, tzinfo=UTC)

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/client-contacts",
                json={
                    "organization_name": "Acme AI Corp",
                    "title": "Staff Machine Learning Engineer",
                    "email": "hiring@acme.ai",
                    "first_name": "Hiring",
                    "last_name": "Manager",
                    "location": "San Francisco, CA",
                    "status": "healthy",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["organization_name"] == "Acme AI Corp"
        assert body["title"] == "Staff Machine Learning Engineer"
