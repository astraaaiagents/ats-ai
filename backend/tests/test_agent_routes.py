"""Tests for the Agent API routes.

Tests route structure and endpoint definitions.
Full integration tests require auth and DB setup.
"""

import pytest
from app.routes.agent import agent_router


class TestRouteStructure:
    """Test that agent routes are properly defined."""

    def test_conversation_route_exists(self) -> None:
        routes = [r for r in agent_router.routes if hasattr(r, 'path') and 'conversation' in r.path]
        assert len(routes) >= 1
        post_routes = [r for r in routes if 'POST' in r.methods]
        assert len(post_routes) >= 1

    def test_preferences_routes_exist(self) -> None:
        routes = [r for r in agent_router.routes if hasattr(r, 'path') and 'preferences' in r.path]
        assert len(routes) >= 2  # GET and PUT

    def test_proactive_alerts_route_exists(self) -> None:
        routes = [r for r in agent_router.routes if hasattr(r, 'path') and 'proactive' in r.path]
        assert len(routes) >= 1

    def test_action_log_route_exists(self) -> None:
        routes = [r for r in agent_router.routes if hasattr(r, 'path') and 'action-log' in r.path]
        assert len(routes) >= 1

    def test_all_routes_have_prefix(self) -> None:
        for r in agent_router.routes:
            if hasattr(r, 'path'):
                assert r.path.startswith('/agent'), f"Route {r.path} missing prefix"
