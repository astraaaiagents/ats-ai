from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_redis():
    with patch("app.middleware.rate_limit.get_redis_client") as mock:
        redis_instance = AsyncMock()
        redis_instance.pipeline.return_value = redis_instance
        redis_instance.execute.return_value = [0, 0, 1, 1]
        mock.return_value = redis_instance
        yield mock
