# AI-Native Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the 7 AI-native feature sections (4.2.1–4.2.7) from the AI-Native Features spec: resume parsing, AI summaries, job recommendations, AI match/ranking, AI outreach drafting, AI assistant, and the PII Privacy Shield.

**Architecture:** Dedicated AI microservice with its own database, queue, and API. All LLM calls route through the PII Shield (4.2.7) and an LLM Provider Router (OpenAI primary, Anthropic secondary). Results are cached and stored with cost tracking, prompt versioning, and model metadata. The AI service communicates with the core API via internal REST endpoints with mTLS.

**Tech Stack (recommended):** Python 3.12+, FastAPI (AI service), spaCy (NER), Apache Tika (text extraction), OpenAI SDK, Anthropic SDK, Redis (job queue, result cache), JSON Schema validation (pydantic/jsonschema), PostgreSQL (result storage with RLS), Celery or arq (background jobs). Frontend integration via WebSocket events from the core API.

## Global Constraints

- All AI features route through the PII Shield (4.2.7) — no feature sends data directly to an LLM
- All AI result tables include `organization_id UUID NOT NULL FK`, `model VARCHAR(50)`, `prompt_version VARCHAR(20)`, `cost_usd DECIMAL(10,6)`
- Confidence scale: High >= 0.85, Medium 0.50–0.84, Low < 0.50
- All user-controlled text passes through prompt injection sanitization before reaching LLM prompts
- LLM provider failover: OpenAI (primary) → Anthropic (secondary) → cached → graceful degradation
- Token budget per tenant: 500K input tokens/day default; hard cap at 120%; cost alerts at 80%/100%
- Prompt contracts are versioned via `ai_model_versions` registry table
- All AI features use request-scoped token namespaces: `[REQ-{trace_id}-TYPE_N]`
- All AI operations log to `audit_logs` (defined in Core Features spec 4.1.1) with `resource_type='ai_feature'`
- Max input tokens per feature: resume parsing = 30K tokens, summary = 8K tokens, active match = 6K tokens, ranking = 16K tokens (all candidates), outreach draft = 4K tokens, assistant query = 3K tokens. Text exceeding the limit is truncated from the bottom (oldest content first).

---

## Phase 0: AI Service Layer Foundation

**Goal:** Scaffold the AI microservice, implement cross-cutting infrastructure (multi-tenancy, LLM router, cost tracking, model registry, prompt injection defense), and set up the shared data models.

### Task 0.1: AI Service Project Structure

**Files:**
- Create: `ai-service/pyproject.toml`
- Create: `ai-service/app/__init__.py`
- Create: `ai-service/app/main.py`
- Create: `ai-service/app/config.py`
- Create: `ai-service/app/database.py`
- Create: `ai-service/Dockerfile`
- Modify: `docker-compose.yml` (add ai-service)

**Interfaces:**
- Consumes: `app.config.settings` — DATABASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
- Produces: FastAPI app with lifespan, database connection, health check endpoint

- [ ] Step 1: Create `pyproject.toml` with FastAPI, SQLAlchemy async, spaCy, OpenAI SDK, Anthropic SDK, Apache Tika client, pytest
- [ ] Step 2: Create `app/config.py` with pydantic Settings for all AI service environment variables
- [ ] Step 3: Create `app/database.py` with async engine and session factory (separate from core API database or shared)
- [ ] Step 4: Create `app/main.py` with FastAPI factory, CORS, health check at `GET /internal/v1/health`
- [ ] Step 5: Create Dockerfile and add ai-service to docker-compose.yml
- [ ] Step 6: Write test verifying health endpoint returns 200

### Task 0.2: AI Service Multi-Tenancy Middleware

**Files:**
- Create: `ai-service/app/middleware/__init__.py`
- Create: `ai-service/app/middleware/tenant.py`
- Create: `ai-service/app/middleware/error_handler.py`

**Interfaces:**
- Consumes: app.config, internal request headers
- Produces: Tenant context extraction from `X-Organization-ID` header, error envelope matching core API format

- [ ] Step 1: Create tenant middleware that extracts `X-Organization-ID` and `X-User-ID` headers and stores them in request state
- [ ] Step 2: Create error handler matching the core API error envelope format
- [ ] Step 3: Verify tenant context is propagated through all request paths

### Task 0.3: LLM Provider Router

