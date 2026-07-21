from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorResponse, FieldError


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


def _build_error_response(code: str, message: str, details: list, status_code: int, headers: dict | None = None) -> JSONResponse:
    body = ErrorResponse(error={"code": code, "message": message, "details": details})
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"), headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        headers = getattr(request.state, "rate_limit_headers", None)
        return _build_error_response(exc.code, exc.message, exc.details, exc.status_code, headers=headers)

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        details = [
            FieldError(
                field=".".join(str(loc) for loc in err.get("loc", [])),
                reason=err.get("msg", ""),
                code=err.get("type", "validation_error"),
            )
            for err in exc.errors()
        ]
        headers = getattr(request.state, "rate_limit_headers", None)
        return _build_error_response(
            "VALIDATION_ERROR", "Request validation failed", [d.model_dump() for d in details], 422, headers=headers
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        headers = getattr(request.state, "rate_limit_headers", None)
        return _build_error_response("HTTP_ERROR", exc.detail, [], exc.status_code, headers=headers)
