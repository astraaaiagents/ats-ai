import uuid
from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.middleware.error_handler import AppException
from app.models.user import User

from .jwt import is_token_blacklisted, verify_token
from .password import hash_password

security = HTTPBearer()

# Dev user returned when auth is bypassed
_DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_DEV_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_DEV_USER_EMAIL = "dev@localhost"


async def ensure_dev_user(db: AsyncSession) -> User:
    """Ensure the dev user exists in the database when auth is bypassed.

    When bypass_auth is enabled, get_current_user() returns the dev user.
    This function guarantees that user exists in the DB so that
    FK-constrained inserts (e.g. recruiter_preferences, agent_conversation_sessions)
    do not fail with ForeignKeyViolationError.
    """
    try:
        from app.models.organization import Organization
        org_result = await db.execute(select(Organization).where(Organization.id == _DEV_ORG_ID))
        dev_org = org_result.scalar_one_or_none()
        if not dev_org:
            dev_org = Organization(
                id=_DEV_ORG_ID,
                name="Default Organization",
                slug="default-org",
                is_active=True,
            )
            db.add(dev_org)
            await db.flush()
        default_org_id = _DEV_ORG_ID

        result = await db.execute(
            select(User).where(User.id == _DEV_USER_ID)
        )
        user = result.scalar_one_or_none()
        if user:
            if user.organization_id != default_org_id:
                user.organization_id = default_org_id
                await db.commit()
                await db.refresh(user)
            return user

        user = User(
            id=_DEV_USER_ID,
            email=_DEV_USER_EMAIL,
            password_hash=hash_password("dev"),
            role="recruiter",
            organization_id=default_org_id,
            is_active=True,
            token_version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        try:
            await db.rollback()
        except Exception:
            pass
        # Retry select in case of concurrent insert
        try:
            result = await db.execute(select(User).where(User.id == _DEV_USER_ID))
            user = result.scalar_one_or_none()
            if user:
                return user
        except Exception:
            pass
        return _make_dev_user_mock()


def _make_dev_user_mock() -> User:
    """Create a mock dev user for fallback when DB is unavailable."""
    return User(
        id=_DEV_USER_ID,
        email=_DEV_USER_EMAIL,
        password_hash="",
        role="recruiter",
        organization_id=_DEV_ORG_ID,
        is_active=True,
        token_version=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    if credentials and credentials.credentials and credentials.credentials != "dev-token":
        payload = verify_token(credentials.credentials, expected_type="access")
        jti = payload.get("jti")
        if jti:
            blacklisted = await is_token_blacklisted(jti, db)
            if blacklisted:
                raise AppException(
                    code="TOKEN_REVOKED",
                    message="Token has been revoked",
                    status_code=401,
                )

        user_id = payload.get("sub")
        if not user_id:
            raise AppException(
                code="UNAUTHORIZED",
                message="Invalid token payload",
                status_code=401,
            )

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AppException(
                code="UNAUTHORIZED",
                message="User not found or inactive",
                status_code=401,
            )

        if payload.get("token_version", 0) != user.token_version:
            raise AppException(
                code="TOKEN_REVOKED",
                message="Token has been invalidated",
                status_code=401,
            )

        return user

    # Fallback to dev user when auth is bypassed or dev-token is provided
    if settings.bypass_auth or (credentials and credentials.credentials == "dev-token"):
        return await ensure_dev_user(db)

    raise AppException(
        code="UNAUTHORIZED",
        message="Authentication required",
        status_code=401,
    )


def require_role(roles: list[str]):
    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppException(
                code="FORBIDDEN",
                message="Insufficient permissions",
                status_code=403,
            )
        return current_user

    return _role_checker


async def get_org_id(request: Request) -> str | None:
    return getattr(request.state, "organization_id", None)
