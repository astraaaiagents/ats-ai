import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends
from freezegun import freeze_time
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.password import hash_password, verify_password
from app.database import get_session
from app.main import create_app
from app.middleware.error_handler import AppException


def _make_session_override(user):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def get_override():
        return mock_session

    return get_override


class TestPasswordHashing:
    def test_hash_password_round_trip(self):
        plain = "secure-password-123!"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_verify_password_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_password_different_each_time(self):
        plain = "same-password"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2
        assert verify_password(plain, h1) is True
        assert verify_password(plain, h2) is True


class TestJWTTokens:
    def test_create_access_token_has_required_claims(self):
        data = {"sub": str(uuid.uuid4()), "org_id": str(uuid.uuid4()), "role": "recruiter", "token_version": 0}
        token = create_access_token(data)
        payload = verify_token(token, expected_type="access")
        assert payload["sub"] == data["sub"]
        assert payload["org_id"] == data["org_id"]
        assert payload["role"] == data["role"]
        assert payload["token_version"] == 0
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_create_refresh_token_has_type_claim(self):
        data = {"sub": str(uuid.uuid4())}
        token = create_refresh_token(data)
        payload = verify_token(token, expected_type="refresh")
        assert payload["sub"] == data["sub"]
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_access_token_default_expiry(self):
        data = {"sub": str(uuid.uuid4())}
        with freeze_time("2025-01-01T00:00:00Z") as frozen_time:
            token = create_access_token(data)
            payload = verify_token(token)
            exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
            expected = datetime(2025, 1, 2, 0, 0, 0, tzinfo=UTC)
            assert exp == expected

    def test_access_token_custom_expiry(self):
        data = {"sub": str(uuid.uuid4())}
        with freeze_time("2025-01-01T00:00:00Z") as frozen_time:
            token = create_access_token(data, expires_delta=timedelta(minutes=30))
            payload = verify_token(token)
            exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
            assert exp == datetime(2025, 1, 1, 0, 30, 0, tzinfo=UTC)

    def test_refresh_token_default_expiry(self):
        data = {"sub": str(uuid.uuid4())}
        with freeze_time("2025-01-01T00:00:00Z") as frozen_time:
            token = create_refresh_token(data)
            payload = verify_token(token, "refresh")
            exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
            assert exp == datetime(2025, 1, 31, 0, 0, 0, tzinfo=UTC)

    def test_verify_expired_token_raises(self):
        data = {"sub": str(uuid.uuid4())}
        with freeze_time("2025-01-01T00:00:00Z") as frozen_time:
            token = create_access_token(data, expires_delta=timedelta(minutes=1))
        with freeze_time("2025-01-01T00:02:00Z"):
            with pytest.raises(AppException) as exc_info:
                verify_token(token)
            assert exc_info.value.status_code == 401
            assert exc_info.value.code == "TOKEN_EXPIRED"

    def test_verify_invalid_token_raises(self):
        with pytest.raises(AppException) as exc_info:
            verify_token("this.is.not.a.valid.token")
        assert exc_info.value.status_code == 401
        assert exc_info.value.code == "INVALID_TOKEN"

    def test_verify_wrong_type_raises(self):
        data = {"sub": str(uuid.uuid4())}
        token = create_refresh_token(data)
        with pytest.raises(AppException) as exc_info:
            verify_token(token, expected_type="access")
        assert exc_info.value.status_code == 401
        assert exc_info.value.code == "INVALID_TOKEN_TYPE"

    def test_verify_access_token_as_refresh_raises(self):
        data = {"sub": str(uuid.uuid4())}
        token = create_access_token(data)
        with pytest.raises(AppException) as exc_info:
            verify_token(token, expected_type="refresh")
        assert exc_info.value.status_code == 401


@pytest.mark.anyio
class TestAuthDependencies:
    async def test_valid_token_returns_user(self):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": user_id, "org_id": org_id, "role": "recruiter", "token_version": 0,
        })
        mock_user = Mock()
        mock_user.id = uuid.UUID(user_id)
        mock_user.email = "test@example.com"
        mock_user.role = "recruiter"
        mock_user.organization_id = uuid.UUID(org_id)
        mock_user.is_active = True
        mock_user.token_version = 0
        session_override = _make_session_override(mock_user)

        app = create_app()
        app.dependency_overrides[get_session] = session_override
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id), "email": user.email, "role": user.role}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/auth",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == user_id
        assert body["email"] == "test@example.com"
        assert body["role"] == "recruiter"

    async def test_expired_token_returns_401(self):
        with freeze_time("2025-01-01T00:00:00Z") as frozen_time:
            token = create_access_token(
                {"sub": str(uuid.uuid4())},
                expires_delta=timedelta(minutes=1),
            )

        app = create_app()
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth-expired")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        with freeze_time("2025-01-01T00:02:00Z"):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/test/auth-expired",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "TOKEN_EXPIRED"

    async def test_missing_token_returns_401(self):
        app = create_app()
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth-missing")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/auth-missing")

        assert response.status_code == 401

    async def test_invalid_token_returns_401(self):
        app = create_app()
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth-invalid")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/auth-invalid",
                headers={"Authorization": "Bearer this.is.not.valid"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_TOKEN"

    async def test_refresh_token_rejected_by_auth_dependency(self):
        token = create_refresh_token({"sub": str(uuid.uuid4())})
        app = create_app()
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth-refresh")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/auth-refresh",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_TOKEN_TYPE"

    async def test_inactive_user_returns_401(self):
        user_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": user_id, "org_id": str(uuid.uuid4()), "role": "recruiter", "token_version": 0,
        })
        mock_user = Mock()
        mock_user.id = uuid.UUID(user_id)
        mock_user.is_active = False
        mock_user.token_version = 0
        session_override = _make_session_override(mock_user)

        app = create_app()
        app.dependency_overrides[get_session] = session_override
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth-inactive")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/auth-inactive",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "USER_INACTIVE"

    async def test_stale_token_version_returns_401(self):
        user_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": user_id, "org_id": str(uuid.uuid4()), "role": "recruiter", "token_version": 0,
        })
        mock_user = Mock()
        mock_user.id = uuid.UUID(user_id)
        mock_user.is_active = True
        mock_user.token_version = 1
        session_override = _make_session_override(mock_user)

        app = create_app()
        app.dependency_overrides[get_session] = session_override
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user

        @app.get("/test/auth-stale")
        async def auth_endpoint(user=Depends(get_current_user)):
            return {"id": str(user.id)}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/auth-stale",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "TOKEN_REVOKED"


