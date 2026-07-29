# Wayfinder Map: Agent-First Recruiter Portal

**Destination:** Implement the Agent-First AI-Native Recruiter Client Portal — a conversational, agent-driven interface for staffing agency recruiters, built on top of the existing ATS backend. The system features an Orchestrator + Specialist Agent architecture (Sourcing, Ranking, Outreach) with preference learning, proactive alerts, and a Next.js chat UI.

**Notes:**
- Base documents: `agent-ats-ai.md` (PRD), `docs/superpowers/specs/2026-07-22-agent-first-recruiter-portal-design.md` (design spec)
- Current state: FastAPI backend with candidates/users/orgs/auth/multi-tenancy. No frontend. No agent code.
- PRD scope: 7 phases over ~20 weeks
- Preference: Implementation decisions with architecture review
- Tracker: Local markdown (`.scratch/wayfinder/`) — `gh` CLI not available

## Decisions so far

- [Research: LangGraph vs alternatives](.scratch/wayfinder/research-langgraph-alternatives-findings.md) — **CONFIRM** LangGraph is production-ready with durable execution, human-in-the-loop, and TypeScript SDK (LangGraph.js) for full-stack consistency
- [Research: pgvector vs separate vector DB](.scratch/wayfinder/research-pgvector-vs-vector-db-findings.md) — **CONFIRM** pgvector with HNSW is excellent for 50K-500K vectors; sub-10ms latency; migrate to dedicated vector DB only at 10M+ vectors
- [Research: SSE vs WebSocket](.scratch/wayfinder/research-sse-vs-websocket-findings.md) — **CONFIRM** SSE is the right choice — server-push alerts + HTTP POST chat = perfect fit; auto-reconnect with Last-Event-ID replay; 100+ concurrent connections is trivial
- [Research: ARQ vs Celery](.scratch/wayfinder/research-arq-vs-celery-findings.md) — **CHALLENGE** ARQ is adequate for MVP (200 tasks/day) but is in maintenance-only mode; use ARQ for MVP with documented migration path to Celery if scale grows
- [Research: Embedding models](.scratch/wayfinder/research-embedding-models-findings.md) — **CONFIRM** OpenAI text-embedding-3-small (1536-dim) is the best balance of accuracy, cost (~$30/mo at 500K), and simplicity; re-embed event-driven + weekly batch
- [Task: DB schema migrations](.scratch/wayfinder/task-db-schema-migrations.md) — **DONE** Migration `005_agent_portal.py` creates 6 tables + pgvector extension; models in `app/models/`; HNSW indexing for vectors, GIN for JSONB, check constraints on enums, SHA-256 pseudonymization documented
- [Task: Agent Gateway API](.scratch/wayfinder/task-agent-gateway-api.md) — **DONE** 6 endpoints in `routes/agent.py`, schemas in `schemas/agent.py`, service layer in `services/agent.py`; SSE via `EventSourceResponse` with 5-event sequence; pseudonymization via SHA-256; placeholder for Orchestrator integration
- [Task: Orchestrator Agent](.scratch/wayfinder/task-orchestrator-agent.md) — **DONE** 7-node LangGraph StateGraph (`classify_intent` → conditional routing → specialist → `synthesize_response` → END); rule-based intent classifier (6 intents); specialist agents as Python async functions (Sourcing, Ranking, Outreach); placeholder implementations for all specialists; `run_orchestrator()` entry point in `services/agent_orchestrator/__init__.py`
- [Task: Sourcing Agent](.scratch/wayfinder/task-sourcing-agent.md) — **DONE** Hybrid search with RRF (Reciprocal Rank Fusion, k=60): structured keyword + full-text (tsvector) + vector (pgvector); keyword extraction with stop-word filtering; tenant-scoped queries; job details lookup via client_contacts; placeholder implementations removed for search, still pending for job board polling and sub-vendor intake (out of MVP scope)
- [Task: Ranking Agent](.scratch/wayfinder/task-ranking-agent.md) — **DONE** Deterministic fit scoring (skill_match 40% + experience_match 25% + preference_alignment 35%); explicit preferences as hard filters (visa, experience, notice period, locations, skills); implicit preferences adjust weights; gap/strength analysis; <50ms for 50 candidates; proactive threshold 0.85
- [Task: Preference Engine](.scratch/wayfinder/task-preference-engine.md) — **DONE** Full CRUD for explicit preferences; implicit learning via weighted updates (LEARNING_RATE=0.1); 12 feature dimensions (cloud, leadership, python, java, etc.); approval/rejection/explicit_statement learning triggers; weekly digest; learning event versioning; GDPR erasure; MVP uses JSON-stored vector (production: pgvector)
- [Task: Proactive Monitor](.scratch/wayfinder/task-proactive-monitor.md) — **DONE** APScheduler-based sourcing pulse every 30 min (ARQ replaced due to maintenance-only status); parallel processing via asyncio.gather; alert batching (max 3/hour); threshold 0.85; graceful degradation per-recruiter; integrated into FastAPI lifespan; manual trigger for testing
- [Task: Chat UI](.scratch/wayfinder/task-chat-ui.md) — **UPDATED** Spec revised per `docs/superpowers/specs/2026-07-26-agent-portal-ui-ux-design.md` + review fixes: Hybrid interaction paradigm (Activity Feed default + Pipeline/Kanban + persistent Command Panel); Warm Indigo visual theme (#4f46e5); Command Panel three states (Compact 340px, Expanded Detail 440px, Side-by-Side Compare); 5 AI output badges (EU AI Act); 5 views (Feed, Pipeline, Jobs, Preferences, Analytics placeholder); full component tree; WCAG 2.1 AA; responsive breakpoints. **Review fixes:** Job selector dropdown with "All Jobs" view + URL encoding; Quick Review mode (/quick-review) — card-by-card approve/reject with keyboard/swipe, batch summary; Global search bar (⌘K) + per-view filters (Pipeline: skill chips, fit score slider, experience, location, visa; Jobs: client search, status dropdown, domain multi-select).

## Not yet specified

- Phase 4 (Outreach Agent) — depends on Sourcing+Ranking being stable
- Phase 5 (Chat UI Polish) — depends on Agent Gateway being functional
- Phase 6 (Proactive Monitor) — depends on Ranking Agent and ARQ setup
- Phase 7 (Compliance + Polish) — depends on all phases
- Deployment strategy (Docker, cloud, etc.)
- Testing strategy for agent code
- LLM provider configuration and cost management

## Out of scope

- Sub-vendor management workflows (Phase 4+ per PRD)
- Direct employer self-service logins (V1 exclusion per PRD)
- Autonomous AI candidate rejection (EU AI Act policy)
- Invoicing and fee tracking (back-office, out of MVP)
- Advanced KPI dashboards (Phase 3+ per PRD)
- Multi-language support (Phase 3+ per PRD)
- Mobile app (web-responsive sufficient for MVP)

## Tickets

### Architecture Review (Research — can run in parallel)

| # | Ticket | Type | Blocked By |
|---|--------|------|------------|
| 1 | [Research: LangGraph vs alternatives](.scratch/wayfinder/research-langgraph-alternatives.md) | research | — |
| 2 | [Research: pgvector vs separate vector DB](.scratch/wayfinder/research-pgvector-vs-vector-db.md) | research | — |
| 3 | [Research: SSE vs WebSocket](.scratch/wayfinder/research-sse-vs-websocket.md) | research | — |
| 4 | [Research: ARQ vs Celery](.scratch/wayfinder/research-arq-vs-celery.md) | research | — |
| 5 | [Research: Embedding models](.scratch/wayfinder/research-embedding-models.md) | research | — |

### Implementation (sequential dependencies)

| # | Ticket | Type | Blocked By |
|---|--------|------|------------|
| 6 | [Task: DB schema migrations](.scratch/wayfinder/task-db-schema-migrations.md) | task | — |
| 7 | [Task: Agent Gateway API](.scratch/wayfinder/task-agent-gateway-api.md) | task | 6 |
| 8 | [Task: Orchestrator Agent](.scratch/wayfinder/task-orchestrator-agent.md) | task | 6, 7 |
| 9 | [Task: Sourcing Agent](.scratch/wayfinder/task-sourcing-agent.md) | task | 6, 7 |
| 10 | [Task: Ranking Agent](.scratch/wayfinder/task-ranking-agent.md) | task | 6, 7, 8 |
| 11 | [Task: Preference Engine](.scratch/wayfinder/task-preference-engine.md) | task | 6, 7, 8, 10 |
| 12 | [Task: Chat UI](.scratch/wayfinder/task-chat-ui.md) | task | 7 |
| 13 | [Task: Proactive Monitor](.scratch/wayfinder/task-proactive-monitor.md) | task | 6, 7, 10 |
| 14 | [Task: Compliance + Polish](.scratch/wayfinder/task-compliance-polish.md) | task | 8, 9, 10, 11, 12, 13 |

### Phases (grouping)

- **Phase 1: Agent Foundation** (Weeks 1-3) → Tickets 6, 7, 8, 11 (partial)
- **Phase 2: Sourcing + Ranking** (Weeks 4-7) → Tickets 9, 10
- **Phase 3: Preference Learning** (Weeks 8-10) → Ticket 11 (complete)
- **Phase 4: Outreach Agent** (Weeks 11-12) → Out of scope for initial map
- **Phase 5: Chat UI Polish** (Weeks 13-16) → Ticket 12
- **Phase 6: Proactive Monitor** (Weeks 17-18) → Ticket 13
- **Phase 7: Compliance + Polish** (Weeks 19-20) → Ticket 14
