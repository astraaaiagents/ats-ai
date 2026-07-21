from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    reason: str
    code: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[FieldError] = []


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PaginationInfo(BaseModel):
    next_cursor: str | None
    has_more: bool
    total: int
    sort: str | None = None


class PaginatedResponse(BaseModel):
    data: list
    pagination: PaginationInfo
