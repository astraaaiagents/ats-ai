# Design: AI-Native Agency ATS

**Date:** 2026-07-21  
**Status:** Approved  
**Source PRDs:** `ats-ai.md`, `ATS PRD pplx.md`, `gemini-AI_Native_Agency_ATS_PRD.md`, `deepseek-ats-ai.md` (final)  
**Approach:** Foundation-First Parallelism (Approach A)  
**Team:** 2-4 developers  
**Timeline:** 6 months to GA  
**Infrastructure:** AWS (managed cloud)

---

## 1. System Architecture & Workstream Decomposition

### Architecture Overview

```
                    +----------------─────────────────────────+
                    |           AWS Infrastructure             |
                    |                                          |
  +---------+      |  +----------+  +----------+  +--------+ |
  |  Web    |------>|  |  API     |  |  AI      |  |  Redis | |
  |  Client |      |  |  Gateway |  |  Service |  | /Queue | |
  | (Next.js)     |  |  (Next.js |  | (Node.js |  |        | |
  +---------+      |  |  Routes) |  |  Service)|  +--------+ |
                    |  +----+-----+  +----+-----+      |        |
                    |       |            |              |        |
                    |  +----v------------v--------------v----+   |
                    |  |        PostgreSQL (RDS)              |   |
                    |  |  +----------+ +--------------+       |   |
                    |  |  |  Core    | |   pgvector   |       |   |
                    |  |  |  Tables  | | (semantic    |       |   |
                    |  |  |          | |  search)     |       |   |
                    |  |  +----------+ +--------------+       |   |
                    |  +--------------------------------------+   |
                    |                                          |
                    |  +----------+  +----------+              |
                    |  |   S3     |  |  Cloud   |              |
                    |  |(tenant   |  |  Watcher |              |
                    |  | isolated)|  |  + Logs  |              |
                    |  +----------+  +----------+              |
                    +------------------------------------------+

  Workstream Mapping:
  +------------------------------------------------------------+
  |  WS1: Core ATS        |  API Gateway + Core Tables + S3    |
  |  WS2: AI Features     |  AI Service + Redis Queue          |
  |  WS3: Portals & CRM   |  Web Client + Email/Calendar APIs  |
  +------------------------------------------------------------+
```

### Workstream Boundaries & Contracts

| Workstream | Owns | Depends On | API Contract |
|------------|------|------------|--------------|
| **WS1: Core ATS** | Candidate, Job, Pipeline, Submission entities | Auth, multi-tenant DB, S3 | RESTful CRUD + search endpoints |
| **WS2: AI Features** | Parsing, matching, summarization, outreach | WS1 data (read-only via API), AI providers | Async job queue (enqueue -> poll for result) |
| **WS3: Portals & CRM** | Candidate portal, client portal, CRM, email sync | WS1 data (read via API), email/calendar APIs | Server-side rendered pages + webhook handlers |

### Key Design Decisions

- **Monorepo** (Turborepo or Nx): Shared TypeScript types between frontend, API, and AI service. Reduces version drift for a small team.
- **API Gateway pattern**: All client requests go through Next.js API routes. WS2 (AI) communicates via Redis job queue, not direct HTTP calls.
- **Server-side rendering for portals**: Candidate and client portals use Next.js SSR for fast, SEO-friendly pages with session-based auth.
- **AI service is async**: All AI operations are queued (Redis/BullMQ). The UI polls for completion. This keeps the UI responsive and allows batch processing.

---

## 2. Data Model & Multi-Tenancy

### Core Entities

```
+---------------------------------------------------------------------+
|                         TENANT (Agency)                             |
|  id, name, domain, plan, region, settings, created_at               |
+-----+---------------------------------------------------------------+
      |
      +---------------+---------------+---------------+
      v               v               v               v
+-----------+   +-----------+   +-----------+   +-----------+
|   USER    |   | CANDIDATE |   |   JOB     |   |   CLIENT  |
| (Agency   |   | (Profile +|   | (Requisition|  | (Organization|
|  member)  |   |  Resume)  |   |  )        |   |  Contact)  |
+-----------+   +-----------+   +-----------+   +-----------+
| id        |   | id        |   | id        |   | id        |
| tenant_id*|   | tenant_id*|   | tenant_id*|   | tenant_id*|
| email     |   | email     |   | client_id |   | name      |
| role      |   | first_name|   | title     |   | contact_nm|
| rbac_roles|   | last_name |   | desc      |   | email     |
| avatar_url|   | phone     |   | skills[]  |   | phone     |
| created_at|   | company   |   | location  |   | address   |
+-----------+   | salary_range|   | comp_range|   +-----------+
                | visa_status|   | urgency   |           |
                | ...        |   | ...       |           +-----------+
                +-----------+   +-----------+           | JOB_STAGE |
                                                        | (configurable)|
                                                        +-----------+
                                                        | id        |
                                                        | job_id    |
                                                        | name      |
                                                        | order     |
                                                        +-----------+
      |                                                  |
      |                                                  |
      v                                                  v
+---------------------------------------------------------------------+
|                        APPLICATION (Candidate <-> Job)              |
|  id, candidate_id, job_id, status, source, applied_at, ai_match_score|
+-----+---------------------------------------------------------------+
      |
      +---------------+---------------+
      v               v               v
+-----------+   +-----------+   +-----------+
|  SUBMISSION|  |  ACTIVITY  |  |  OUTREACH  |
| (Shortlist |  |  TIMELINE  |  | (CRM       |
|  Package)  |  | (All events)| |  sequence) |
+-----------+   +-----------+   +-----------+
| id        |   | id        |   | id        |
| job_id    |   | candidate_id| | candidate_id|
| candidates|   | job_id    |   | job_id    |
| notes     |   | type      |   | template_id|
| client_view|  | data (JSON)| | subject   |
| status    |   | occurred_at| | sent_at   |
| created_at|   | created_by | | response  |
+-----------+   +-----------+   +-----------+
```

