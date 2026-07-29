# Question: What is the database schema for the agent system?

The PRD defines 6 new tables but the schema needs refinement for implementation. Key decisions:

**Tables to create:**
1. `recruiter_preferences` — explicit JSONB + implicit pgvector
2. `agent_conversation_sessions` — conversation sessions
3. `agent_conversation_messages` — messages with cards, actions, sources
4. `agent_actions` — EU AI Act audit log
5. `agent_proactive_alerts` — proactive alert notifications
6. `preference_learning_events` — preference evolution tracking

**Decisions needed:**
1. Vector dimension — 1536 (OpenAI) vs other dimensions. Affects pgvector index strategy.
2. JSONB structure — what exactly goes in `explicit_preferences`? What schema for `cards` in messages?
3. Pseudonymization — how are `agent_actions` pseudonymized? What's the transformation?
4. Indexing strategy — which columns need indexes? pgvector HNSW vs IVF index?
5. Soft delete vs hard delete — GDPR erasure requires DELETE; should we use soft deletes for audit?
6. Conversation session lifecycle — auto-prune after 90 days? How?
7. Preference vector update mechanism — how are implicit preferences updated? Batch? Real-time?

**Existing tables used:**
- `candidates` — SourcingAgent queries (tenant-scoped)
- `candidate_skills` — Vector search + structured filter
- `candidate_timeline` — Preference learning
- `organizations` — Tenant isolation
- `users` — Links recruiter to preferences
- `client_contacts` — Job requirements

Resolve by designing the complete schema (column types, constraints, indexes, foreign keys) and writing the Alembic migration.

---

## Resolution

**Date:** 2026-07-26

**Migration created:** `backend/db/versions/005_agent_portal.py`

**Models created:**
- `backend/app/models/recruiter_preference.py` — RecruiterPreference
- `backend/app/models/agent_conversation.py` — AgentConversationSession, AgentConversationMessage
- `backend/app/models/agent_action.py` — AgentAction
- `backend/app/models/agent_alert.py` — AgentProactiveAlert
- `backend/app/models/preference_learning_event.py` — PreferenceLearningEvent

**Key decisions made:**
1. **Vector dimension:** 1536 (OpenAI text-embedding-3-small) — stored as `String(1536)` in pgvector
2. **HNSW indexing:** `m=16`, `ef_construction=256` for implicit_preference_vector
3. **GIN indexes:** On all JSONB columns (explicit_preferences, cards, actions, sources, data, features_before, features_after, preference_delta)
4. **Pseudonymization:** SHA-256 hash of PII fields (names, emails, phones) before storage in agent_actions. Documented in model docstring.
5. **Check constraints:** action_type, agent_name, alert_type, event_type all have CHECK constraints with allowed values
6. **Cascade deletes:** Consistent with existing pattern (`ondelete="CASCADE"` for tenant-scoped data, `ondelete="SET NULL"` for optional references)
7. **Session lifecycle:** 90-day auto-prune via scheduled task (not enforced at DB level to allow GDPR export first)
8. **Preference updates:** Real-time via Preference Engine (no batch mechanism)
9. **Unique constraint:** `uq_recruiter_preferences_recruiter_id` ensures one preference profile per recruiter

**Pattern consistency:** Follows existing conventions — UUID PKs with `gen_random_uuid()`, `Mapped[T]` syntax, `server_default=func.now()` for timestamps, `ondelete` cascade patterns, partial indexes where appropriate.
