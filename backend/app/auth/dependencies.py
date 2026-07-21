from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.middleware.error_handler import AppException
from app.models.user import User

from .jwt import verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    payload = verify_token(credentials.credentials, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise AppException(
            code="INVALID_TOKEN",
            message="Token missing subject claim",
            status_code=401,
        )

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

    token_version = payload.get("token_version", 0)
    if token_version != user.token_version:
        raise AppException(
            code="TOKEN_REVOKED",
            message="Token has been revoked",
            status_code=401,
        )

    return user


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