### Multi-Tenancy Strategy

**Row-Level Security (RLS) on PostgreSQL** - the primary isolation mechanism:

```sql
-- Every query-enforced tenant boundary
CREATE POLICY tenant_isolation ON candidates
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Every table has tenant_id as a NOT NULL column with foreign key
-- to tenants table. No query can access another tenant's data.
```

**Storage isolation:** S3 buckets use tenant-prefixed paths:
```
s3://ats-storage/{tenant_id}/candidates/{candidate_id}/resumes/
s3://ats-storage/{tenant_id}/submissions/{submission_id}/packages/
```

**Encryption:** AES-256 at rest (RDS encrypted), KMS keys per tenant for S3. TLS 1.3 in transit.

### AI-Specific Tables

```
+---------------------------------------------------------------------+
|                     AI AUDIT LOG (Immutable)                        |
|  id, tenant_id, candidate_id, job_id, user_id,                      |
|  operation (parse|match|summarize|outreach),                        |
|  input_tokens, output_tokens, model, latency_ms,                    |
|  prompt_hash (not raw prompt - hashed for privacy),                 |
|  output_hash, status, created_at                                    |
+---------------------------------------------------------------------+

+---------------------------------------------------------------------+
|                   AI MATCH RESULT                                   |
|  id, candidate_id, job_id, ai_score (0-100),                        |
|  fit_signals (JSON: skills_match, experience_match, ...),           |
|  gap_analysis (JSON: missing_skills, recommended_training, ...),    |
|  recruiter_approved (boolean), recruiter_override (JSON),           |
|  override_reason, created_at                                        |
+---------------------------------------------------------------------+
```

### Key Design Decisions

- **tenant_id on every table**: Non-nullable, foreign-keyed. RLS enforces it at the database level.
- **Pseudonymized AI logs**: AI audit logs store hashed prompts (not raw text) to support GDPR "Right to be Forgotten" while maintaining EU AI Act traceability. Candidate IDs are preserved for cross-referencing.
- **Configurable pipeline stages**: Each job/requisition has configurable stages (not hardcoded). This allows different clients to have different workflows.
- **Activity timeline as JSON**: All events (calls, emails, status changes, AI actions) stored in a single `activities` table with a `type` discriminator and JSON `data` payload. This gives flexibility for new event types without schema changes.

---

## 3. AI Middleware & PII Privacy Shield

### PII Privacy Shield Architecture

```
                    +---------------------------------------------+
                    |         AI Service (WS2)                    |
                    |                                             |
  +---------+      |  +-----------------------------------------+|
  |  UI /   |------>|  |  Job Queue (Redis/BullMQ)              ||
  |  API    |      |  |  { type: 'parse'|'match'|'summarize',   ||
  |  (WS1/3)|<------|  |   payload: { job_id, candidate_id },   ||
  +---------+      |  |   callback_url }                        ||
                    |  +-----------+-----------------------------+|
                    |              |                              |
                    |  +-----------v-----------------------------+|
                    |  |        PII Redaction Layer               ||
                    |  |                                          ||
                    |  |  1. NER (spaCy / custom model)           ||
                    |  |  2. Regex patterns (email, phone, SSN...) ||
                    |  |  3. Contextual token replacement          ||
                    |  |     "John Doe" -> [CAND_001_NAME]          ||
                    |  |     "john@example.com" -> [CAND_001_EMAIL] ||
                    |  +-----------+-----------------------------+|
                    |              |                              |
                    |  +-----------v-----------------------------+|
                    |  |     External LLM API Call                ||
                    |  |     OpenAI GPT-4o / Anthropic Claude     ||
                    |  |     Enterprise ZDR agreement             ||
                    |  +-----------+-----------------------------+|
                    |              |                              |
                    |  +-----------v-----------------------------+|
                    |  |     Token Re-hydration Layer             ||
                    |  |     [CAND_001_NAME] -> "John Doe"         ||
                    |  |     (only where output needs PII)         ||
                    |  +-----------+-----------------------------+|
                    |              |                              |
                    |  +-----------v-----------------------------+|
                    |  |     Audit Logger                         ||
                    |  |     Hash prompt/output, store metadata   ||
                    |  |     Log to ai_audit_logs table           ||
                    |  +-----------------------------------------+|
                    +---------------------------------------------+
```

