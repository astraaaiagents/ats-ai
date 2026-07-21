from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.middleware.error_handler import AppException


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_header = request.headers.get("Authorization")
        org_id: str | None = None

        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header.removeprefix("Bearer ")
            if token_str:
                try:
                    from app.auth.jwt import verify_token

                    payload = verify_token(token_str, expected_type="access")
                    org_id = payload.get("org_id")
                except AppException:
                    pass

        request.state.organization_id = org_id
        response = await call_next(request)
        return response
