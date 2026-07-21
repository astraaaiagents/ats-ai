from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        cursor: str | None = Query(None, description="Pagination cursor"),
        limit: int = Query(25, ge=1, le=100, description="Number of items per page"),
        sort: str | None = Query(None, description="Sort field and direction (e.g., created_at:desc)"),
    ) -> None:
        self.cursor = cursor
        self.limit = limit
        self.sort = sort


def paginated_response(data: list, total: int, limit: int, sort: str | None = None) -> dict:
    has_more = total > limit
    data_slice = data[:limit]
    next_cursor = None
    if has_more and data_slice:
        last = data_slice[-1]
        if isinstance(last, dict):
            next_cursor = str(last.get("id", ""))
        else:
            next_cursor = str(getattr(last, "id", ""))
    return {
        "data": data_slice,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total": total,
            "sort": sort,
        },
    }