**Files:**
- Create: `ai-service/app/llm/__init__.py`
- Create: `ai-service/app/llm/router.py`
- Create: `ai-service/app/llm/providers/openai.py`
- Create: `ai-service/app/llm/providers/anthropic.py`
- Create: `ai-service/app/llm/providers/__init__.py`

**Interfaces:**
- Consumes: Provider API keys from config
- Produces: `LLMRouter.complete(prompt, model, feature) → { content, model_used, cost_usd, prompt_version }` with automatic failover

- [ ] Step 1: Implement OpenAI provider wrapper — `call_openai(prompt, model, tenant_id) → { content, usage }`
- [ ] Step 2: Implement Anthropic provider wrapper — `call_anthropic(prompt, model, tenant_id) → { content, usage }`
- [ ] Step 3: Implement `LLMRouter` class — primary=OpenAI → secondary=Anthropic → cache → graceful degradation
- [ ] Step 4: Before each LLM call, look up the pinned model version from `ai_model_versions` registry; use only the pinned version (e.g., `openai/gpt-4o-2026-05-13`, `anthropic/claude-3.5-sonnet-2026-06-01`). Version upgrades are explicit config changes, not automatic.
- [ ] Step 5: Implement health check — track per-provider error rate over 60s window, failover on 3 consecutive failures
- [ ] Step 6: Implement rollback/recovery — re-test primary provider every 60s; restore traffic after 2 consecutive healthy checks
- [ ] Step 7: Implement per-region routing — EU tenants route LLM calls to EU-based provider endpoints; non-EU tenants use default endpoints
- [ ] Step 8: Implement cost calculation — track tokens used, multiply by per-model rate, return cost_usd
- [ ] Step 9: Implement rate limit awareness — switch providers early if primary approaching per-minute limit
- [ ] Step 10: Write tests for failover on timeout, rollback recovery cadence, per-region routing, model version pinning, cost calculation

### Task 0.4: Model Registry & Prompt Versioning

**Files:**
- Create: `ai-service/app/models/__init__.py`
- Create: `ai-service/app/models/ai_model_version.py`
- Create: `ai-service/app/services/prompt_registry.py`
- Create: `ai-service/db/versions/001_initial.py`

**Interfaces:**
- Consumes: database session
- Produces: `ai_model_versions` table model, `PromptRegistry.get_version(feature, model) → prompt_text, version_hash`

- [ ] Step 1: Define `AiModelVersion` model — model_name, version, active_from, prompt_version, prompt_hash
- [ ] Step 2: Create initial Alembic migration for the AI service database
- [ ] Step 3: Implement `PromptRegistry` — stores prompt contracts keyed by `(feature, version)`, returns prompt text + version hash
- [ ] Step 4: Seed the registry with initial model versions (`openai/gpt-4o-2026-05-13`, `anthropic/claude-3.5-sonnet-2026-06-01`) and prompt contracts from spec sections 4.2.1–4.2.6
- [ ] Step 5: Write tests for version lookup and hash generation

### Task 0.5: Prompt Injection Defense & Response Validation

**Files:**
- Create: `ai-service/app/services/sanitizer.py`
- Create: `ai-service/app/services/response_validator.py`

**Interfaces:**
- Consumes: raw user input, LLM response string, JSON schema
- Produces: `sanitize_input(text) → str` (clean), `validate_response(response, schema) → dict` (validated + parsed)

- [ ] Step 1: Implement `sanitize_input()` — strip prompt-injection patterns (ignore previous instructions, system prompt, forget), wrap in delimiters, prepend system guard
- [ ] Step 2: Implement `validate_response()` — parse LLM response as JSON, validate against a pydantic model or JSON Schema, retry once on failure
- [ ] Step 3: Implement provider response normalization — normalize OpenAI vs Anthropic output format differences to a single internal schema before validation
- [ ] Step 4: Define reusable JSON schemas for each feature (parse result, summary, match scores, ranking array, draft content, query intent)
- [ ] Step 5: Write tests for injection pattern detection, malformed JSON handling, schema validation, provider normalization

---

## Phase 1: PII Privacy Shield Middleware (4.2.7)

**Dependencies:** Phase 0 complete (AI service foundation, LLM router)
**Provides:** PII redaction, token map, re-hydration, side-by-side verification, review queue, audit logging

### Task 1.1: PII Shield Core

