"""Integration tests for Organization, User, and Client Contact management endpoints.

Tests cover:
- Organization CRUD (SuperAdmin only)
- User management with invite flow (Admin/Manager only)
- Client contacts CRUD (Admin/Manager only)
- Role-based access control enforcement
- Tenant isolation
- Invitation expiration, token revocation edge cases
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient
from freezegun import freeze_time

from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.password import hash_password
from app.database import get_session
from app.main import create_app


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_org_token(org_id: str, role: str = "super_admin", user_id: uuid.UUID | None = None) -> str:
    """Create a super_admin token for a given org (org_id=None for platform admin).

    If user_id is provided, the token's sub claim matches it so get_current_user
    can find the user in the mock session.
    """
    sub = str(user_id) if user_id else str(uuid.uuid4())
    return create_access_token({
        "sub": sub,
        "org_id": None if role == "super_admin" else org_id,
        "role": role,
        "token_version": 0,
    })


def _make_user_token(org_id: str, role: str = "admin", user_id: uuid.UUID | None = None) -> str:
    """Create an org user token.

    If user_id is provided, the token's sub claim matches it so get_current_user
    can find the user in the mock session.
    """
    sub = str(user_id) if user_id else str(uuid.uuid4())
    return create_access_token({
        "sub": sub,
        "org_id": org_id,
        "role": role,
        "token_version": 0,
    })


def _make_current_user(role: str, org_id: str | None = None) -> Mock:
    """Create a mock current user for auth dependency."""
    user = Mock()
    user.id = uuid.uuid4()
    user.email = f"{role}@example.com"
    user.role = role
    user.organization_id = uuid.UUID(org_id) if org_id else None
    user.is_active = True
    user.token_version = 0
    return user


def _make_session_with_user(user: Mock, extra_executes: list | None = None):
    """Create a session override that returns a mock user for get_current_user,
    plus optional extra execute results for route logic.

    get_current_user calls:
    1. is_token_blacklisted (db.execute on TokenBlacklist) → returns None (not blacklisted)
    2. db.execute on User table → returns the user
    Then route logic executes extra_executes in order.
    """
    # First: blacklist check (returns None = not blacklisted)
    mock_blacklist_result = Mock()
    mock_blacklist_result.scalar_one_or_none.return_value = None

    # Second: get_current_user queries User table
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


# ── Organization Endpoints ───────────────────────────────────────────────────


class TestOrganizationEndpoints:
    """POST /organizations, GET /organizations/:id, PUT /organizations/:id"""

    @pytest.mark.anyio
    async def test_create_organization_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("super_admin")
        token = _make_org_token(org_id, "super_admin", user_id=current_user.id)
        org_uuid = uuid.uuid4()

        mock_org = Mock()
        mock_org.id = org_uuid
        mock_org.name = "Acme Corp"
        mock_org.slug = "acme-corp"
        mock_org.kms_key_id = None
        mock_org.is_active = True
        mock_org.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_org.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        # execute for slug check: returns None (no duplicate)
        mock_slug_result = Mock()
        mock_slug_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_slug_result])

        async def refresh_side_effect(obj):
            obj.id = org_uuid
            obj.name = "Acme Corp"
            obj.slug = "acme-corp"
            obj.kms_key_id = None
            obj.is_active = True
            obj.created_at = datetime(2025, 1, 1, tzinfo=UTC)
            obj.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/organizations",
                json={"name": "Acme Corp", "slug": "acme-corp"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Acme Corp"
        assert body["slug"] == "acme-corp"
        assert body["is_active"] is True

    @pytest.mark.anyio
    async def test_create_organization_duplicate_slug_returns_409(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("super_admin")
        token = _make_org_token(org_id, "super_admin", user_id=current_user.id)

        existing = Mock()
        existing.id = uuid.uuid4()

        # execute for slug check: returns existing org
        mock_slug_result = Mock()
        mock_slug_result.scalar_one_or_none.return_value = existing

        mock_session = _make_session_with_user(current_user, [mock_slug_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/organizations",
                json={"name": "Acme Corp", "slug": "acme-corp"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "DUPLICATE_SLUG"

    @pytest.mark.anyio
    async def test_get_organization_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("super_admin")
        token = _make_org_token(org_id, "super_admin", user_id=current_user.id)
        org_uuid = uuid.UUID(org_id)

        mock_org = Mock()
        mock_org.id = org_uuid
        mock_org.name = "Acme Corp"
        mock_org.slug = "acme-corp"
        mock_org.kms_key_id = "key-123"
        mock_org.is_active = True
        mock_org.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_org.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        # execute for org lookup
        mock_org_result = Mock()
        mock_org_result.scalar_one_or_none.return_value = mock_org

        mock_session = _make_session_with_user(current_user, [mock_org_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/organizations/{org_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == org_id
        assert body["name"] == "Acme Corp"
        assert body["kms_key_id"] == "key-123"

    @pytest.mark.anyio
    async def test_get_organization_not_found_returns_404(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("super_admin")
        token = _make_org_token(org_id, "super_admin", user_id=current_user.id)

        mock_org_result = Mock()
        mock_org_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_org_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/organizations/{org_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    @pytest.mark.anyio
    async def test_update_organization_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("super_admin")
        token = _make_org_token(org_id, "super_admin", user_id=current_user.id)
        org_uuid = uuid.UUID(org_id)

        mock_org = Mock()
        mock_org.id = org_uuid
        mock_org.name = "Old Name"
        mock_org.slug = "old-slug"
        mock_org.kms_key_id = None
        mock_org.is_active = True
        mock_org.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_org.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_org_result = Mock()
        mock_org_result.scalar_one_or_none.return_value = mock_org

        mock_session = _make_session_with_user(current_user, [mock_org_result])

        async def refresh_side_effect(obj):
            obj.name = "New Name"
            obj.slug = "old-slug"
            obj.kms_key_id = "new-key"
            obj.updated_at = datetime(2025, 6, 1, tzinfo=UTC)

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/organizations/{org_id}",
                json={"name": "New Name", "kms_key_id": "new-key"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "New Name"
        assert body["kms_key_id"] == "new-key"

    @pytest.mark.anyio
    async def test_create_organization_requires_super_admin(self):
        """Regular user should not be able to create organizations."""
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = current_user

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/organizations",
                json={"name": "Acme Corp", "slug": "acme-corp"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    @pytest.mark.anyio
    async def test_create_organization_requires_auth(self):
        """Unauthenticated request should be rejected."""
        app = create_app()
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/organizations",
                json={"name": "Acme Corp", "slug": "acme-corp"},
            )

        assert response.status_code == 401


# ── User Management Endpoints ────────────────────────────────────────────────


class TestUserEndpoints:
    """GET /users, POST /users/invite, PUT /users/:id, DELETE /users/:id"""

    @pytest.mark.anyio
    async def test_list_users_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)

        mock_user1 = Mock()
        mock_user1.id = uuid.uuid4()
        mock_user1.email = "user1@example.com"
        mock_user1.role = "recruiter"
        mock_user1.is_active = True
        mock_user1.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_user1.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_user2 = Mock()
        mock_user2.id = uuid.uuid4()
        mock_user2.email = "user2@example.com"
        mock_user2.role = "manager"
        mock_user2.is_active = True
        mock_user2.created_at = datetime(2025, 1, 2, tzinfo=UTC)
        mock_user2.updated_at = datetime(2025, 1, 2, tzinfo=UTC)

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2

        mock_users_result = Mock()
        mock_users_result.scalars.return_value.all.return_value = [mock_user1, mock_user2]

        mock_session = _make_session_with_user(current_user, [mock_count_result, mock_users_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["pagination"]["total"] == 2
        assert len(body["data"]) == 2
        assert body["data"][0]["email"] == "user1@example.com"

    @pytest.mark.anyio
    async def test_list_users_requires_admin(self):
        """Recruiter should not be able to list users."""
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = current_user

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    @pytest.mark.anyio
    async def test_invite_user_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        new_user_id = uuid.uuid4()

        mock_new_user = Mock()
        mock_new_user.id = new_user_id
        mock_new_user.email = "newuser@example.com"
        mock_new_user.role = "recruiter"
        mock_new_user.is_active = True
        mock_new_user.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_new_user.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        # execute for existing user check: None
        mock_empty_result = Mock()
        mock_empty_result.scalar_one_or_none.return_value = None
        # execute for create: return new user
        mock_create_result = Mock()
        mock_create_result.scalar_one.return_value = mock_new_user
        # execute for get user by email (for magic link token)
        mock_email_result = Mock()
        mock_email_result.scalar_one.return_value = mock_new_user

        mock_session = _make_session_with_user(current_user, [mock_empty_result, mock_create_result, mock_email_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/users/invite",
                json={"email": "newuser@example.com", "role": "recruiter"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert "magic_link" in body
        assert "expires_at" in body
        assert "http://localhost:3000/invite?token=" in body["magic_link"]

    @pytest.mark.anyio
    async def test_invite_user_requires_admin(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = current_user

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/users/invite",
                json={"email": "newuser@example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_update_user_requires_reason_for_role_change(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        target_user_id = str(uuid.uuid4())

        mock_target = Mock()
        mock_target.id = uuid.UUID(target_user_id)
        mock_target.email = "user@example.com"
        mock_target.role = "recruiter"
        mock_target.is_active = True
        mock_target.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_target.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_target

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/users/{target_user_id}",
                json={"role": "manager"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "MISSING_REASON"

    @pytest.mark.anyio
    async def test_update_user_with_reason_succeeds(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        target_user_id = str(uuid.uuid4())

        mock_target = Mock()
        mock_target.id = uuid.UUID(target_user_id)
        mock_target.email = "user@example.com"
        mock_target.role = "recruiter"
        mock_target.is_active = True
        mock_target.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_target.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_target

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.role = "manager"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/users/{target_user_id}",
                json={"role": "manager", "reason": "Promotion to team lead"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "manager"

    @pytest.mark.anyio
    async def test_deactivate_user_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        target_user_id = str(uuid.uuid4())

        mock_target = Mock()
        mock_target.id = uuid.UUID(target_user_id)
        mock_target.email = "user@example.com"
        mock_target.role = "recruiter"
        mock_target.is_active = True
        mock_target.token_version = 0
        mock_target.organization_id = uuid.UUID(org_id)
        mock_target.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_target.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_target

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.is_active = False
            obj.token_version = 1

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/users/{target_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["is_active"] is False
        assert mock_target.token_version == 1

    @pytest.mark.anyio
    async def test_deactivate_user_not_found_returns_404(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        target_user_id = str(uuid.uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/users/{target_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 404


# ── Client Contact Endpoints ─────────────────────────────────────────────────


class TestClientContactEndpoints:
    """GET, POST, PUT, DELETE /client-contacts"""

    @pytest.mark.anyio
    async def test_list_client_contacts_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)

        mock_contact1 = Mock()
        mock_contact1.id = uuid.uuid4()
        mock_contact1.email = "client@acme.com"
        mock_contact1.first_name = "John"
        mock_contact1.last_name = "Doe"
        mock_contact1.phone = "+1234567890"
        mock_contact1.is_active = True
        mock_contact1.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_contact1.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        mock_contacts_result = Mock()
        mock_contacts_result.scalars.return_value.all.return_value = [mock_contact1]

        mock_session = _make_session_with_user(current_user, [mock_count_result, mock_contacts_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/client-contacts",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["pagination"]["total"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0]["first_name"] == "John"

    @pytest.mark.anyio
    async def test_create_client_contact_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        contact_uuid = uuid.uuid4()

        mock_contact = Mock()
        mock_contact.id = contact_uuid
        mock_contact.email = "client@acme.com"
        mock_contact.first_name = "Jane"
        mock_contact.last_name = "Smith"
        mock_contact.phone = "+1987654321"
        mock_contact.is_active = True
        mock_contact.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_contact.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_empty_result = Mock()
        mock_empty_result.scalar_one_or_none.return_value = None

        mock_session = _make_session_with_user(current_user, [mock_empty_result])

        async def refresh_side_effect(obj):
            obj.id = contact_uuid
            obj.created_at = datetime(2025, 1, 1, tzinfo=UTC)
            obj.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/client-contacts",
                json={
                    "email": "client@acme.com",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "phone": "+1987654321",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "client@acme.com"
        assert body["first_name"] == "Jane"

    @pytest.mark.anyio
    async def test_create_client_contact_duplicate_email_returns_409(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)

        existing = Mock()
        existing.id = uuid.uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/client-contacts",
                json={
                    "email": "client@acme.com",
                    "first_name": "Jane",
                    "last_name": "Smith",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "DUPLICATE_EMAIL"

    @pytest.mark.anyio
    async def test_update_client_contact_success(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        contact_id = str(uuid.uuid4())

        mock_contact = Mock()
        mock_contact.id = uuid.UUID(contact_id)
        mock_contact.email = "client@acme.com"
        mock_contact.first_name = "Jane"
        mock_contact.last_name = "Smith"
        mock_contact.phone = "+1987654321"
        mock_contact.is_active = True
        mock_contact.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_contact.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_contact

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.first_name = "Janet"

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/client-contacts/{contact_id}",
                json={"first_name": "Janet"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["first_name"] == "Janet"

    @pytest.mark.anyio
    async def test_delete_client_contact_soft_deletes(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("admin", org_id)
        token = _make_user_token(org_id, "admin", user_id=current_user.id)
        contact_id = str(uuid.uuid4())

        mock_contact = Mock()
        mock_contact.id = uuid.UUID(contact_id)
        mock_contact.email = "client@acme.com"
        mock_contact.first_name = "Jane"
        mock_contact.last_name = "Smith"
        mock_contact.phone = None
        mock_contact.is_active = True
        mock_contact.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_contact.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_contact

        mock_session = _make_session_with_user(current_user, [mock_result])

        async def refresh_side_effect(obj):
            obj.is_active = False

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/client-contacts/{contact_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["is_active"] is False

    @pytest.mark.anyio
    async def test_client_contacts_requires_admin(self):
        org_id = str(uuid.uuid4())
        current_user = _make_current_user("recruiter", org_id)
        token = _make_user_token(org_id, "recruiter", user_id=current_user.id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = current_user

        mock_session = _make_session_with_user(current_user, [mock_result])

        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_session
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/client-contacts",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 403


# ── Tenant Isolation ─────────────────────────────────────────────────────────


class TestTenantIsolation:
    """Verify that users from different organizations cannot access each other's data."""

    @pytest.mark.anyio
    async def test_different_org_tokens_produce_different_org_id(self):
        """Tokens from different orgs should set different request.state.organization_id."""
        org_a = str(uuid.uuid4())
        org_b = str(uuid.uuid4())

        token_a = create_access_token({
            "sub": str(uuid.uuid4()),
            "org_id": org_a,
            "role": "admin",
            "token_version": 0,
        })
        token_b = create_access_token({
            "sub": str(uuid.uuid4()),
            "org_id": org_b,
            "role": "admin",
            "token_version": 0,
        })

        app = create_app()
        transport = ASGITransport(app=app)

        from fastapi import Request

        @app.get("/test/org-a")
        async def org_a_endpoint(request: Request):
            return {"org_id": request.state.organization_id}

        @app.get("/test/org-b")
        async def org_b_endpoint(request: Request):
            return {"org_id": request.state.organization_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r_a = await client.get(
                "/test/org-a",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            r_b = await client.get(
                "/test/org-b",
                headers={"Authorization": f"Bearer {token_b}"},
            )

        assert r_a.json()["org_id"] == org_a
        assert r_b.json()["org_id"] == org_b
        assert org_a != org_b

    @pytest.mark.anyio
    async def test_super_admin_token_has_no_org(self):
        """SuperAdmin tokens should have org_id=None."""
        token = create_access_token({
            "sub": str(uuid.uuid4()),
            "org_id": None,
            "role": "super_admin",
            "token_version": 0,
        })

        app = create_app()
        transport = ASGITransport(app=app)

        from fastapi import Request

        @app.get("/test/platform")
        async def platform_endpoint(request: Request):
            return {"org_id": request.state.organization_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/platform",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["org_id"] is None


# ── Token Revocation & Expiration Edge Cases ─────────────────────────────────


class TestTokenEdgeCases:
    """Tests for invitation expiration, password reset expiry, token revocation."""

    @pytest.mark.anyio
    async def test_expired_invite_token_rejected(self):
        """Magic link tokens that have expired should be rejected.

        We construct an expired token manually since freeze_time doesn't
        reliably affect PyJWT's internal time checks.
        """
        from jose import jwt as pyjwt
        from app.config import settings

        now = int(datetime.now(UTC).timestamp())
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "type": "magic_link",
            "email": "test@example.com",
            "exp": now - 100,  # Expired 100 seconds ago
            "iat": now - 200,
            "jti": str(uuid.uuid4()),
        }
        magic_token = pyjwt.encode(expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

        # Should be expired
        with pytest.raises(Exception) as exc_info:
            verify_token(magic_token)
        assert exc_info.value.code == "TOKEN_EXPIRED"

    @pytest.mark.anyio
    async def test_token_revoked_on_deactivation(self):
        """When a user is deactivated, their token_version increments and tokens are revoked."""
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())

        token = create_access_token({
            "sub": user_id,
            "org_id": org_id,
            "role": "admin",
            "token_version": 0,
        })

        mock_user = Mock()
        mock_user.id = uuid.UUID(user_id)
        mock_user.is_active = True
        mock_user.token_version = 1

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def get_override():
            return mock_session

        app = create_app()
        app.dependency_overrides[get_session] = get_override
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user
        from fastapi import Depends

        @app.get("/test/check-token")
        async def check_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/check-token",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "TOKEN_REVOKED"

    @pytest.mark.anyio
    async def test_refresh_token_cannot_be_used_as_access_token(self):
        """A refresh token should not work for protected endpoints."""
        refresh_token = create_refresh_token({"sub": str(uuid.uuid4())})

        app = create_app()
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user
        from fastapi import Depends

        @app.get("/test/refresh-rejected")
        async def endpoint(user=Depends(get_current_user)):
            return {"ok": True}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/refresh-rejected",
                headers={"Authorization": f"Bearer {refresh_token}"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_TOKEN_TYPE"

    @pytest.mark.anyio
    async def test_password_reset_token_expiry(self):
        """Password reset tokens should expire after 1 hour.

        We construct an expired token manually since freeze_time doesn't
        reliably affect PyJWT's internal time checks.
        """
        from jose import jwt as pyjwt
        from app.config import settings

        now = int(datetime.now(UTC).timestamp())
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "type": "password_reset",
            "email": "test@example.com",
            "exp": now - 100,  # Expired 100 seconds ago
            "iat": now - 4000,  # Created ~1.1 hours ago
            "jti": str(uuid.uuid4()),
        }
        reset_token = pyjwt.encode(expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

        # Should be expired
        with pytest.raises(Exception) as exc_info:
            verify_token(reset_token, expected_type="password_reset")
        assert exc_info.value.code == "TOKEN_EXPIRED"
