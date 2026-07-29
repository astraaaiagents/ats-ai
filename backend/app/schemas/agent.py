"""Agent Gateway API schemas.

Schemas for the agent-first recruiter portal API endpoints:
- POST /api/v1/agent/conversation (SSE streaming)
- GET /api/v1/agent/conversation/{session_id}
- GET/PUT /api/v1/agent/preferences
- GET /api/v1/agent/proactive/alerts
- GET /api/v1/agent/action-log
"""

from typing import Any

from pydantic import BaseModel, Field


# --- Conversation ---


class ConversationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: str | None = None


class ConversationHistoryResponse(BaseModel):
    session_id: str
    title: str | None = None
    messages: list["AgentMessageResponse"] = []


class AgentMessageResponse(BaseModel):
    id: str
    role: str  # "agent" | "user" | "system"
    content: str
    cards: list[dict[str, Any]] = []
    actions: list["AgentActionResponse"] = []
    sources: list["SourceRefResponse"] = []
    confidence: float | None = None
    is_proactive: bool = False
    created_at: str


class AgentActionResponse(BaseModel):
    id: str
    label: str
    type: str  # "approve" | "reject" | "submit" | "edit_preference" | "schedule_interview" | "draft_outreach"
    payload: dict[str, Any] = {}
    confirmation: str | None = None


class SourceRefResponse(BaseModel):
    type: str  # "internal_db" | "job_board" | "sub_vendor" | "client_portal"
    identifier: str
    timestamp: str


# --- Preferences ---


class PreferenceUpdate(BaseModel):
    explicit: dict[str, Any] = {}


class PreferenceResponse(BaseModel):
    explicit: dict[str, Any] = {}
    implicit_scores: dict[str, float] = {}
    last_updated: str


# --- Proactive Alerts ---


class ProactiveAlertResponse(BaseModel):
    id: str
    alert_type: str  # "new_match" | "pipeline_update" | "feedback_reminder" | "weekly_digest"
    title: str
    body: str
    data: dict[str, Any] | None = None
    is_read: bool = False
    created_at: str


class ProactiveAlertsResponse(BaseModel):
    alerts: list[ProactiveAlertResponse] = []


# --- Action Log ---


class ActionLogEntry(BaseModel):
    id: str
    action_type: str
    agent_name: str
    input_pseudonymized: str
    output_pseudonymized: str
    created_at: str


class ActionLogResponse(BaseModel):
    actions: list[ActionLogEntry] = []
    total: int = 0
    page: int = 1
    per_page: int = 100


# --- Error Responses ---


class ErrorResponse(BaseModel):
    error: str
    code: str
    details: dict[str, Any] | None = None


# --- SSE Event Types (internal, not exposed as API responses) ---

# event: message_start
# data: {"session_id": "uuid", "timestamp": "2026-07-26T10:00:00Z"}
#
# event: content
# data: {"type": "text", "content": "Here are your top matches:"}
#
# event: card
# data: {"type": "candidate", "data": {...}, "fitScore": 0.92}
#
# event: action
# data: {"id": "approve_1", "label": "Approve", "type": "approve", "payload": {"candidate_id": "uuid"}}
#
# event: message_end
# data: {"confidence": 0.88, "sources": [{"type": "internal_db", "identifier": "candidates"}]}