**Files:**
- Create: `ai-service/app/shield/__init__.py`
- Create: `ai-service/app/shield/ner.py`
- Create: `ai-service/app/shield/regex_patterns.py`
- Create: `ai-service/app/shield/anonymizer.py`
- Create: `ai-service/app/shield/token_map.py`

**Interfaces:**
- Consumes: `app.config.settings` (NER model path, confidence thresholds)
- Produces: `ShieldService.redact(text, tenant_id) → { anonymized, token_map, entities_found }`, `ShieldService.rehydrate(response, token_map) → str`

- [ ] Step 1: Implement NER engine — wrap spaCy `en_core_web_trf` with per-language model fallback; extract entities: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, STREET_ADDRESS, DATE_OF_BIRTH, CREDIT_CARD, SSN, PASSPORT, DRIVERS_LICENSE, BANK_ACCOUNT
- [ ] Step 2: Implement regex pattern layer — SSN, passport, UK NI numbers, EU passport formats, Canadian SIN
- [ ] Step 3: Implement Scunthorpe resolution — if NER confidence > threshold AND regex match exists → trust NER; if NER confidence < threshold AND regex match → flag for manual review
- [ ] Step 4: Implement `TokenMap` — request-scoped namespace `[REQ-{trace_id}-TYPE_N]`, 30s TTL, auto-cleanup, per-request isolation; enforce 100-entry limit per payload (return error "Payload too complex — split into smaller segments" if exceeded)
- [ ] Step 5: Implement anonymizer — replace detected PII with tokens from TokenMap
- [ ] Step 6: Implement re-hydrator — replace tokens with original values in LLM responses
- [ ] Step 7: Implement language detection — detect text language, select appropriate NER model, fall back with confidence penalty
- [ ] Step 8: Write tests — "Sarah Chen email sarah@example.com" → "[REQ-abc-NAME_1] email [REQ-abc-EMAIL_1]", concurrent non-colliding namespaces

### Task 1.2: Shield Internal API

**Files:**
- Create: `ai-service/app/routes/__init__.py`
- Create: `ai-service/app/routes/shield.py`
- Create: `ai-service/app/schemas/__init__.py`
- Create: `ai-service/app/schemas/shield.py`

**Interfaces:**
- Consumes: `ShieldService`, database session
- Produces: `POST /internal/v1/shield/redact`, `POST /internal/v1/shield/rehydrate`, `POST /internal/v1/shield/verify`, `GET /internal/v1/shield/health`; all accept `X-Organization-ID`, `X-Trace-ID`, and `X-User-ID` headers

- [ ] Step 1: Implement `POST /internal/v1/shield/redact` — input → anonymized_output + token_map + entities_found
- [ ] Step 2: Implement `POST /internal/v1/shield/rehydrate` — anonymized_response + token_map → re-hydrated_output
- [ ] Step 3: Implement `POST /internal/v1/shield/verify` — return both original and redacted text for UI comparison
- [ ] Step 4: Implement `GET /internal/v1/shield/health` — NER model loaded, confidence threshold check
- [ ] Step 5: Write integration tests for the complete shield pipeline (redact → rehydrate → verify)

### Task 1.3: Shield Data Models (Audit Log & Review Queue)

**Files:**
- Create: `ai-service/app/models/redaction_audit_log.py`
- Create: `ai-service/app/models/redaction_review_queue.py`

**Interfaces:**
- Consumes: database session, `ShieldService` results
- Produces: `RedactionAuditLog` model (append-only, no PII), `RedactionReviewQueue` model (encrypted PII, 90d retention)

- [ ] Step 1: Define `RedactionAuditLog` model — organization_id, trace_id, feature, input_length_chars, pii_entities_found (entity types + counts, no values), pii_entity_types, language, redaction_success, false_positive_flags; append-only
- [ ] Step 2: Define `RedactionReviewQueue` model — organization_id, trace_id, original_text (encrypted AES-256-GCM), redacted_text, low_confidence_entities JSONB, status, reviewed_by, reviewed_at; 90d hard-delete
- [ ] Step 3: Create Alembic migration for both tables
- [ ] Step 4: Wire audit logging into the shield endpoints — log every redact + rehydrate call
- [ ] Step 5: Wire review queue — move payloads below confidence threshold to review queue instead of returning to caller
- [ ] Step 6: Write tests for audit log content (no PII values stored), review queue lifecycle

### Task 1.4: Shield Business Logic & Configuration

