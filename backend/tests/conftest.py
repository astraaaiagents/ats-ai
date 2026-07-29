import os
import sys
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

# Ensure both repository root and backend directory are in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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
        redis_instance.zremrangebyscore = AsyncMock(return_value=0)
        redis_instance.zcard = AsyncMock(return_value=0)
        pipeline_mock = Mock()
        pipeline_mock.execute = AsyncMock()
        redis_instance.pipeline = AsyncMock(return_value=pipeline_mock)
        mock.return_value = redis_instance
        yield mock