### Operation Types & Prompts

| Operation | Input | Output | PII Handling |
|-----------|-------|--------|--------------|
| **parse** | Raw resume text/PDF | Structured JSON (name, skills, experience, education) | PII extracted -> stored in candidate profile; redacted before LLM |
| **match** | Candidate profile + job req | Fit score, fit signals, gap analysis | Both PII-redacted; score is numeric, no PII in output |
| **summarize** | Candidate profile | Recruiter-friendly summary, strengths | PII-redacted input; PII-rehydrated output for recruiter view |
| **outreach** | Candidate profile + job req | Personalized email draft | PII-rehydrated (needs candidate name, job title) |

### Provider Abstraction

```typescript
// Common interface - swap providers without changing business logic
interface AIProvider {
  parseResume(input: ResumeInput): Promise<StructuredProfile>;
  matchCandidate(input: MatchInput): Promise<MatchResult>;
  summarizeProfile(input: SummaryInput): Promise<string>;
  draftOutreach(input: OutreachInput): Promise<EmailDraft>;
}

// Configuration-driven provider selection per tenant
const providers: Record<string, AIProvider> = {
  openai: new OpenAIProvider(process.env.OPENAI_API_KEY),
  anthropic: new AnthropicProvider(process.env.ANTHROPIC_API_KEY),
};

// Tenant-level provider preference + fallback
async function callAI(operation: string, input: unknown, tenantId: string) {
  const tenant = await getTenantConfig(tenantId);
  const primary = providers[tenant.ai_provider];
  const fallback = providers[tenant.ai_provider_fallback];
  // Retry with fallback on failure
}
```

### Key Design Decisions

- **Async-only AI operations**: No synchronous LLM calls in the request path. All AI operations are queued and processed in the background. The UI polls for completion or uses WebSocket/SSE for real-time updates.
- **Hashed prompt storage**: Raw prompts are never stored. Only SHA-256 hashes are logged for audit. This satisfies EU AI Act traceability while protecting candidate privacy.
- **Side-by-side verification UI**: Recruiters see the original resume and the parsed result side-by-side. They can edit and correct the parsed data. This mitigates the "Scunthorpe problem" (false PII redaction).
- **Confidence scores**: Every AI output includes a confidence score (0-100). Low-confidence outputs are visually flagged in the UI and require explicit recruiter acknowledgment.
- **Graceful degradation**: If all AI providers are unavailable, the system degrades gracefully - the UI shows "AI temporarily unavailable" and allows manual entry. No feature is completely blocked.

---

## 4. Core ATS Features (Workstream 1)

### Feature Scope

WS1 owns the "heart" of the ATS - everything recruiters use daily to manage candidates, jobs, and submissions.

```
+-------------------------------------------------------------+
|                    WS1: Core ATS                             |
|                                                              |
|  +-------------+  +-------------+  +---------------------+  |
|  | Candidate   |  | Job &       |  | Pipeline &          |  |
|  | Management  |  | Requisition |  | Submission          |  |
|  |             |  | Management  |  | Management          |  |
|  | - Profiles  |  | - Intake    |  | - Kanban board      |  |
|  | - Resume    |  |   forms     |  | - Stage config      |  |
|  |   upload    |  | - Skills/   |  | - Shortlists        |  |
|  | - Parsing   |  |   comp/     |  | - Submission        |  |
|  |   (from WS2)|  |   visa      |  |   packages          |  |
|  | - Dedup &   |  | - Lifecycle |  | - Feedback          |  |
|  |   merge     |  | tracking    |  |   collection        |  |
|  | - Timeline  |  | - Client    |  | - Placement &       |  |
|  |   tracking  |  |   portals   |  |   fee tracking      |  |
|  +-------------+  +-------------+  +---------------------+  |
|                                                              |
|  +-------------+  +-------------+                          |
|  | Search &    |  | Reporting   |                          |
|  | Filtering   |  | & Dashboards|                          |
|  |             |  |             |                          |
|  | - Keyword   |  | - Pipeline  |                          |
|  |   + filters |  |   health    |                          |
|  | - Semantic  |  | - Submit-   |                          |
|  |   (from     |  |   tion rates|                          |
|  |   WS2/pg-   |  | - Time-to-  |                          |
|  |   vector)   |  |   submit    |                          |
|  | - Export    |  | - Recruiter |                          |
|  +-------------+  |   productivity|                        |
|                   +-------------+                          |
+-------------------------------------------------------------+
```

### Key UI Flows

**Candidate Profile Flow:**
```
Upload Resume -> AI Parse (WS2) -> Review/Edit Parsed Data -> Save Profile
                                            |
                                    Candidate is created
                                    with structured data
```

**Job Requisition Flow:**
```
Client Intake Form -> Structured Job Record -> Configurable Stages
                                                      |
                                              Assign to Recruiter
                                                      |
                                              AI Matching triggered (WS2)
                                                      |
                                              Review AI-ranked candidates
                                                      |
                                              Create Shortlist -> Submit to Client
```