**Files:**
- Modify: `ai-service/app/config.py`
- Create: `ai-service/app/shield/config.py`

**Interfaces:**
- Consumes: Shield models, NER engine
- Produces: Shield configuration (per-tenant thresholds, entity tracking, false positive feedback)

- [ ] Step 1: Add per-tenant shield config — EU tenants use 0.95 NER threshold, others 0.85
- [ ] Step 2: Implement circuit breaker — fail-closed on shield unavailability, return 503 with "PII protection service unavailable"
- [ ] Step 3: Implement rate limiting — 100 req/s per tenant to shield endpoints
- [ ] Step 4: Implement false positive feedback — UI calls endpoint to log FP, periodic batch fine-tuning (deferred, schema only in v1)
- [ ] Step 5: Write tests for circuit breaker behavior, rate limit enforcement

---

## Phase 2: Resume Parsing & Profile Normalization (4.2.1)

**Dependencies:** Phase 1 complete (PII Shield v1), Core Features Phase 2 (Candidate Management)
**Provides:** Resume text extraction, LLM parsing, title normalization, hallucination detection, parsing job management

### Task 2.1: Text Extraction & Normalization Service

**Files:**
- Create: `ai-service/app/services/text_extractor.py`
- Create: `ai-service/app/services/title_normalizer.py`
- Create: `ai-service/app/models/parsing_job.py`
- Create: `ai-service/app/models/title_synonym.py`

**Interfaces:**
- Consumes: File bytes, `ShieldService`, `LLMRouter`, `PromptRegistry`
- Produces: `ParsingJob` model (with cost_usd, model, prompt_version), `TitleSynonym` model, `extract_text(file_bytes) → str`, `normalize_title(raw_title, org_id) → normalized_title`

- [ ] Step 1: Define `ParsingJob` model — organization_id, candidate_id, document_id, status, parsed_data JSONB, normalized_data JSONB, raw_text TEXT, confidence_score, model, prompt_version, cost_usd, processing_time_ms, language; raw_text cleared by cleanup job after 24h, never persisted in production beyond this window
- [ ] Step 2: Define `TitleSynonym` model — organization_id, raw_pattern, normalized_title, is_global, created_by
- [ ] Step 3: Implement `extract_text()` — Apache Tika for PDF/DOCX/TXT, handle scanned PDFs (no text layer → error)
- [ ] Step 4: Implement `normalize_title()` — lookup in title_synonyms (org-specific first, then global), fuzzy match on raw_pattern
- [ ] Step 5: Implement language detection before PII shield — detect language via fastText or langdetect
- [ ] Step 6: Implement scheduled cleanup job — delete/clear raw_text for parsing_jobs older than 24h (cron daily)
- [ ] Step 7: Create Alembic migration for parsing_jobs and title_synonyms
- [ ] Step 8: Write tests for text extraction, title normalization

### Task 2.2: LLM Parse & Hallucination Detection

**Files:**
- Create: `ai-service/app/services/parse_service.py`
- Create: `ai-service/app/services/hallucination_detector.py`

**Interfaces:**
- Consumes: `LLMRouter`, `ShieldService`, `PromptRegistry`, `ParsingJob` model
- Produces: `run_parse(document_text, language, org_id) → { parsed_data, normalized_data, confidence_score, hallucination_warnings }`

- [ ] Step 1: Build the parse prompt — load from `PromptRegistry` (feature='resume_parse'), inject language tag and anonymized resume text
- [ ] Step 2: Implement `run_parse()` flow — extract text → detect language → PII shield redact → LLM call → validate JSON → re-hydrate → normalize → detect hallucinations → store
- [ ] Step 3: Implement confidence score — weighted formula: critical fields (name, work_history≥1, skills≥1) weighted 3x, important (email, phone, education) 2x, optional (certifications, salary) 1x
- [ ] Step 4: Implement `HallucinationDetector` — extract key entities from raw text using regex/keyword extraction, compare against LLM-parsed entities, flag unsupported ones with confidence penalty (-0.05 each)
- [ ] Step 5: Implement idempotency — compute SHA-256 of document bytes, skip if identical document parsed within 24h
- [ ] Step 6: Implement re-parse diff merge — patch key-level merge into existing parsed_data JSONB
- [ ] Step 7: Write tests for hallucination detection, confidence score calculation, idempotency

### Task 2.3: Parse API Endpoints & Background Job

