from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, HTTPException
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.middleware.error_handler import AppException
from app.middleware.pagination import PaginationParams, paginated_response
from app.middleware.rate_limit import rate_limiter


class TestErrorHandler:
    @pytest.mark.anyio
    async def test_app_exception_returns_error_envelope(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/app-error")
        async def raise_app_error():
            raise AppException(
                code="RESOURCE_NOT_FOUND",
                message="Job posting not found",
                status_code=404,
                details=[{"field": "job_id", "reason": "No job with that ID exists", "code": "not_found"}],
            )

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/app-error")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert body["error"]["message"] == "Job posting not found"
        assert len(body["error"]["details"]) == 1
        assert body["error"]["details"][0]["field"] == "job_id"

    @pytest.mark.anyio
    async def test_validation_error_returns_422_envelope(self):
        app = create_app()
        transport = ASGITransport(app=app)

        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            name: str = Field(min_length=1)

        @app.get("/test/validation-error")
        async def raise_validation_error():
            TestModel(name="")
            return {}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/validation-error")
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert len(body["error"]["details"]) > 0
        assert all("field" in d and "reason" in d and "code" in d for d in body["error"]["details"])

    @pytest.mark.anyio
    async def test_http_exception_returns_error_envelope(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/http-error")
        async def raise_http_error():
            raise HTTPException(status_code=403, detail="Forbidden")

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/http-error")
        assert response.status_code == 403
        body = response.json()
        assert body["error"]["code"] == "HTTP_ERROR"
        assert body["error"]["message"] == "Forbidden"

    @pytest.mark.anyio
    async def test_app_exception_no_details_returns_empty_list(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/app-error-no-details")
        async def raise_no_details():
            raise AppException(code="INTERNAL_ERROR", message="Something went wrong", status_code=500)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/app-error-no-details")
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["details"] == []


class TestRequestID:
    @pytest.mark.anyio
    async def test_generates_request_id_when_missing(self, client):
        response = await client.get("/api/v1/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    @pytest.mark.anyio
    async def test_forwards_request_id_when_provided(self, client):
        response = await client.get("/api/v1/health", headers={"X-Request-ID": "my-custom-id"})
        assert response.headers["X-Request-ID"] == "my-custom-id"

    @pytest.mark.anyio
    async def test_unique_ids_for_different_requests(self, client):
        r1 = await client.get("/api/v1/health")
        r2 = await client.get("/api/v1/health")
        assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]

    @pytest.mark.anyio
    async def test_request_id_available_in_request_state(self, app):
        from fastapi import Request

        transport = ASGITransport(app=app)

        @app.get("/test/state-rid")
        async def check_state(request: Request):
            return {"request_id": request.state.request_id}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/test/state-rid", headers={"X-Request-ID": "state-test-id"})
            assert r.json()["request_id"] == "state-test-id"


class TestPagination:
    def test_paginated_response_basic(self):
        data = [{"id": str(i), "name": f"item_{i}"} for i in range(5)]
        result = paginated_response(data, total=5, limit=10)
        assert len(result["data"]) == 5
        assert result["pagination"]["has_more"] is False
        assert result["pagination"]["next_cursor"] is None
        assert result["pagination"]["total"] == 5

    def test_paginated_response_with_more(self):
        data = [{"id": str(i), "name": f"item_{i}"} for i in range(25)]
        result = paginated_response(data, total=100, limit=20)
        assert len(result["data"]) == 20
        assert result["pagination"]["has_more"] is True
        assert result["pagination"]["next_cursor"] == "19"
        assert result["pagination"]["total"] == 100

    def test_paginated_response_exact_fit(self):
        data = [{"id": str(i)} for i in range(20)]
        result = paginated_response(data, total=20, limit=20)
        assert len(result["data"]) == 20
        assert result["pagination"]["has_more"] is False
        assert result["pagination"]["next_cursor"] is None

    def test_paginated_response_empty(self):
        result = paginated_response([], total=0, limit=20)
        assert result["data"] == []
        assert result["pagination"]["has_more"] is False
        assert result["pagination"]["next_cursor"] is None
        assert result["pagination"]["total"] == 0

    def test_paginated_response_objects_with_id_attr(self):
        class Item:
            def __init__(self, id: str):
                self.id = id

        data = [Item(str(i)) for i in range(25)]
        result = paginated_response(data, total=100, limit=20)
        assert len(result["data"]) == 20
        assert result["pagination"]["next_cursor"] == "19"

    def test_paginated_response_single_item_more_remaining(self):
        data = [{"id": "abc"}]
        result = paginated_response(data, total=5, limit=1)
        assert len(result["data"]) == 1
        assert result["pagination"]["has_more"] is True
        assert result["pagination"]["next_cursor"] == "abc"

    @pytest.mark.anyio
    async def test_pagination_params_through_endpoint(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/paginate")
        async def paginate(params: PaginationParams = Depends()):
            return {"cursor": params.cursor, "limit": params.limit, "sort": params.sort}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/test/paginate?limit=50&cursor=abc&sort=created_at:desc")
            body = r.json()
            assert body["limit"] == 50
            assert body["cursor"] == "abc"
            assert body["sort"] == "created_at:desc"

    @pytest.mark.anyio
    async def test_pagination_params_default_values(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/paginate-defaults")
        async def paginate_defaults(params: PaginationParams = Depends()):
            return {"cursor": params.cursor, "limit": params.limit, "sort": params.sort}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/test/paginate-defaults")
            body = r.json()
            assert body["cursor"] is None
            assert body["limit"] == 25
            assert body["sort"] is None

    @pytest.mark.anyio
    async def test_pagination_params_limit_too_high(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/paginate-clamp")
        async def paginate_clamp(params: PaginationParams = Depends()):
            return {"limit": params.limit}

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/test/paginate-clamp?limit=200")
            assert r.status_code == 422


class TestRateLimit:
    def _mock_redis(self, zcard_return: int = 0):
        from unittest.mock import Mock

        redis_mock = AsyncMock()
        redis_mock.zremrangebyscore = AsyncMock(return_value=0)
        redis_mock.zcard = AsyncMock(return_value=zcard_return)
        pipeline_mock = Mock()
        pipeline_mock.execute = AsyncMock()
        redis_mock.pipeline = AsyncMock(return_value=pipeline_mock)
        return redis_mock

    @pytest.mark.anyio
    async def test_rate_limiter_allows_requests_within_limit(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/rate-limited", dependencies=[Depends(rate_limiter)])
        async def rate_limited_endpoint():
            return {"status": "ok"}

        with patch("app.middleware.rate_limit.get_redis_client") as mock_get:
            mock_get.return_value = self._mock_redis(zcard_return=5)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get("/test/rate-limited")
                assert r.status_code == 200

    @pytest.mark.anyio
    async def test_rate_limiter_blocks_when_limit_exceeded(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/rate-limited-block", dependencies=[Depends(rate_limiter)])
        async def rate_limited_block():
            return {"status": "ok"}

        with patch("app.middleware.rate_limit.get_redis_client") as mock_get:
            mock_get.return_value = self._mock_redis(zcard_return=1000)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get("/test/rate-limited-block")
                assert r.status_code == 429
                assert "burst" in r.json()["error"]["message"].lower()

    @pytest.mark.anyio
    async def test_rate_limiter_checks_all_three_windows(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/rate-limited-all", dependencies=[Depends(rate_limiter)])
        async def rate_limited_all():
            return {"status": "ok"}

        with patch("app.middleware.rate_limit._check_sliding_window") as mock_check:
            mock_check.return_value = (True, 0)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get(
                    "/test/rate-limited-all",
                    headers={"X-Tenant-ID": "tenant-1", "X-User-ID": "user-1"},
                )
                assert r.status_code == 200
                assert mock_check.call_count == 3

    @pytest.mark.anyio
    async def test_rate_limiter_default_ids_when_no_headers(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/rate-limit-default", dependencies=[Depends(rate_limiter)])
        async def rate_limit_default():
            return {"status": "ok"}

        with patch("app.middleware.rate_limit._check_sliding_window") as mock_check:
            mock_check.return_value = (True, 0)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get("/test/rate-limit-default")
                assert r.status_code == 200

    @pytest.mark.anyio
    async def test_rate_limiter_burst_limit_exceeded(self):
        app = create_app()
        transport = ASGITransport(app=app)

        call_index = [0]

        @app.get("/test/burst-limited", dependencies=[Depends(rate_limiter)])
        async def burst_limited():
            return {"status": "ok"}

        with patch("app.middleware.rate_limit._check_sliding_window") as mock_check:
            def side_effect(redis, key, max_requests, window_seconds):
                call_index[0] += 1
                if call_index[0] == 1:
                    return (False, 50)
                return (True, 0)

            mock_check.side_effect = side_effect

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get("/test/burst-limited")
                assert r.status_code == 429
                assert "burst" in r.json()["error"]["message"].lower()

    @pytest.mark.anyio
    async def test_rate_limiter_handles_redis_unavailable(self):
        app = create_app()
        transport = ASGITransport(app=app)

        @app.get("/test/rate-limited-unavailable", dependencies=[Depends(rate_limiter)])
        async def rate_limited_unavailable():
            return {"status": "ok"}

        with patch("app.middleware.rate_limit.get_redis_client") as mock_get:
            mock_get.side_effect = ConnectionError("Redis unavailable")
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get("/test/rate-limited-unavailable")
                assert r.status_code == 503