**Submission Flow:**
```
Select Candidates -> AI generates summary (WS2) -> Review Package
                                                        |
                                                Generate Client Magic Link
                                                        |
                                                Client reviews + gives feedback
                                                        |
                                                Feedback captured -> Pipeline updated
```

### Search Architecture

```
+-----------------------------------------------------+
|                   Search Layer                       |
|                                                      |
|  Keyword Search (PostgreSQL full-text)               |
|  +----------------------------------------------+    |
|  | WHERE (name || skills || company) @@ query   |    |
|  |   AND tenant_id = ?                          |    |
|  +----------------------------------------------+    |
|                                                      |
|  Semantic Search (pgvector + embeddings)             |
|  +----------------------------------------------+    |
|  | SELECT candidate_id                         |    |
|  | FROM candidates                              |    |
|  | ORDER BY candidate_embedding <=> query_embedding | |
|  | LIMIT 20                                     |    |
|  +----------------------------------------------+    |
|                                                      |
|  Hybrid (keyword + semantic, ranked merge)           |
|  +----------------------------------------------+    |
|  | BM25 score (0.6) + vector similarity (0.4)   |    |
|  +----------------------------------------------+    |
+-----------------------------------------------------+
```

### Key Design Decisions

- **Kanban board as primary pipeline view**: Drag-and-drop stage progression. Configurable per job. This is the recruiter's "home screen."
- **Submission packages are immutable snapshots**: Once submitted, the package is frozen. Any changes create a new version. This provides audit trail integrity.
- **Magic link client portals**: Clients access submitted candidates via time-limited, single-use magic links with optional OTP. No password required. White-labeled per client.
- **Placement & fee tracking**: Simple financial ledger tracking fee percentage, start date, guarantee period, and commission splits between recruiters.
- **Search is unified**: One search bar that combines keyword, filter, and semantic results. pgvector handles semantic search natively in PostgreSQL - no separate vector database needed.

---

## 5. AI Features (Workstream 2)

### Feature Scope

WS2 owns all AI-powered capabilities. It's a service layer that WS1 and WS3 consume through async job queues.

```
+-------------------------------------------------------------+
|                  WS2: AI Features                            |
|                                                              |
|  +-----------------------------------------------+          |
|  |           PII Privacy Shield (Section 3)       |          |
|  +-----------------------------------------------+          |
|                            |                                |
|  +-----------+ +----------+|  +----------+ +------------+  |
|  | Resume    | | Match    ||  | Summarize| | Outreach   |  |
|  | Parser    | | Support  ||  | Engine   | | Drafter    |  |
|  |           | |          ||  |          | |            |  |
|  | - Structure| | - Fit    ||  | - Profile| | - Email    |  |
|  |   extraction| |   score  ||  |  summary | |   drafts   |  |
|  | - Normal-  | | - Fit    ||  | - Candidate| | - Follow-  |  |
|  |   ization  | |   signals||  |  brief   | |   up       |  |
|  | - Dedup    | | - Gap    ||  | - Interview| | - Variant  |  |
|  |   detection| |   analysis||  |  feedback| |   generation| |
|  +-----------+ +----------+|  +----------+ +------------+  |
|                            |                                |
|  +-----------------------------------------------+          |
|  |         AI Governance Layer                       |          |
|  |  - Audit logging (hashed prompts/outputs)         |          |
|  |  - Confidence scoring & visual flags              |          |
|  |  - Override capture (reason, timestamp, user)     |          |
|  |  - Bias monitoring (4/5ths rule, offline)         |          |
|  |  - Provider failover & rate limiting              |          |
|  +-----------------------------------------------+          |
+-------------------------------------------------------------+
```

### AI Job Queue

```
+------------------------------------------------------+
|              Redis Job Queue (BullMQ)                 |
|                                                       |
|  Queues:                                              |
|  + ai:parse        (resume parsing)                   |
|  + ai:match        (candidate-job matching)           |
|  + ai:summarize    (profile/feedback summarization)   |
|  + ai:outreach     (email/message drafting)           |
|                                                       |
|  Priority: parse > match > summarize > outreach       |
|  Retry: 3 attempts with exponential backoff           |
|  Timeout: 30s per job (then fail + notify)            |
+------------------------------------------------------+
```

### AI Feature Details

**Resume Parser:**
- Input: PDF/DOCX/TXT resume file
- Process: Extract text -> PII redaction -> LLM parse -> structured JSON
- Output: `{ name, email, phone, skills[], experience[], education[], ... }`
- Confidence: Per-field confidence scores. Low-confidence fields flagged for review.
- Trigger: Automatic on resume upload. Also triggerable manually.

**Match Support:**
- Input: Candidate profile JSON + job requisition JSON
- Process: PII-redact both -> LLM comparison -> fit analysis
- Output: `{ score: 0-100, fit_signals: {...}, gaps: [...], recommendation: "strong|moderate|weak" }`
- **Human approval gate**: AI score is a suggestion. Recruiter must explicitly approve before shortlist export.
- Override logging: If recruiter changes the AI ranking, the reason is captured.