**Files:**
- Create: `ai-service/app/routes/parse.py`
- Create: `ai-service/app/schemas/parse.py`
- Create: `ai-service/app/workers/__init__.py`
- Create: `ai-service/app/workers/parse_worker.py`

**Interfaces:**
- Consumes: `ParseService`, `AIJobQueue`
- Produces: `POST /api/v1/candidates/:id/parse` (triggers async job), `GET /api/v1/parse/:candidateId/status`, parse worker

- [ ] Step 1: Implement `POST /api/v1/candidates/:id/parse` — accept document, enqueue parse job, return job_id. Supports both initial parse (new candidate) and re-parse (existing candidate with updated document).
- [ ] Step 2: Implement `GET /api/v1/parse/:candidateId/status` — return status, confidence_score, error
- [ ] Step 3: Implement parse worker — consume queue, call `run_parse()`, store results, emit WebSocket event on complete
- [ ] Step 4: Implement retry logic — 3x exponential backoff on LLM failure, then mark failed
- [ ] Step 5: Write integration test for upload → parse → complete flow with mock LLM

---

## Phase 3: AI-Generated Candidate Profile Summaries (4.2.2)

**Dependencies:** Phase 0 (LLM router, shield), Core Features Phase 2 (Candidate Management with `is_ai_summary_edited` column)
**Provides:** AI summary generation, regeneration, flagging, summary_flags storage

### Task 3.1: Summary Service

**Files:**
- Create: `ai-service/app/services/summary_service.py`
- Create: `ai-service/app/routes/summaries.py`
- Create: `ai-service/app/schemas/summary.py`
- Create: `ai-service/app/models/summary_flag.py`

**Interfaces:**
- Consumes: `LLMRouter`, `ShieldService`, `PromptRegistry`
- Produces: `GET /api/v1/candidates/:id/summary` (read current AI summary), `POST /api/v1/candidates/:id/summary/regenerate`, `POST /api/v1/candidates/:id/summary/flag`, `PUT /api/v1/candidates/:id/summary` (recruiter edit), `SummaryFlag` model

- [ ] Step 1: Define `SummaryFlag` model — organization_id, candidate_id, flagged_by (user or candidate), reason, status (open, reviewed, dismissed), resolution_note, resolved_at
- [ ] Step 2: Implement `GET /api/v1/candidates/:id/summary` — return `ai_summary`, `ai_summary_generated_at`, `is_ai_summary_edited` from the candidates table
- [ ] Step 3: Implement summary generation prompt — load from PromptRegistry (feature='candidate_summary'), inject skills/work_history/education
- [ ] Step 4: Implement candidate-facing variant — second-person voice, AI disclosure, flagging link
- [ ] Step 5: Implement summary regeneration — check `is_ai_summary_edited` flag, skip if recruiter edited (unless explicitly requested)
- [ ] Step 6: Implement rate limiting — 5 regenerations per candidate per hour
- [ ] Step 7: Implement incomplete profile guard — if < 2 of (work≥1, skills≥3, education≥1), return message instead of generating
- [ ] Step 8: Create Alembic migration for summary_flags
- [ ] Step 9: Wire `POST /summary/flag` to create SummaryFlag record and send admin notification
- [ ] Step 10: Write tests for summary GET, generation, rate limiting, profile guard, flag creation

### Task 3.2: Profile Change Event Integration

**Files:**
- Create: `ai-service/app/services/event_subscriber.py`

**Interfaces:**
- Consumes: Profile update events (via message queue or webhook)
- Produces: Auto-triggered summary regeneration on profile changes

- [ ] Step 1: Subscribe to candidate profile change events (resume uploaded, profile edited, skills changed)
- [ ] Step 2: Implement event handler — check conditions, regenerate summary asynchronously
- [ ] Step 3: Write test for event-triggered regeneration

---

## Phase 4: AI-Driven Job Recommendations (4.2.3)

**Dependencies:** Phase 0 (LLM router, shield), Core Features Phase 2 (Candidates) + Phase 3 (Requisitions)
**Provides:** Pre-computed passive recommendations (nightly + incremental), on-demand active matching, interest expression

### Task 4.1: Recommendation Models & Pre-Computation

**Files:**
- Create: `ai-service/app/models/job_recommendation.py`
- Create: `ai-service/app/services/recommendation_service.py`
- Create: `ai-service/app/workers/recommendation_worker.py`