@pytest.mark.anyio
class TestRoleRequirement:
    async def test_require_role_allows_correct_role(self):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": user_id, "org_id": org_id, "role": "admin", "token_version": 0,
        })
        mock_user = Mock()
        mock_user.id = uuid.UUID(user_id)
        mock_user.role = "admin"
        mock_user.organization_id = uuid.UUID(org_id)
        mock_user.is_active = True
        mock_user.token_version = 0
        session_override = _make_session_override(mock_user)

        app = create_app()
        app.dependency_overrides[get_session] = session_override
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user, require_role

        @app.get("/test/role-check")
        async def role_endpoint(user=Depends(require_role(["admin", "recruiter"]))):
            return {"role": user.role}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/role-check",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    async def test_require_role_blocks_wrong_role(self):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": user_id, "org_id": org_id, "role": "interviewer", "token_version": 0,
        })
        mock_user = Mock()
        mock_user.id = uuid.UUID(user_id)
        mock_user.role = "interviewer"
        mock_user.organization_id = uuid.UUID(org_id)
        mock_user.is_active = True
        mock_user.token_version = 0
        session_override = _make_session_override(mock_user)

        app = create_app()
        app.dependency_overrides[get_session] = session_override
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_current_user, require_role

        @app.get("/test/role-block")
        async def role_endpoint(user=Depends(require_role(["admin"]))):
            return {"role": user.role}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/role-block",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"


class TestTenantMiddleware:
    @pytest.mark.anyio
    async def test_sets_org_id_from_token(self):
        org_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": str(uuid.uuid4()), "org_id": org_id, "role": "recruiter", "token_version": 0,
        })

        app = create_app()
        transport = ASGITransport(app=app)

        from fastapi import Request

        @app.get("/test/tenant")
        async def tenant_endpoint(request: Request):
            return {"org_id": request.state.organization_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/tenant",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["org_id"] == org_id

    @pytest.mark.anyio
    async def test_sets_none_when_no_token(self):
        app = create_app()
        transport = ASGITransport(app=app)

        from fastapi import Request

        @app.get("/test/tenant-no-token")
        async def tenant_endpoint(request: Request):
            return {"org_id": request.state.organization_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/tenant-no-token")

        assert response.status_code == 200
        assert response.json()["org_id"] is None

    @pytest.mark.anyio
    async def test_sets_none_when_invalid_token(self):
        app = create_app()
        transport = ASGITransport(app=app)

        from fastapi import Request

        @app.get("/test/tenant-bad-token")
        async def tenant_endpoint(request: Request):
            return {"org_id": request.state.organization_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/tenant-bad-token",
                headers={"Authorization": "Bearer totally.invalid.token"},
            )

        assert response.status_code == 200
        assert response.json()["org_id"] is None

    @pytest.mark.anyio
    async def test_sets_org_id_for_multiple_endpoints(self):
        org_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": str(uuid.uuid4()), "org_id": org_id, "role": "recruiter", "token_version": 0,
        })

        app = create_app()
        transport = ASGITransport(app=app)

        from fastapi import Request

        @app.get("/test/tenant-a")
        async def tenant_a(request: Request):
            return {"org_id": request.state.organization_id}

        @app.get("/test/tenant-b")
        async def tenant_b(request: Request):
            return {"org_id": request.state.organization_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r1 = await client.get(
                "/test/tenant-a",
                headers={"Authorization": f"Bearer {token}"},
            )
            r2 = await client.get(
                "/test/tenant-b",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert r1.json()["org_id"] == org_id
        assert r2.json()["org_id"] == org_id

    @pytest.mark.anyio
    async def test_get_org_id_dependency(self):
        org_id = str(uuid.uuid4())
        token = create_access_token({
            "sub": str(uuid.uuid4()), "org_id": org_id, "role": "recruiter", "token_version": 0,
        })

        app = create_app()
        transport = ASGITransport(app=app)

        from app.auth.dependencies import get_org_id

        @app.get("/test/org-id-dep")
        async def org_id_endpoint(current_org: str | None = Depends(get_org_id)):
            return {"org_id": current_org}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test/org-id-dep",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["org_id"] == org_id
