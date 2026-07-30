import pytest
from unittest.mock import MagicMock, patch
from streamlit_app.api_client import APIClient

def test_api_client_init():
    client = APIClient(base_url="http://localhost:8000/api/v1", token="dev-token")
    assert client.base_url == "http://localhost:8000/api/v1"
    assert client.headers["Authorization"] == "Bearer dev-token"

@patch("httpx.get")
def test_get_action_log(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": [{"id": "1", "action_type": "intent_parse"}]}
    mock_get.return_value = mock_resp

    client = APIClient()
    items = client.get_action_log()
    assert len(items) == 1
    assert items[0]["id"] == "1"

@patch("httpx.get")
def test_get_candidates(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": [{"id": "c1", "first_name": "Jane", "last_name": "Doe"}]}
    mock_get.return_value = mock_resp

    client = APIClient()
    candidates = client.get_candidates()
    assert len(candidates) == 1
    assert candidates[0]["first_name"] == "Jane"

@patch("httpx.get")
def test_get_proactive_alerts(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"alerts": [{"id": "a1", "title": "High Fit Score"}]}
    mock_get.return_value = mock_resp

    client = APIClient()
    alerts = client.get_proactive_alerts()
    assert len(alerts) == 1
    assert alerts[0]["title"] == "High Fit Score"

@patch("httpx.delete")
def test_delete_conversation(mock_delete):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_delete.return_value = mock_resp

    client = APIClient()
    success = client.delete_conversation("dummy-sid")
    assert success is True