**Summarization Engine:**
- Profile summary: AI-generated 3-paragraph brief of candidate's background, strengths, and fit
- Candidate brief: Job-specific summary for client submission packages
- Interview feedback: Aggregates multiple feedback entries into a coherent summary
- Candidate-facing: Candidates can view their own AI-generated summary in the portal

**Outreach Drafter:**
- Input: Candidate profile + job requisition + outreach context
- Output: Personalized email draft with subject line, body, and suggested follow-up timing
- Variants: Generates 2-3 tone variants (professional, warm, concise)
- Template integration: Uses tenant-configured email templates as base

### Key Design Decisions

- **AI as a service, not a UI**: AI features don't have their own screens. They're embedded in WS1 workflows (candidate profile page shows AI match score, job page shows AI-suggested candidates).
- **No auto-rejection**: AI can never auto-reject or auto-select a candidate. Every AI output is a recommendation that requires human action.
- **Bias monitoring is offline**: Because PII is redacted during LLM processing, real-time bias monitoring on individual predictions is infeasible. Bias analysis runs on aggregated pseudonymized datasets in a separate offline pipeline (weekly cron job).
- **Model provider is configurable per tenant**: Admins can choose which LLM provider their tenant uses, with automatic failover to a configured backup.

---

## 6. Portals & CRM (Workstream 3)

### Feature Scope

WS3 owns everything that touches candidates and clients directly - the candidate self-service portal, the client submission portal, and the recruiter CRM with email/calendar sync.

```
+-------------------------------------------------------------+
|                WS3: Portals & CRM                            |
|                                                              |
|  +---------------+   +-----------------------------------+  |
|  |  Candidate    |   |  Client Portal                    |  |
|  |  Portal       |   |  (SSR, Next.js)                   |  |
|  |  (SSR, Next.js) | |                                   |  |
|  |               |   |  - View submitted                 |  |
|  |  - Profile mgmt|  |    candidates                    |  |
|  |  - AI summary view| |  - AI-generated summaries      |  |
|  |  - Job recommendations| |    of candidates             |  |
|  |  - Status tracking| |  - Provide feedback              |  |
|  |  - AI disclosure &| |  - Track requisition             |  |
|  |    consent      |   |    progress                      |  |
|  |  - Magic link login | |  - OTP-protected access        |  |
|  +---------------+   +-----------------------------------+  |
|                                                              |
|  +-----------------------------------------------+          |
|  |              Recruiter CRM                       |          |
|  |                                                |          |
|  |  - Sourcing lists & prospect tracking          |          |
|  |  - Outreach templates & sequences              |          |
|  |  - Activity timeline (calls, emails, follow-ups)|          |
|  |  - Relationship history (candidates, clients)  |          |
|  |  - Bi-directional email sync (Exchange + Google)|          |
|  |  - Calendar sync (availability, interviews)    |          |
|  +-----------------------------------------------+          |
+-------------------------------------------------------------+
```

### Candidate Portal

```
Authentication:
+ Email magic link (one-time login URL, expires in 15 min)
+ Optional OTP secondary verification (for sensitive actions)
+ Session-based (JWT stored in httpOnly cookie)

Pages:
+ /portal/dashboard     - Application status overview
+ /portal/profile       - View/edit profile, upload resumes
+ /portal/recommendations - AI-suggested open jobs
+ /portal/consent       - AI disclosure, data rights, consent mgmt
+ /portal/interview     - Interview details (if applicable)

AI Features in Portal:
+ AI-generated profile summary (viewable, regeneratable)
+ AI-driven job recommendations (passive, based on profile)
+ AI disclosure notices (when/how AI is used)
```

### Client Portal

```
Authentication:
+ Magic link sent to client contact email
+ Optional OTP for high-sensitivity roles
+ Time-limited (links expire after 7 days or first use)

Pages:
+ /client/{token}       - Submission package view
+ /client/{token}/feedback - Provide feedback on candidates
+ /client/{token}/status - Requisition progress tracker

Features:
+ White-labeled (agency logo, colors)
+ Read-only candidate packages (no edit access)
+ 1-click feedback: Approve / Request Interview / Pass
+ Feedback is captured -> flows back to WS1 pipeline
```

### Email & Calendar Sync

```
+------------------------------------------------------+
|              Email/Calendar Sync Layer                |
|                                                       |
|  Providers:                                           |
|  + Microsoft Graph API (Outlook/Office 365)           |
|  + Google Workspace API (Gmail + Calendar)            |
|                                                       |
|  Flow:                                                |
|  +---------+    OAuth2    +--------------+            |
|  | Recruiter| ----------> | Provider API |            |
|  |  connects| <----------- | (Graph/Google)|            |
|  +---------+   tokens     +--------------+            |
|        |                                              |
|        v                                              |
|  +--------------+    Webhook    +--------------+      |
|  | Local Sync   | <---------- | Provider     |      |
|  | Service      |              | Webhooks     |      |
|  +------+-------+              +--------------+      |
|         |                                              |
|         v                                              |
|  +--------------+                                     |
|  | Activity     |                                     |
|  | Table (WS1)  |                                     |
|  +--------------+                                     |
|                                                       |
|  Capabilities:                                        |
|  + Send emails (via provider, logged locally)         |
|  + Receive emails (webhook -> activity log)           |
|  + Calendar events (interviews, follow-ups)           |
|  + Two-way sync (changes in either direction prop.)   |
+------------------------------------------------------+
```

