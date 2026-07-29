# Question: What is the Agent Gateway API design?

The PRD defines 6 endpoints but the implementation needs detailed design. Key decisions:

**Endpoints (from PRD):**
1. `POST /api/v1/agent/conversation` — send message, stream response
2. `GET /api/v1/agent/conversation/{session_id}` — retrieve history
3. `GET /api/v1/agent/preferences` — read preferences
4. `PUT /api/v1/agent/preferences` — update preferences
5. `GET /api/v1/agent/proactive/alerts` — get alerts
6. `GET /api/v1/agent/action-log` — audit trail

**Decisions needed:**
1. SSE streaming format — exact event format for `message_start`, `content`, `card`, `action`, `message_end`
2. Session management — how are sessions created? Auto-create on first message?
3. Auth integration — how does the existing JWT middleware integrate? Recruiter role check?
4. Rate limiting — existing Redis rate limiter applies; what are the agent-specific limits?
5. Error handling — what error responses for LLM failures, timeout, invalid input?
6. Tenant isolation — how is tenant-scoping enforced at the API layer?
7. Preference endpoint structure — what's the exact JSON schema for GET/PUT?
8. Action-log pagination — cursor-based (existing pattern) or offset-based?

**Existing patterns to follow:**
- Route pattern: router file in `app/routes/`, schema in `app/schemas/`
- Error handling: `AppException(code, message, details)`
- Pagination: cursor-based, `PaginationParams`, default 25, max 100
- Auth: JWT via `python-jose`, bcrypt, Bearer token `HTTPBearer`

Resolve by designing the complete API (request/response schemas, error handling, streaming format) and writing the FastAPI routes.

---

## Resolution

**Date:** 2026-07-26

**Files created:**
- `backend/app/routes/agent.py` — All 6 Agent Gateway endpoints
- `backend/app/schemas/agent.py` — Pydantic v2 schemas for all request/response types
- `backend/app/services/agent.py` — Service layer (session mgmt, preferences, action logging, pseudonymization)

**Endpoint design decisions:**

1. **SSE streaming format:** `EventSourceResponse` from FastAPI. Event sequence: `message_start` → `content` (text chunks) → `card` (structured cards) → `action` (buttons) → `message_end` (confidence + sources). Nginx `proxy_buffering off` required (documented in headers).

2. **Session management:** Auto-create on first message (when `session_id` is null). Session scoped to `recruiter_id` + `session_id`. New sessions get title "New conversation" (can be updated by Orchestrator).

3. **Auth integration:** Uses existing `get_current_user` dependency (JWT, Bearer token). All endpoints require authentication. No role check needed — all agent endpoints are recruiter-accessible (AMs can also use them via same role).

4. **Rate limiting:** Existing `TenantMiddleware` + Redis rate limiter applies automatically. No agent-specific limits needed at MVP stage.

5. **Error handling:** `AppException(code, message, status_code)` pattern. Specific errors:
   - `INVALID_INPUT` (400) — empty message
   - `NOT_FOUND` (404) — session not found
   - `TOKEN_REVOKED` (401) — via existing auth middleware
   - `USER_INACTIVE` (401) — via existing auth middleware

6. **Tenant isolation:** Existing `TenantMiddleware` sets `request.state.organization_id`. Agent queries are recruiter-scoped (recruiter → organization implicit via user model). No additional tenant filtering needed on agent tables (they're user-scoped, not org-scoped).

7. **Preference endpoint:** GET returns `{explicit: {}, implicit_scores: {}, last_updated: iso}`. PUT accepts `{explicit: {}}` and merges with existing preferences.

8. **Action-log pagination:** Cursor-based via existing `PaginationParams` and `paginated_response`. Supports `start_date`, `end_date`, `action_type` filters.

9. **Pseudonymization:** `pseudonymize()` function in service layer replaces PII field values (first_name, last_name, email, phone, current_employer) with SHA-256 hash (first 16 chars). Applied to `input_pseudonymized` and `output_pseudonymized` in `agent_actions`.

10. **Orchestrator integration point:** The `conversation_stream` generator has a TODO placeholder where the Orchestrator will be called. Current implementation returns a placeholder echo response.

**Pattern consistency:** Follows existing conventions — router prefix pattern, `Depends()` for auth/db, `AppException` for errors, Pydantic v2 with `from_attributes`, service layer for business logic, UUID as strings in API.
