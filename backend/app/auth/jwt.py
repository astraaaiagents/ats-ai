import uuid
from datetime import UTC, datetime, timedelta

from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings
from app.middleware.error_handler import AppException


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_expiration_minutes))
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
    )
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(days=settings.jwt_refresh_expiration_days))
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
    )
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError:
        raise AppException(
            code="TOKEN_EXPIRED",
            message="Token has expired",
            status_code=401,
        )
    except JWTError:
        raise AppException(
            code="INVALID_TOKEN",
            message="Invalid or malformed token",
            status_code=401,
        )

    token_type = payload.get("type", "access")
    if token_type != expected_type:
        raise AppException(
            code="INVALID_TOKEN_TYPE",
            message=f"Expected {expected_type} token, got {token_type}",
            status_code=401,
        )

    return payload