### CRM Data Model (extends Section 2)

```
+-----------------------------------------------------+
|  OUTREACH (CRM sequence management)                 |
|  +-----------------------------------------------+  |
|  | id, candidate_id, job_id, template_id         |  |
|  | sequence_step (1, 2, 3...), status            |  |
|  | subject, body, sent_at, responded_at          |  |
|  | response_type (interested|not_interested      |  |
|  |   | no_reply), next_action, scheduled_at      |  |
|  +-----------------------------------------------+  |
|                                                      |
|  +-----------------------------------------------+  |
|  | ACTIVITY (unified timeline)                   |  |
|  | id, tenant_id, candidate_id, job_id           |  |
|  | actor_id (user who created it)                |  |
|  | type (email_sent|email_received|call          |  |
|  |   | meeting|note|status_change|ai_action)     |  |
|  | data (JSON - type-specific payload)           |  |
|  | occurred_at, created_at                       |  |
|  +-----------------------------------------------+  |
+-----------------------------------------------------+
```

### Key Design Decisions

- **Portals are SSR, not SPA**: Candidate and client portals use Next.js server-side rendering. This means fast initial load, SEO-friendly, and session auth handled server-side. No separate frontend needed.
- **Magic links for both portals**: No passwords. This reduces friction for clients (who may only use the portal once per submission) and candidates (who may apply once and forget).
- **Email sync is opt-in per recruiter**: Recruiters connect their own email/calendar accounts. The system doesn't have a shared inbox. This keeps privacy simple and aligns with how recruiters actually work.
- **CRM is recruiter-centric**: Sourcing lists, outreach sequences, and activity tracking are all tied to the recruiter's perspective. Candidates are the shared entity between CRM and ATS.
- **Activity timeline is the single source of truth**: Every interaction (email, call, note, AI action, status change) flows into the unified activity table. This is what both the recruiter and candidate portals display as the "timeline."

---

## 7. Compliance & Security

### EU AI Act Compliance Architecture

```
+-------------------------------------------------------------------+
|              EU AI Act High-Risk Compliance Framework             |
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Article 5: Prohibited Practices (Hard Blocks)              ||
|  |  - No emotion recognition                                   ||
|  |  - No biometric categorization                              ||
|  |  - No automated rejection/auto-selection                    ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Article 9: Risk Management                                 ||
|  |  - Written AI risk management process                       ||
|  |  - Risk matrix per AI feature (parse, match, summarize)     ||
|  |  - Periodic review (quarterly)                              ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Article 10: Data Governance                                ||
|  |  - Representative operational data                          ||
|  |  - Bias testing (4/5ths rule, offline, weekly)              ||
|  |  - No training on customer data (ZDR agreements)            ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Article 12: Logging & Traceability                         ||
|  |  - Immutable audit logs (hashed prompts/outputs)            ||
|  |  - 6-month minimum retention                                ||
|  |  - Searchable by tenant, job, candidate, user               ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Article 13 & 14: Transparency & Human Oversight            ||
|  |  - AI disclosure in candidate portal & emails               ||
|  |  - Human approval gate before shortlist export              ||
|  |  - Override capture (reason, timestamp, user)               ||
|  |  - AI outputs visually distinct from decisions              ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Article 15: Accuracy, Robustness & Cybersecurity           ||
|  |  - Prompt injection defenses (input sanitization)           ||
|  |  - Rate limiting on all AI API calls                        ||
|  |  - Output validation before workflow use                    ||
|  |  - ZDR agreements with all providers                        ||
|  |  - Model drift monitoring                                   ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Articles 26 & 86: Candidate Rights                         ||
|  |  - Right to explanation (one-click automated report)        ||
|  |  - Access, correction, objection, deletion, portability     ||
|  |  - Complaint intake & case tracking                         ||
|  +-------------------------------------------------------------+|
|                                                                   |
|  +-------------------------------------------------------------+|
|  |  Post-Market Monitoring                                     ||
|  |  - Incident tracking & escalation                           ||
|  |  - Performance review by tenant/workflow                    ||
|  |  - Rollback procedures for problematic models               ||
|  |  - Regular vendor review for AI providers                   ||
|  +-------------------------------------------------------------+|
+-------------------------------------------------------------------+
```

### Security Architecture

