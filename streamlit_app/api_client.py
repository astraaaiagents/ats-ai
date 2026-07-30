import os
import json
import logging
import httpx
from typing import Generator, Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class APIClient:
    """Client for FastAPI Agent Gateway endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")).rstrip("/")
        self.token = token or os.getenv("STREAMLIT_API_TOKEN", "dev-token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_action_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch past activity logs / sessions."""
        try:
            url = f"{self.base_url}/agent/action-log?limit={limit}"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching action log: {exc}")
            return []

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch history for a specific session."""
        try:
            url = f"{self.base_url}/agent/conversation/{session_id}"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("messages", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching conversation {session_id}: {exc}")
            return []

    def stream_conversation(
        self,
        message: str,
        session_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Send message and yield parsed SSE events."""
        url = f"{self.base_url}/agent/conversation"
        payload = {"message": message, "session_id": session_id}

        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=self.headers,
                timeout=30.0,
            ) as response:
                current_event = "message"
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line.replace("event:", "").strip()
                    elif line.startswith("data:"):
                        raw_data = line.replace("data:", "").strip()
                        try:
                            data = json.loads(raw_data)
                            yield {"event": current_event, "data": data}
                        except json.JSONDecodeError:
                            yield {"event": current_event, "data": raw_data}
        except Exception as exc:
            logger.error(f"Error streaming conversation: {exc}")
            yield {"event": "error", "data": {"message": str(exc)}}

    def get_candidates(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch list of candidates with optional status filter."""
        try:
            url = f"{self.base_url}/candidates?limit={limit}"
            if status:
                url += f"&status={status}"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching candidates: {exc}")
            return []

    def update_candidate_status(self, candidate_id: str, new_status: str) -> bool:
        """Update a candidate's pipeline status."""
        try:
            url = f"{self.base_url}/candidates/{candidate_id}/status"
            payload = {"status": new_status, "reason": "Updated via Streamlit Portal"}
            resp = httpx.patch(url, json=payload, headers=self.headers, timeout=10.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.error(f"Error updating candidate {candidate_id} status: {exc}")
            return False

    def get_proactive_alerts(self) -> List[Dict[str, Any]]:
        """Fetch proactive AI alerts and feeds."""
        try:
            url = f"{self.base_url}/agent/proactive/alerts"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("alerts", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching proactive alerts: {exc}")
            return []

    def get_preferences(self) -> Dict[str, Any]:
        """Fetch recruiter preferences."""
        try:
            url = f"{self.base_url}/agent/preferences"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as exc:
            logger.error(f"Error fetching preferences: {exc}")
            return {}

    def update_preferences(self, explicit: Dict[str, Any]) -> Dict[str, Any]:
        """Update explicit recruiter preferences."""
        try:
            url = f"{self.base_url}/agent/preferences"
            payload = {"explicit": explicit}
            resp = httpx.put(url, json=payload, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as exc:
            logger.error(f"Error updating preferences: {exc}")
            return {}