**Interfaces:**
- Consumes: `LLMRouter`, `ShieldService`, `PromptRegistry`, candidate + requisition data
- Produces: `JobRecommendation` model, scheduled passive recompute, incremental update, active match

- [ ] Step 1: Define `JobRecommendation` model — organization_id, candidate_id FK, requisition_id FK, type (passive/active), fit_score, fit_data JSONB (normalized schema), candidate_expressed_interest, expressed_at, model, prompt_version, cost_usd, computed_at; unique on (candidate_id, requisition_id, type)
- [ ] Step 2: Implement active match — compare one candidate + one requisition via LLM, store with type='active', cache 24h
- [ ] Step 3: Implement passive full recompute worker — nightly at 2:00 AM tenant-local time, compare all complete profiles (skills ≥ 1, work_history ≥ 1, education ≥ 1) against open requisitions; exclude candidates already submitted or rejected from those requisitions
- [ ] Step 4: Implement incremental update — on candidate profile change, re-compute recommendations for that single candidate
- [ ] Step 5: Implement requisition change handler — on requisition open/close/skill change, re-compute for affected candidates; on requisition close/fill, mark all recommendations for that requisition as inactive and send notification to candidates who expressed interest
- [ ] Step 6: Create Alembic migration
- [ ] Step 7: Add tie-breaking for equal fit scores: sort by `computed_at` descending (most recently computed first)
- [ ] Step 8: Write tests for active match, pre-computed recommendation freshness, exclusion of already-submitted candidates, tie-breaking

### Task 4.2: Recommendation & Interest API

**Files:**
- Create: `ai-service/app/routes/recommendations.py`
- Create: `ai-service/app/schemas/recommendation.py`

**Interfaces:**
- Consumes: `JobRecommendation` model, activity service
- Produces: `GET /api/v1/candidates/:id/recommendations` (reads pre-computed, < 200ms), `POST /api/v1/match/compare`, `POST /api/v1/recommendations/:id/express-interest`

- [ ] Step 1: Implement `GET /api/v1/candidates/:id/recommendations` — read from job_recommendations table, return top 5 (for candidate portal)
- [ ] Step 2: Implement `GET /api/v1/requisitions/:id/recommended-candidates` — recruiter-facing view of candidates ranked for a job, returns array of `{ candidate_id, fit_score, skill_match: { matched, missing }, gap_analysis, recommendation }` sorted by fit_score descending
- [ ] Step 3: Implement `POST /api/v1/match/compare` — on-demand LLM comparison, cache 24h
- [ ] Step 4: Implement `POST /api/v1/recommendations/:id/express-interest` — set expressed_interest=true, create activity event, notify recruiter (WebSocket + in-app)
- [ ] Step 5: Write integration tests for pre-computed reads, active match, interest expression

---

## Phase 5: AI Match Support & Ranking (4.2.4)

**Dependencies:** Phase 0 (LLM router, shield), Core Features Phase 4 (Shortlists)
**Provides:** AI ranking of shortlisted candidates, chunked batch processing, skill-count fallback, override detection

### Task 5.1: Ranking Service

**Files:**
- Create: `ai-service/app/services/ranking_service.py`
- Create: `ai-service/app/routes/ranking.py`
- Create: `ai-service/app/schemas/ranking.py`

**Interfaces:**
- Consumes: `LLMRouter`, `ShieldService`, `PromptRegistry`, shortlist data
- Produces: `POST /api/v1/requisitions/:id/rank` → ranked array; `GET /api/v1/shortlists/:id/rankings` → current AI rankings; fallback scoring; override tracking; low-fit warning

- [ ] Step 1: Implement ranking prompt — load from PromptRegistry (feature='candidate_ranking'), inject job context and anonymized candidate profiles
- [ ] Step 2: Implement chunked processing — batch candidates in groups of 10, merge and normalize scores across chunks
- [ ] Step 3: Implement skill-count fallback — if LLM unavailable, rank by `matched_required_skills * 3 + matched_preferred_skills * 1.5 + experience_years * 0.5`
- [ ] Step 4: Implement ranking API — `POST /api/v1/requisitions/:id/rank` → validate: max 50 candidates, update ai_rank on shortlist_candidates
- [ ] Step 5: Implement `GET /api/v1/shortlists/:id/rankings` — return current AI rankings as array of `{ shortlist_candidate_id, candidate_id, ai_rank, fit_score, skill_match, strengths, concerns, recommendation }` ordered by ai_rank; include low-fit warning (`"fit_score < 50: This candidate may not be a strong match"`) for any candidate with fit_score < 50
- [ ] Step 6: Implement override detection — if a recruiter's override rate > 80% in 30 days, trigger admin notification
- [ ] Step 7: Write tests for chunked ranking with score merge, fallback scoring, low-fit warning, override rate tracking