```
+-------------------------------------------------------------+
|                   Security Layers                            |
|                                                              |
|  1. Network & Infrastructure                                |
|     + TLS 1.3 everywhere (in transit)                       |
|     + AWS WAF (web application firewall)                    |
|     + Security groups (least privilege)                     |
|     + VPC isolation (RDS, ElastiCache, ECS in private subnets)|
|                                                              |
|  2. Application                                              |
|     + NextAuth.js (session-based auth)                      |
|     + RBAC middleware (protect routes + API endpoints)       |
|     + Rate limiting (per-user, per-tenant on API)           |
|     + Input validation (Zod schemas on all inputs)          |
|     + CSRF protection (sameSite cookies)                    |
|                                                              |
|  3. Data                                                     |
|     + AES-256 at rest (RDS encryption + S3 KMS)             |
|     + Tenant-isolated S3 paths with KMS keys                |
|     + RLS on PostgreSQL (every query enforces tenant_id)    |
|     + Secrets in AWS Secrets Manager (not env vars)         |
|     + Pseudonymized AI audit logs                           |
|                                                              |
|  4. AI-Specific                                              |
|     + PII redaction before every LLM call                   |
|     + Hashed prompt/output storage (no raw PII in logs)     |
|     + ZDR enterprise agreements with providers              |
|     + Prompt injection detection (input sanitization)       |
|     + Graceful degradation (AI unavailable -> manual mode)  |
+-------------------------------------------------------------+
```

### GDPR / Privacy Data Flows

```
Candidate Data Lifecycle:
+----------+   +----------+   +----------+   +----------+
| Collect  |-->| Store    |-->| Process  |-->| Delete   |
| (resume, |   | (encrypted|   | (AI      |   | (retention|
|  profile,|   |  RDS +    |   |  parsing,|   |  policy  |
|  consent)|   |  S3)      |   |  matching)|   |  triggered|
+----------+   +----------+   +----------+   |  by cron  |
                                             +----------+
         |                                          |
         |  DSAR (Data Subject Access Request)      |
         |  +-----------------------------------+   |
         |  | 1. Candidate requests data        |   |
         |  | 2. System exports all candidate   |   |
         |  |    data (PDF/JSON)                |   |
         |  | 3. Candidate requests deletion    |   |
         |  | 4. System erases within 24h       |   |
         |  | 5. AI audit logs pseudonymized    |   |
         |  |    (retained for 6 months per     |   |
         |  |    EU AI Act, but candidate PII  |   |
         |  |    removed from logs)             |   |
         |  +-----------------------------------+   |
         +------------------------------------------+
```

### Key Design Decisions

- **Compliance is built-in, not bolted-on**: Every feature has compliance considerations baked into its design. The AI audit log table is created alongside the candidate table, not as an afterthought.
- **Pseudonymized audit logs**: EU AI Act requires 6-month log retention, but GDPR requires the right to be forgotten. The solution: audit logs store hashed prompts (not raw text) and use candidate IDs (not names). When a candidate requests deletion, their ID is replaced with `[DELETED_CANDIDATE_XXX]` in audit logs - traceability is maintained without PII.
- **Tenant-configurable retention**: Each agency tenant sets their own data retention periods (e.g., "delete inactive candidate data after 2 years"). A cron job enforces these policies automatically.
- **Right to explanation is automated**: When a candidate requests an explanation of AI evaluation, the system generates a report from the AI match result data (fit signals, gap analysis, score breakdown) - no manual intervention needed.

---

## 8. Milestones & Delivery Plan

### Timeline Overview

```
Month 1          Month 2          Month 3          Month 4          Month 5          Month 6
+--------------+ +--------------+ +--------------+ +--------------+ +--------------+ +--------------+
|  FOUNDATION  | |  Foundation  | |   WS1: Core  | |   WS2: AI    | |   WS3:       | |  Compliance  |
|  (All Hands) | |  (All Hands)  | |   ATS (WS1)  | |   Features   | |   Portals &  | |  Hardening   |
|              | |              | |   + WS2: AI  | |   (WS2) +    | |   CRM (WS3)  | |  + GA Launch |
| - Infra setup| | - Auth + RBAC| |   parsing    | |   matching   | |   + email/c  | | - Audit log  |
| - DB schema  | | - Multi-tenant| |   + summar.  | |   + outreach | |   alendar    | |   completeness|
| - AI middleware| - AI middleware|   + job mgmt | |   + candidate | |   + client   | | - Bias moni- |
| skeleton     | - S3 + Redis  | |   + candidate | |   portal      | |   portal      |   toring +   |
| - Core models| - Kanban board| |   profiles    | |   + CRM       | |   + CRM       |   drift      |
| scaffolding  | (partial)      | |   + search    | |   + outreach   | |   + reporting | | - Pen test   |
+--------------+ +--------------+ +--------------+ +--------------+ +--------------+ +--------------+
     alpha (internal)                beta (limited beta)                              GA release
```

### Phase Details

**Phase 0: Foundation (Month 1)** - All 2-4 devs
- AWS infrastructure (VPC, RDS, S3, ElastiCache, ECS)
- PostgreSQL with RLS, pgvector, Prisma schema
- Auth (NextAuth.js), RBAC middleware, admin console
- AI middleware skeleton (PII redaction, provider abstraction, job queue)
- Core data models (Tenant, User, Candidate, Job, Application, Submission)
- API scaffolding (REST endpoints for all core entities)

**Phase 1: Foundation + Early Features (Month 2)** - All hands transition to workstreams
- Auth + RBAC polished (magic link login, session management)
- Multi-tenant isolation verified (RLS tests, S3 isolation tests)
- AI middleware production-ready (all 4 operations: parse, match, summarize, outreach)
- WS1: Kanban board (partial), candidate profiles, job management
- WS1: Basic search (keyword + filters)
- **Milestone: Internal alpha**

