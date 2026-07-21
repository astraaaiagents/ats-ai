from datetime import UTC, datetime, timedelta
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token, is_token_blacklisted, verify_token
from app.auth.password import hash_password, verify_password
from app.config import settings
from app.database import get_session
from app.middleware.error_handler import AppException
from app.models.audit_log import AuditLog
from app.models.blacklist import TokenBlacklist
from app.models.platform_user import PlatformUser
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


async def _authenticate_user(db: AsyncSession, email: str, password: str) -> tuple[object, str]:
    """Find user by email and verify password. Returns (user, user_type) on success."""
    result = await db.execute(
        select(PlatformUser).where(PlatformUser.email == email)
    )
    platform_user = result.scalar_one_or_none()
    if platform_user:
        if not verify_password(password, platform_user.password_hash):
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password",
                status_code=401,
            )
        if not platform_user.is_active:
            raise AppException(
                code="USER_INACTIVE",
                message="User account is inactive",
                status_code=401,
            )
        return platform_user, "platform"

    result = await db.execute(
        select(User).where(User.email == email, User.is_active == True)
    )
    user = result.scalars().first()
    if not user:
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401,
        )

    if not verify_password(password, user.password_hash):
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401,
        )
    if not user.is_active:
        raise AppException(
            code="USER_INACTIVE",
            message="User account is inactive",
            status_code=401,
        )
    return user, "org"


def _build_token_data(user: object, user_type: str) -> dict:
    if user_type == "platform":
        return {
            "sub": str(user.id),
            "org_id": None,
            "role": user.role,
            "token_version": 0,
        }
    return {
        "sub": str(user.id),
        "org_id": str(user.organization_id) if user.organization_id else None,
        "role": user.role,
        "token_version": user.token_version,
    }


@auth_router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)):
    user, user_type = await _authenticate_user(db, body.email, body.password)
    token_data = _build_token_data(user, user_type)
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    db.add(
        AuditLog(
            organization_id=getattr(user, "organization_id", None),
            user_id=user.id,
            event_type="auth.login",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": body.email},
        )
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    payload = verify_token(body.refresh_token, expected_type="refresh")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti, db):
        raise AppException(
            code="TOKEN_REVOKED",
            message="Token has been revoked",
            status_code=401,
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AppException(
            code="INVALID_TOKEN",
            message="Token missing subject claim",
            status_code=401,
        )

    user_id = uuid.UUID(user_id_str)
    org_id_str = payload.get("org_id")
    org_id = uuid.UUID(org_id_str) if org_id_str else None
    role = payload.get("role")
    token_version = payload.get("token_version", 0)

    exp_ts = payload.get("exp")
    if jti and exp_ts:
        db.add(
            TokenBlacklist(
                jti=jti,
                expires_at=datetime.fromtimestamp(exp_ts, tz=UTC),
            )
        )

    if org_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found",
                status_code=401,
            )
        if not user.is_active:
            raise AppException(
                code="USER_INACTIVE",
                message="User account is inactive",
                status_code=401,
            )
        if token_version != user.token_version:
            raise AppException(
                code="TOKEN_REVOKED",
                message="Token has been revoked",
                status_code=401,
            )
        token_data = _build_token_data(user, "org")
    else:
        result = await db.execute(
            select(PlatformUser).where(PlatformUser.id == user_id)
        )
        platform_user = result.scalar_one_or_none()
        if not platform_user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found",
                status_code=401,
            )
        if not platform_user.is_active:
            raise AppException(
                code="USER_INACTIVE",
                message="User account is inactive",
                status_code=401,
            )
        token_data = {
            "sub": str(platform_user.id),
            "org_id": None,
            "role": platform_user.role,
            "token_version": 0,
        }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@auth_router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(PlatformUser).where(PlatformUser.email == body.email)
    )
    platform_user = result.scalar_one_or_none()

    user = None
    if not platform_user:
        result = await db.execute(
            select(User).where(User.email == body.email, User.is_active == True)
        )
        user = result.scalars().first()

    if platform_user or user:
        found_user = platform_user or user
        reset_token = create_access_token(
            {
                "sub": str(found_user.id),
                "type": "password_reset",
                "email": body.email,
            },
            expires_delta=timedelta(hours=1),
        )
        app_url = getattr(settings, "app_url", "http://localhost:3000")
        print(f"Password reset link: {app_url}/reset-password?token={reset_token}")

    return {"message": "If the email exists, a password reset link has been sent"}


@auth_router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_session)):
    payload = verify_token(body.token, expected_type="password_reset")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AppException(
            code="INVALID_TOKEN",
            message="Token missing subject claim",
            status_code=401,
        )

    user_id = uuid.UUID(user_id_str)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.password_hash = hash_password(body.password)
        user.token_version += 1
    else:
        result = await db.execute(
            select(PlatformUser).where(PlatformUser.id == user_id)
        )
        platform_user = result.scalar_one_or_none()
        if not platform_user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found",
                status_code=404,
            )
        platform_user.password_hash = hash_password(body.password)

    return {"message": "Password has been reset successfully"}
