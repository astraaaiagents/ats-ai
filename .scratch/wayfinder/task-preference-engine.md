# Question: How is the Preference Engine implemented?

The Preference Engine stores, updates, and applies recruiter preferences (explicit + implicit). Key decisions:

**Implementation decisions:**
1. **Explicit preferences schema** — What's the JSONB structure? What fields are supported? (min_experience_years, required_visa_status, preferred_locations, etc.)
2. **Implicit preference learning** — How are implicit preferences updated from recruiter actions? What's the update algorithm?
3. **Learning triggers** — After each review batch? After explicit statement? After outreach response? Weekly digest?
4. **Preference vector representation** — What do the 1536 dimensions represent? Skill weights? Domain preferences?
5. **Preference transparency UI** — How does the recruiter see what the agent learned?
6. **Preference override** — How can the recruiter manually adjust implicit preferences?
7. **Preference versioning** — Are preference changes tracked? (preference_learning_events table)
8. **GDPR compliance** — How is preference data deleted on "right to be forgotten"?

**Data flow:**
1. Recruiter reviews N candidates → approves/rejects
2. RankingAgent logs: approval/rejection + candidate features + job context
3. Preference Engine updates: explicit (no change) + implicit (embedding adjusted)
4. Next sourcing pulse: candidates with preferred traits get boosted scores

Resolve by implementing the preference CRUD API, the learning loop, and the preference vector update mechanism.

---

## Resolution

**Date:** 2026-07-26

**File created:** `services/preference_engine/__init__.py` — Full preference engine implementation

**Implementation decisions:**

1. **Explicit preferences schema:** JSONB dict in DB. Supported keys: `required_visa_status`, `min_experience_years`, `max_notice_period_days`, `preferred_locations`, `required_skills`, `excluded_skills`, `preferred_industries`. CRUD operations: `get_explicit_preferences`, `set_explicit_preference`, `update_explicit_preferences`, `delete_explicit_preference`.

2. **Implicit preference learning:** Weighted update algorithm with `LEARNING_RATE = 0.1`. Approvals boost feature weights (`min(1.0, current + rate * value)`). Rejections reduce weights (`max(0.0, current - rate * value)`). Features extracted from candidate profiles using `FEATURE_DIMENSIONS` mapping (12 dimensions: cloud, leadership, startup, finance, healthcare, remote, contract, python, java, javascript, data, devops).

3. **Learning triggers:**
   - `record_approval()` — After recruiter approves a candidate
   - `record_rejection()` — After recruiter rejects a candidate
   - `set_explicit_preference()` — After recruiter states a preference
   - `get_weekly_digest()` — Weekly summary of learning activity
   - All triggers log to `preference_learning_events` table

4. **Preference vector representation:** 1536-dim pgvector for production. MVP stores as JSON string (decoded/encoded via `_decode_vector`/`_encode_vector`). Production implementation would use actual pgvector embeddings.

5. **Preference transparency UI:** `get_implicit_scores()` returns decoded scores as `{dimension: score}` dict. `get_weekly_digest()` returns summary with approvals, rejections, top changes. PreferencePanel UI consumes these endpoints.

6. **Preference override:** `delete_explicit_preference()` removes a single key. `update_explicit_preferences()` replaces specific keys. Implicit scores can be reset by deleting the preference vector.

7. **Preference versioning:** All changes logged to `preference_learning_events` with `features_before`, `features_after`, `preference_delta`. `get_learning_events()` returns event history with optional type filter.

8. **GDPR compliance:** `delete_recruiter_preferences()` deletes preference profile + all learning events. Conversation history and action logs are separate tables (deleted via separate endpoints).

9. **Weekly digest:** `get_weekly_digest()` summarizes past 7 days: approval/rejection counts, explicit update count, top 5 preference dimension changes.

10. **Feature dimensions:** 12 mapped dimensions covering cloud, leadership, startup, finance, healthcare, remote, contract, python, java, javascript, data, devops. Each dimension maps to skill/title keywords for feature extraction.

**API surface:**
- `get_explicit_preferences(db, recruiter_id)` → dict
- `set_explicit_preference(db, recruiter_id, key, value)` → dict
- `update_explicit_preferences(db, recruiter_id, updates)` → dict
- `delete_explicit_preference(db, recruiter_id, key)` → dict
- `record_approval(db, recruiter_id, candidate_id, job_id?, features?)` → implicit_scores
- `record_rejection(db, recruiter_id, candidate_id, job_id?, reason?, features?)` → implicit_scores
- `get_implicit_scores(db, recruiter_id)` → dict[str, float]
- `get_learning_events(db, recruiter_id, limit?, event_type?)` → list[dict]
- `get_weekly_digest(db, recruiter_id)` → dict
- `delete_recruiter_preferences(db, recruiter_id)` → None

**Remaining work:**
- Actual pgvector embedding (currently JSON-stored for MVP)
- Feature extraction from real candidate data (currently returns defaults)
- Outreach style learning (outreach_edit event type — structure defined, not yet triggered)
- Outreach response learning (outreach_response event type — structure defined, not yet triggered)