**Phase 2: Core ATS + AI Parsing (Months 3-4)** - WS1 primary, WS2 kicks in
- WS1: Pipeline management (full kanban, configurable stages), submission workflow, placement & fee tracking
- WS1: Semantic search (pgvector), reporting dashboards
- WS2: Resume parsing (production), match support, summarization, outreach drafting
- WS2: AI governance (audit logging, confidence flags, override capture)
- WS3: Candidate portal (profile mgmt, AI summary view, job recommendations, consent)
- **Milestone: Beta release**

**Phase 3: AI Matching + Portals + CRM (Months 4-5)** - WS2 primary, WS3 active
- WS2: AI matching production, bias monitoring (offline), provider failover
- WS3: Client portal (magic link, submission review, feedback)
- WS3: Recruiter CRM (sourcing lists, outreach sequences, activity timeline)
- WS3: Email/calendar sync (Microsoft Graph + Google Workspace)
- WS1: Search polish, exportable reports, client feedback integration
- **Milestone: Client portal + AI matching deployed**

**Phase 4: Compliance Hardening + GA (Months 5-6)** - All hands
- Full EU AI Act compliance (audit logs, bias monitoring, right-to-explanation)
- Candidate rights workflows (access, correction, deletion, portability)
- Post-market monitoring setup, incident tracking
- Performance optimization, multi-region readiness
- Security hardening, penetration testing
- Conformity assessment documentation
- **Milestone: GA release**

### KPIs (from PRD)

| Metric | Target |
|--------|--------|
| Time per client submission package | <5 min (from 45 min) |
| Time-to-first-submittal | 50% decrease |
| CV parsing accuracy | >92% |
| PII redaction accuracy | >92% |
| AI recommendation acceptance rate | >60% |
| Audit log completeness | 100% |
| Non-compliance flags | 0 |

### Key Design Decisions

- **Foundation-first with overlapping phases**: Month 1 is all-hands foundation. Months 2-6 have overlapping workstreams - WS2 starts in Month 2 (parsing) and ramps up in Month 4 (matching). WS3 starts in Month 3 and runs through Month 5.
- **Three milestone gates**: Alpha (end of M2), Beta (end of M4), GA (end of M6). Each gate has a clear "done" definition.
- **Compliance is the last phase, but built incrementally**: Audit logging is built in Month 2. Bias monitoring in Month 4. Full compliance hardening in Month 6. You can't "add compliance" at the end - it's woven into every phase.
- **Email/calendar sync is late because it's complex**: Bi-directional sync with two providers (Microsoft + Google) is a significant undertaking. It's placed in WS3 (Months 4-5) where it doesn't block the core ATS or AI features.
- **Testing runs parallel to development**: Each workstream owns its tests (unit, integration, E2E). Compliance phase includes pen testing and external audit.

---

## Tech Stack Summary

| Layer | Choice | Why |
|-------|--------|-----|
| **Frontend** | Next.js 14+ (App Router), React 18, TypeScript | Full-stack framework, SSR for portals, great DX |
| **UI** | Tailwind CSS + shadcn/ui | Fast, accessible, customizable component library |
| **Backend** | Next.js API Routes (monorepo) or separate Node/Express service | Shared TypeScript types, simple deployment |
| **Database** | PostgreSQL + Prisma ORM | RLS for multi-tenancy, pgvector for semantic search, great tooling |
| **Cache/Queue** | Redis (ElastiCache) | Job queues for AI processing, session cache |
| **Storage** | AWS S3 + presigned URLs | Tenant-isolated buckets, KMS encryption |
| **Auth** | NextAuth.js (Auth.js) v5 | OAuth, magic links, session management |
| **AI Middleware** | Custom Node.js service | PII redaction, provider abstraction, ZDR compliance |
| **Email/Calendar** | Microsoft Graph API + Google Workspace API | Bi-directional sync |
| **Infra** | AWS (RDS, S3, ECS/Fargate, ElastiCache) | Managed services, multi-region readiness, EU data residency |
| **Monitoring** | OpenTelemetry + Grafana/LangSmith | Logs, metrics, traces across AI and non-AI workflows |

---

## Design Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Foundation-First Parallelism | Best balance of parallelism and coordination for 2-4 devs |
| Email/Calendar sync | Included in v1 | Essential for recruiter CRM and outreach |
| AI chatbot | Excluded from v1 | Complex, not core to ATS value proposition |
| Tech stack | Next.js + PostgreSQL + AWS | Full-stack TypeScript, RLS multi-tenancy, managed infra |
| AI operations | Async-only (job queue) | Keeps UI responsive, enables batch processing |
| Prompt storage | Hashed (SHA-256) | EU AI Act traceability + GDPR privacy |
| Bias monitoring | Offline, weekly cron | PII is redacted during LLM processing; real-time monitoring infeasible |
| Portal auth | Magic links | Low friction for clients and candidates |
| Email sync | Opt-in per recruiter | Privacy-simple, matches how recruiters actually work |
| Search | pgvector (in-database) | No separate vector DB needed; simpler ops |
