from fastapi import Request, Response
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.auth.jwt import verify_token
from app.database import async_session_factory
from app.middleware.error_handler import AppException


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_header = request.headers.get("Authorization")
        org_id: str | None = None

        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header.removeprefix("Bearer ")
            if token_str:
                try:
                    payload = verify_token(token_str, expected_type="access")
                    org_id = payload.get("org_id")
                except AppException:
                    pass

        request.state.organization_id = org_id

        try:
            async with async_session_factory() as session:
                await session.execute(
                    text("SET LOCAL app.organization_id = :val"),
                    {"val": org_id or None},
                )
                await session.commit()
        except Exception:
            pass

        response = await call_next(request)
        return response