---

## Phase 6: AI Outreach Assistance (4.2.5)

**Dependencies:** Phase 0 (LLM router, shield), Core Features Phase 5 (CRM templates, activities, opt-out)
**Provides:** Draft generation, variant creation, sequence suggestion, refinement, hallucination detection

### Task 6.1: Outreach Drafting Service

**Files:**
- Create: `ai-service/app/services/outreach_service.py`
- Create: `ai-service/app/routes/outreach.py`
- Create: `ai-service/app/schemas/outreach.py`

**Interfaces:**
- Consumes: `LLMRouter`, `ShieldService`, `PromptRegistry`, template + candidate data, opt-out check
- Produces: `POST /api/v1/outreach/draft`, `POST /api/v1/outreach/draft/variants`, `POST /api/v1/outreach/suggest-sequence`, `POST /api/v1/outreach/refine`

- [ ] Step 1: Implement opt-out check — before generating, query activities table for `opt_out` for this candidate; block with 403 if found
- [ ] Step 2: Implement draft generation prompt — load from PromptRegistry (feature='outreach_draft'), inject template, candidate context, job context
- [ ] Step 3: Implement variant generation — call LLM with different temperature/tone instructions, return 2-3 variants
- [ ] Step 4: Implement refinement — pass existing draft + natural language instruction to LLM for modification
- [ ] Step 5: Implement sequence suggestion — load from PromptRegistry (feature='sequence_suggest'), inject job type; return 3-step sequence
- [ ] Step 6: Implement deduplication — if same recruiter + candidate + job + template in last 5min, return cached draft
- [ ] Step 7: Rate limit — 30 generations per user per hour
- [ ] Step 8: Wire hallucination detection (from Task 2.2) on draft content before returning
- [ ] Step 9: Note: drafts are ephemeral — returned in response body only, not persisted to database
- [ ] Step 10: Write tests for draft generation, variant switching, opt-out blocking, refinement

---

## Phase 7: AI Assistant for Recruiters (4.2.6)

**Dependencies:** Phase 0 (LLM router, shield), Core Features Phase 7 (Search API)
**Provides:** Natural language query interpretation, structured search execution, conversation context, suggestion chips

### Task 7.1: Assistant Service

**Files:**
- Create: `ai-service/app/services/assistant_service.py`
- Create: `ai-service/app/routes/assistant.py`
- Create: `ai-service/app/schemas/assistant.py`

**Interfaces:**
- Consumes: `LLMRouter`, `ShieldService`, `PromptRegistry`, search API (via internal HTTP), conversation context store (Redis)
- Produces: `POST /api/v1/assistant/query` → interpreted response + suggested actions; `POST /api/v1/assistant/suggest`

- [ ] Step 1: Implement assistant prompt — load from PromptRegistry (feature='assistant_query'), inject available filter fields, conversation context
- [ ] Step 2: Implement conversation context store — Redis hash per user session, TTL 30min (max 1 hour total), stores message history + last parsed intent
- [ ] Step 3: Implement query interpretation — call LLM to parse intent → search_params JSON, pass to search API via internal call
- [ ] Step 4: Implement ambiguous intent resolution — if LLM returns `ambiguous=true`, return disambiguation prompt instead of executing
- [ ] Step 5: Implement follow-up context — append follow-up queries to conversation history, use last result set
- [ ] Step 6: Implement suggestion chips — based on current pipeline state (stale requisitions, recent submissions, etc.), generate 3-5 suggestions
- [ ] Step 7: Implement aggregate query support — when LLM detects count/aggregation intent, call search API's `_meta` endpoint for count-only results
- [ ] Step 8: Implement read-only enforcement — assistant endpoint calls search API with a read-only service account (SELECT-only DB privileges)
- [ ] Step 9: Write tests for query interpretation, follow-up context, ambiguous intent, aggregate queries, read-only enforcement
- [ ] Step 10: Write integration test for full flow: "Show me React developers in SF" → search → formatted response → "What are their skills?" → context-aware follow-up
