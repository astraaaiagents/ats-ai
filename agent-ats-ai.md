# Product Requirements Document (PRD)
## Agent-First AI-Native Recruiter Client Portal

**Version:** 1.0
**Date:** 2026-07-22
**Status:** Approved Design — Ready for Implementation
**Base Reference:** ats-ai.md (AI-Native ATS), notes.md (Staffing Co. scope)

---

## 1. Executive Summary

The Agent-First AI-Native Recruiter Client Portal is a conversational, agent-driven interface for staffing agency recruiters. Instead of navigating dashboards, filters, and forms, the recruiter **talks to an AI agent** that understands their preferences, sources candidates from multiple channels, ranks them intelligently, and drafts outreach — all through natural language.

The agent **learns** each recruiter's unique candidate matching preferences over time, becoming increasingly accurate at surfacing the right candidates. It is proactive: it monitors the candidate pool and job openings, and initiates contact when strong matches are found.

This system is a **superset** of the base ATS (ats-ai.md). It adds an agent-first interaction layer on top of the existing multi-tenant candidate management, job requisition, and client portal foundations. The recruiter portal is the primary interface; the client portal (for Hiring Managers) and candidate portal (for applicants) remain as separate but integrated experiences.

**Crucially, this system treats AI candidate matching as High-Risk (EU AI Act Annex III, Point 4).** All AI-generated rankings, summaries, and outreach drafts are decision support only. Every submission to a client requires explicit human approval. Zero auto-submissions.

---

## 2. Business Context

### 2.1 Staffing Company Profile

| Attribute | Detail |
|-----------|--------|
| **Domain** | IT Staffing (software engineers, data scientists, DevOps, PMs) |
| **Anchor Customers** | TCS, Infosys, Wipro (large Indian IT services firms) |
| **Business Model** | Markup on contractor bill rates; revenue = (bill_rate × hours) − burden |
| **MVP Scope** | Front-office only: job intake → sourcing → submission → placement |
| **Out of MVP** | Back-office (invoicing, fee tracking, compliance), direct employer self-service |

### 2.2 Current Recruiter Workflow (As-Is)

```
1. Hiring Manager (HM) at TCS submits job requirement via email/call/portal
2. Account Manager (AM) at Staffing Co. assigns job to a recruiter (round-robin)
3. Recruiter manually searches internal candidate database (50K+ candidates)
   - Uses structured filters: location, experience, skills, visa status
   - Reviews hundreds of profiles manually
   - No AI assistance for ranking or matching
4. Recruiter sources from job boards (manual monitoring)
5. Recruiter reviews candidates, creates shortlist
6. Recruiter submits candidates to client portal for HM review
7. Recruiter schedules interviews
8. Placement: contract / temporary / permanent
```

**Pain Points:**
- Manual candidate search across 50K+ profiles is time-consuming and error-prone
- No intelligent ranking — recruiters rely on gut feel, not data
- Job board monitoring is manual and inconsistent
- Outreach drafting is repetitive and generic
- No preference learning — each recruiter starts from scratch every time
- AM round-robin assignment has no intelligence (doesn't match recruiter expertise to job domain)

---

## 3. Target Personas

| Persona | Role & Needs | System Interaction |
| :--- | :--- | :--- |
| **Recruiter** | Primary user. Sources, ranks, submits candidates. Needs AI assistance to eliminate manual search and scale outreach. | **Daily driver.** Interacts with the AI agent via chat. Reviews candidate cards, approves/rejects, drafts outreach, schedules interviews. |
| **Account Manager (AM)** | Manages client relationships, assigns jobs to recruiters. Needs visibility into recruiter workload and submission quality. | Assigns job requests to recruiters (may be AI-assisted in future). Monitors recruiter KPIs. Hybrid role: can also act as recruiter. |
| **Hiring Manager (HM)** | Client-side contact (at TCS/Infy/Wipro). Submits job requirements, reviews submitted candidates. | Uses the **Client Portal** (separate from agent portal). Submits job reqs via portal or email. Reviews candidate submissions. |
| **Candidate** | Job seeker applying through client websites. Needs easy application flow and transparency. | Uses the **Candidate Portal** (embedded in client websites). Uploads resume, searches jobs, tracks applications. |
| **Agency Admin** | Manages multi-tenant configurations, user permissions, compliance, audits. | Admin Console for RBAC, compliance logs, data residency controls. |

---

## 4. System Architecture

### 4.1 The Unified AI Middleware Gateway (Extended)

All AI features operate through a centralized gateway, extended for the agent portal:

1. **PII Redaction:** Strips PII before sending data to external LLMs. Side-by-side original vs. redacted view for recruiter review.
2. **Provider Routing:** Routes sanitized prompts to foundational LLMs (OpenAI GPT-4o) under Enterprise Zero-Data-Retention agreements.
3. **Agent Orchestration:** New layer — manages the Orchestrator + Specialist Agent lifecycle, state management, and inter-agent communication.
4. **Preference Learning Pipeline:** New component — tracks recruiter actions, updates preference vectors, feeds learned preferences back into ranking.
5. **Audit Logging & GDPR Erasure:** Logs all agent interactions, tool calls, preference updates. Pseudonymized for GDPR "Right to be Forgotten."
6. **Data Sovereignty:** Region-specific data residency. EU candidate data remains in EU.

### 4.2 Agent Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chat UI (Next.js)                        │
│  ┌──────────┬────────────────────────┬──────────────────────┐  │
│  │ Sidebar  │    Chat Panel          │   Context Panel      │  │
│  │          │  ┌──────────────────┐  │  Open Jobs           │  │
│  │ Convers. │  │ Agent: I found   │  │  └─ Java Lead        │  │
│  │ History  │  │ 3 strong matches │  │  └─ Python Dev       │  │
│  │          │  │ for TCS Java     │  │                      │  │
│  │          │  │ [Approve][Review]│  │  Top Matches         │  │
│  │          │  └──────────────────┘  │  ────────────        │  │
│  │          │  ┌──────────────────┐  │  1. Jane Doe ★★★★★  │  │
│  │          │  │ Candidate Card   │  │  2. John Smith ★★★★ │  │
│  │          │  │ [View][Submit]   │  │                      │  │
│  │          │  └──────────────────┘  │  Recent Activity     │  │
│  │          │  [Type...] 📎         │                      │  │
│  └──────────┴────────────────────────┴──────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ SSE / WebSocket (proactive alerts)
                         │ POST / GET (conversations)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Gateway (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Auth Middleware → Tenant Isolation → Rate Limiting      │  │
│  │  /api/v1/agent/conversation (POST/GET)                   │  │
│  │  /api/v1/agent/preferences (GET/PUT)                     │  │
│  │  /api/v1/agent/proactive/alerts (GET)                    │  │
│  │  /api/v1/agent/action-log (GET)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Orchestration Layer                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Orchestrator Agent (LangGraph)              │   │
│  │  • Parses user intent                                    │   │
│  │  • Delegates to specialists                              │   │
│  │  • Synthesizes responses                                 │   │
│  │  • Manages conversation state                            │   │
│  │  • Triggers proactive checks                             │   │
│  └────┬──────────┬──────────┬──────────────────┬───────────┘   │
│       │          │          │                  │                │
│       ▼          ▼          ▼                  ▼                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────────┐        │
│  │Sourcing│ │Ranking │ │Outreach│ │Preference Engine │        │
│  │Agent   │ │Agent   │ │Agent   │ │(JSONB + pgvector)│        │
│  │        │ │        │ │        │ │                  │        │
│  │search_ │ │compute_│ │draft_  │ │Explicit prefs    │        │
│  │candidates│fit_   │ │outreach│ │Implicit vectors  │        │
│  │_db()   │ │score() │ │()      │ │Learning loop     │        │
│  │        │ │        │ │        │ │Update triggers   │        │
│  │search_ │ │gap_    │ │get_    │ │                  │        │
│  │job_    │ │identify│ │contact │ │Memory Store      │        │
│  │boards()│ │()      │ │()      │ │(InMemoryStore)   │        │
│  │        │ │        │ │        │ │                  │        │
│  │search_ │ │compare │ │gen_    │ │Session Memory    │        │
│  │sub_    │ │_cand() │ │email() │ │Conversation Log  │        │
│  │vendors()│ │        │ │        │ │Action Audit Log │        │
│  └──┬─────┘ └──┬─────┘ └──┬─────┘ └──────────────────┘        │
│     │           │            │                                 │
│     ▼           ▼            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Data & Integration Layer                    │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │  │
│  │  │PostgreSQL│ │pgvector  │ │Redis     │ │LLM Gateway │ │  │
│  │  │(Candidates│ │(Embed-  │ │(Rate     │ │(PII Redact │ │  │
│  │  │, Users,  │ │dings)    │ │Limit,    │ │, ZDR)      │  │
│  │  │Jobs,     │ │          │ │ARQ Queue)│ │             │  │
│  │  │Prefs)    │ │          │ │          │ │             │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  Job Boards (RSS/API) │ Google Calendar │ Email (SendGrid)      │
│  ──────────────────── │ ─────────────── │ ────────────────────  │
│  Monitor inbound apps │ Schedule interviews │ Send outreach     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Data Flow: Reactive (Recruiter Initiates)

```
Step 1: Recruiter types "Find me strong candidates for the TCS Java lead role"
Step 2: Agent Gateway receives message, validates JWT, extracts recruiter_id + tenant_id
Step 3: Gateway loads recruiter's conversation session from Memory Store
Step 4: Gateway loads recruiter's preference profile (explicit JSONB + implicit pgvector)
Step 5: Orchestrator parses intent → determines need for sourcing + ranking
Step 6: Orchestrator calls SourcingAgent.search_candidates_db(query="Java lead", filters={client:"TCS"})
Step 7: SourcingAgent queries PostgreSQL (tenant-scoped) + pgvector (skill embeddings)
Step 8: SourcingAgent returns top 50 candidate profiles with metadata
Step 9: Orchestrator calls RankingAgent.compute_fit_score(candidates=[...], job_id=123)
Step 10: RankingAgent applies recruiter's learned preferences → computes fit scores
Step 11: RankingAgent returns ranked list with fit scores, strengths, gaps
Step 12: Orchestrator synthesizes → generates natural language response + structured candidate cards
Step 13: Response streamed to Chat UI via SSE
Step 14: Action logged to agent_actions table (EU AI Act audit)
```

### 4.4 Data Flow: Proactive (Agent Initiates)

```
Step 1: ARQ Cron Job fires every 30 minutes
Step 2: For each active recruiter:
  a. Fetch open job requisitions from existing backend
  b. Fetch recruiter's implicit + explicit preferences
  c. Query new candidates in DB (since last sourcing pulse)
  d. Run RankingAgent on new candidates
Step 3: If top match score > configured threshold (default: 0.85):
  a. Orchestrator generates proactive alert message
  b. Alert stored in agent_proactive_alerts table
  c. Alert pushed to recruiter's Chat UI via SSE
Step 4: Recruiter sees alert banner: "I found 3 strong matches for your TCS Java role"
Step 5: Recruiter clicks alert → conversation opens with candidate cards
```

---

## 5. Feature Scope

### 5.1 In-Scope for MVP (Front-Office)

#### 5.1.1 Agent Gateway & Conversation API

| Feature | Description | Priority |
|---------|-------------|----------|
| Conversation endpoint | POST `/api/v1/agent/conversation` — receive recruiter message, stream agent response | P0 |
| Conversation history | GET `/api/v1/agent/conversation/{session_id}` — retrieve past messages | P0 |
| Preference read/write | GET/PUT `/api/v1/agent/preferences` — manage explicit preferences | P0 |
| Preference scores | GET `/api/v1/agent/preferences/implicit` — read learned preference scores | P1 |
| Proactive alerts | GET `/api/v1/agent/proactive/alerts` — retrieve agent-initiated alerts | P1 |
| Audit trail | GET `/api/v1/agent/action-log` — EU AI Act compliant action log | P0 |
| SSE streaming | Server-Sent Events for real-time agent responses and proactive alerts | P0 |

#### 5.1.2 Orchestrator Agent

| Feature | Description | Priority |
|---------|-------------|----------|
| Intent parsing | LLM-based intent classification: source candidates, check pipeline, update preferences, schedule interview | P0 |
| Tool delegation | Dynamic delegation to SourcingAgent, RankingAgent, OutreachAgent based on intent | P0 |
| Response synthesis | Combine specialist outputs into coherent natural language + structured cards | P0 |
| State management | LangGraph StateGraph with persistent conversation state | P0 |
| Proactive trigger | Support for "sourcing pulse" trigger from background monitor | P1 |
| Confidence scoring | Agent confidence score on each response (low confidence → flag for human review) | P1 |

#### 5.1.3 Sourcing Agent

| Feature | Description | Priority |
|---------|-------------|----------|
| Internal DB search | Search 50K+ candidates via structured filters (location, experience, visa, salary) | P0 |
| Vector skill search | pgvector-based semantic search on candidate skill embeddings | P0 |
| Job board monitoring | Poll job boards (RSS/API) for inbound applications | P1 |
| Sub-vendor intake | Receive and process candidate profiles from sub-vendors | P2 |
| Job details lookup | Fetch full job requisition details for context-aware sourcing | P0 |
| Quick review support | Return candidates in a format optimized for rapid recruiter review | P1 |

#### 5.1.4 Ranking Agent

| Feature | Description | Priority |
|---------|-------------|----------|
| Fit score computation | Compute 0–1 fit score for each candidate against job requirements | P0 |
| Preference application | Apply recruiter's explicit + implicit preferences to ranking | P0 |
| Gap analysis | Identify skill/experience gaps between candidate and job requirements | P0 |
| Strength analysis | Identify candidate strengths relative to job requirements | P0 |
| Candidate comparison | Side-by-side comparison of top candidates | P1 |
| Bias mitigation | Offline statistical bias monitoring on aggregated pseudonymized data | P1 |

#### 5.1.5 Outreach Agent

| Feature | Description | Priority |
|---------|-------------|----------|
| Outreach drafting | Generate personalized email/message for each candidate | P1 |
| Template engine | Job-specific template with candidate personalization | P1 |
| Recruiter approval | Draft stored for recruiter review before sending | P0 |
| Email sending | Integrate with SendGrid/SMTP for delivery | P2 |
| Style learning | Learn preferred outreach tone from recruiter edits | P2 |

#### 5.1.6 Preference Engine & Memory

| Feature | Description | Priority |
|---------|-------------|----------|
| Explicit preferences | JSONB storage for hard rules set by recruiter | P0 |
| Implicit preferences | pgvector embeddings for learned patterns | P0 |
| Learning loop | Auto-update implicit preferences from recruiter actions | P0 |
| Session memory | LangChain InMemoryStore for conversation context | P0 |
| Conversation log | PostgreSQL storage for full conversation history | P0 |
| Preference transparency | UI to show recruiter what the agent learned | P1 |
| Weekly learning digest | Agent summarizes weekly learning to recruiter | P2 |

#### 5.1.7 Chat UI

| Feature | Description | Priority |
|---------|-------------|----------|
| Chat window | Message list with streaming responses | P0 |
| Candidate cards | Structured card: name, title, fit score, strengths, actions | P0 |
| Job cards | Job requisition details, submission status | P0 |
| Proactive alerts | Banner/notification for agent-initiated alerts | P0 |
| Preference panel | Show/edit explicit preferences, view learning summary | P1 |
| Context panel | Right sidebar: open jobs, top matches, recent activity | P1 |
| AI output distinction | Visual badge/styling on all AI-generated content | P0 |
| Action buttons | Approve, reject, submit, edit preferences on cards | P0 |

### 5.2 Out of Scope for MVP

| Feature | Reason | Target Phase |
|---------|--------|--------------|
| Sub-vendor management workflows | Complex vendor onboarding, SLA tracking | Phase 4+ |
| Job posting on client's own website | Requires client integration | Phase 3+ |
| Direct employer self-service logins | Per ats-ai.md, excluded from V1 | Future |
| Autonomous AI candidate rejection | Per EU AI Act, zero auto-rejections | Never (policy) |
| Invoicing and fee tracking | Back-office, out of MVP scope | Phase 4+ |
| Advanced KPI dashboards | Basic KPI tracking in Phase 3 | Phase 3+ |
| Multi-language support | Not required for initial US market | Phase 3+ |
| Mobile app | Web-responsive is sufficient for MVP | Future |

---

## 6. Detailed User Stories

### 6.1 Recruiter — Sourcing & Ranking

**Story 1.1: Natural Language Candidate Search**
> As a recruiter, I want to type "Find me Java candidates for the TCS role" in natural language, so that I don't have to navigate filters and forms.
- **Given** I have open job requisition #123 for TCS Java Lead
- **When** I type "Find me strong Java candidates for the TCS role"
- **Then** the agent searches the internal database using structured filters + vector skill search
- **And** returns ranked candidate cards with fit scores, strengths, and gaps
- **And** each card has [View], [Submit], [Reject] action buttons

**Story 1.2: Preference-Based Ranking**
> As a recruiter, I want the agent to rank candidates the way I would, based on what I've learned about my preferences over time.
- **Given** I've reviewed 50+ candidates and consistently approved those with cloud experience
- **When** the agent ranks new candidates for a job requiring cloud skills
- **Then** candidates with cloud experience receive higher fit scores
- **And** I can see WHY each candidate was ranked where they were (strengths/gaps)
- **And** I can override the ranking by explicitly stating a preference

**Story 1.3: Quick Review Mode**
> As a recruiter, I want to quickly review a batch of candidates and approve/reject them in bulk, so that I can process hundreds of profiles efficiently.
- **Given** the agent has returned 50 candidates for a job
- **When** I review them in a streamlined card-by-card view
- **Then** I can approve, reject (with optional reason), or flag for later
- **And** each approval/rejection updates the agent's implicit preferences
- **And** after the batch, the agent summarizes: "You preferred candidates with AWS and leadership experience this round"

**Story 1.4: Proactive Match Alerts**
> As a recruiter, I want the agent to proactively notify me when strong candidates become available, so that I don't miss good talent.
- **Given** I have open job requisitions
- **When** new candidates enter the database (via application, upload, or sub-vendor)
- **Then** the agent evaluates them against my open jobs every 30 minutes
- **And** if a candidate scores above 0.85 fit, I receive a proactive alert
- **And** the alert shows the candidate's top match reasons
- **And** I can click the alert to open the candidate in the chat

### 6.2 Recruiter — Outreach

**Story 2.1: AI-Drafted Outreach**
> As a recruiter, I want the agent to draft personalized outreach messages for candidates, so that I can engage more candidates in less time.
- **Given** I've identified 5 strong candidates for a job
- **When** I ask "Draft outreach messages for these candidates"
- **Then** the agent generates personalized messages referencing each candidate's background and the job requirements
- **And** each draft shows [Edit], [Approve], [Discard] options
- **And** approved drafts are queued for sending (after recruiter confirmation)

**Story 2.2: Outreach Style Learning**
> As a recruiter, I want the agent to learn my preferred outreach tone and style, so that future drafts match how I communicate.
- **Given** I've edited several outreach drafts (e.g., made them more casual, added specific phrases)
- **When** the agent drafts new outreach messages
- **Then** it applies my learned style preferences
- **And** I can see what style preferences the agent has learned

### 6.3 Recruiter — Preference Management

**Story 3.1: Set Explicit Preferences**
> As a recruiter, I want to tell the agent my hard rules in natural language, so that it never suggests candidates that violate them.
- **Given** I'm working on a job requiring US work authorization
- **When** I say "Remember, I only submit candidates with US work authorization"
- **Then** the agent adds this as an explicit preference
- **And** future searches automatically filter out candidates without US work authorization
- **And** I can see and edit my explicit preferences in the Preference Panel

**Story 3.2: View Learning Summary**
> As a recruiter, I want to see what the agent has learned about my preferences, so that I can verify it's ranking correctly.
- **Given** I've reviewed candidates over several weeks
- **When** I open the Preference Panel
- **Then** I see my explicit rules and implicit preference scores
- **And** I see a weekly digest: "This week you preferred candidates with cloud experience, 5+ years in Java, and based in NYC"
- **And** I can override any preference

### 6.4 Account Manager — Job Assignment

**Story 4.1: AM Assigns Jobs to Recruiters**
> As an AM, I want to assign job requests to recruiters, so that the right recruiter handles each job.
- **Given** a Hiring Manager at TCS submits a new job requirement
- **When** the AM reviews the assignment queue
- **Then** the AM assigns the job to a recruiter (round-robin or manual)
- **And** the assigned recruiter receives a notification
- **And** the recruiter's agent automatically loads the job context for sourcing

**Future (out of MVP): AI-Assisted Assignment**
> As an AM, I want the agent to recommend the best recruiter for a job based on domain expertise and current workload.

### 6.5 Hiring Manager — Client Portal (Existing, Integrated)

**Story 5.1: Submit Job Requirement**
> As a Hiring Manager at TCS, I want to submit a job requirement via the client portal or email, so that the staffing agency can start sourcing.
- **Via Portal:** HM logs into client portal, fills job intake form, submits
- **Via Email:** HM emails job requirement → system parses and creates job in portal
- **And** the job is visible to the assigned AM and their recruiters

**Story 5.2: Review Submitted Candidates**
> As a Hiring Manager, I want to review candidates submitted by the staffing agency, so that I can approve/reject/provide feedback.
- **Given** the recruiter has submitted candidates to the job
- **When** the HM opens the client portal
- **Then** they see submitted candidates with AI-generated fit summaries
- **And** they can approve, reject, or provide feedback
- **And** feedback is fed back to the recruiter's agent for preference learning

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Category | Requirement | Measurement |
|----------|-------------|-------------|
| Page load | <200ms for Chat UI initial render | Lighthouse |
| CRUD operations | <100ms for agent API responses (excluding LLM call) | API metrics |
| Agent response time | <5s for intent parsing + tool delegation; <15s total with LLM | Agent metrics |
| Vector search | <500ms for pgvector skill search | DB metrics |
| Proactive monitor | Complete sourcing pulse for all recruiters within 30 min window | Cron metrics |
| SSE latency | <2s from alert generation to UI display | Network metrics |

### 7.2 Scalability

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent recruiters | 100+ | Agent Gateway horizontal scaling |
| Candidates in DB | 500K+ | pgvector supports billion-scale with IVF index |
| Conversations per day | 10,000+ | Session-based, auto-pruned after 90 days |
| LLM API calls per day | 50,000+ | Rate-limited via existing Redis rate limiter |
| Proactive pulses | Every 30 min per recruiter | ARQ distributed task queue |

### 7.3 Reliability

| Category | Requirement |
|----------|-------------|
| Availability | 99.9% uptime SLA for production |
| Agent fallback | Graceful degradation: if LLM is unavailable, agent returns "AI temporarily unavailable — please use manual search" |
| Queue durability | ARQ tasks persisted in Redis; retry on failure with exponential backoff |
| Data durability | PostgreSQL with daily backups; RPO < 1 hour, RTO < 4 hours |

### 7.4 Security

| Category | Requirement |
|----------|-------------|
| Authentication | JWT-based, existing auth middleware |
| Tenant isolation | TenantMiddleware enforces data separation; agent queries are tenant-scoped |
| PII protection | All LLM calls routed through Unified AI Middleware Gateway with PII redaction |
| Rate limiting | Existing Redis-based rate limiter applies to agent endpoints |
| Audit logging | Every agent action logged to agent_actions table with pseudonymized input/output |
| Data encryption | TLS in transit; AES-256 at rest for PostgreSQL |

---

## 8. Key Performance Indicators (KPIs)

### 8.1 Agent-Specific KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Search relevance** | >85% of top-10 candidates are recruiter-approved | Agent analytics |
| **Preference accuracy** | >90% alignment between learned preferences and recruiter actions | Weekly audit |
| **Proactive alert quality** | >70% of proactive alerts lead to recruiter review | Alert analytics |
| **Outreach draft acceptance** | >60% of AI-drafted outreach used without major edits | Outreach analytics |
| **Agent response time** | <15s p95 for full agent response (intent + tools + synthesis) | API metrics |
| **Recruiter satisfaction** | >4.0/5.0 weekly NPS score on agent usefulness | Survey |

### 8.2 Business KPIs (Aligned with ats-ai.md)

| Metric Category | Target KPI | Business Impact |
|-----------------|------------|-----------------|
| **Operational Efficiency** | <5 min per client submission package (from 45 min) | 88% reduction in candidate prep time |
| **Pipeline Velocity** | 50% decrease in time-to-first-submittal | Faster client response, higher placement win rate |
| **AI Accuracy** | >92% accuracy on CV parsing and PII redaction | Reduced human correction, zero data leaks |
| **AI Adoption** | >60% AI recommendation acceptance or edit rate | High recruiter trust and workflow integration |
| **Compliance** | 100% audit log completeness, 0 non-compliance flags | Full operational safety across US/UK/EU |

### 8.3 Recruiter KPIs (From notes.md)

| Metric | Calculation | Tracking |
|--------|-------------|----------|
| Monthly job closures | Count of placed candidates per month | Agent action log |
| Yearly job closures | Count of placed candidates per year | Agent action log |
| Candidate interactions | Count of candidate reviews, outreach sent, interviews scheduled | Agent action log |
| Gross margin | (bill_rate × total_hours) − burden (expenses, meals, travel) | Future back-office integration |
| Submission-to-placement rate | Placed candidates / Total submitted candidates | Agent action log |

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Over-automation (Automation Bias)** | Recruiters blindly accept AI rankings without review | Human approval gate on every submission; visual distinction of AI outputs; UX friction for low-confidence AI assertions; override logging |
| **Preference drift** | Agent learns incorrect patterns from noisy recruiter actions | Confidence threshold on implicit preference updates; weekly learning digest for recruiter verification; manual override capability |
| **LLM provider outage** | Agent becomes unavailable, disrupting recruiter workflow | Safe fallback: graceful degradation to manual search; output caching where safe; retry with backoff |
| **Prompt injection** | Malicious candidate resume text injects harmful prompts | Input sanitization; output validation; rate limiting; anomaly detection on CV text |
| **Vector search quality** | pgvector embeddings don't capture skill nuance | Hybrid search: vector + structured keyword match; continuous embedding model tuning; recruiter feedback loop |
| **Data privacy concerns** | Recruiters concerned about preference data collection | Transparency: recruiter sees all learned preferences; GDPR-compliant data handling; pseudonymization; right to delete |
| **Bias in AI ranking** | Agent learns biased preferences (e.g., prefers certain demographics) | PII redaction during LLM matching; offline statistical bias monitoring on aggregated pseudonymized data; bias alerts to admin |
| **Context window cost** | Multi-agent delegation increases LLM token usage | Each specialist receives minimal necessary data; Orchestrator acts as data pipeline controller; cost monitoring and alerts |
| **Proactive alert fatigue** | Too many alerts annoy recruiters | Configurable alert thresholds; batching (max 3 alerts per hour); recruiter can pause proactive mode |

---

## 10. Compliance (EU AI Act Annex III & GDPR)

### 10.1 AI Act Compliance Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Human Oversight (Art 14)** | ✅ | Every submission requires explicit recruiter approval. AI outputs are visually distinguished. Low-confidence assertions require manual confirmation. |
| **Audit Logging (Art 12)** | ✅ | All agent interactions, tool calls, preference updates logged in `agent_actions` table. Pseudonymized. |
| **Transparency & Disclosure (Art 13)** | ✅ | AI-generated content is clearly labeled. Recruiters can request explanation for any ranking. |
| **PII & Bias Mitigation (Art 10)** | ✅ | PII redaction gateway for all LLM calls. Offline statistical bias monitoring. |
| **Cybersecurity & Robustness (Art 15)** | ✅ | Prompt injection safeguards. ZDR API agreements. Rate limiting. |
| **Conformity Assessment (Art 43)** | ⏳ | Mandatory system assessment prior to EU launch (Phase 4). |
| **Risk Management (Art 9)** | ✅ | Continuous risk framework implemented via monitoring and bias alerts. |
| **Post-Market Monitoring (Art 61)** | ⏳ | Implemented in Phase 4: active reporting for incidents or AI malfunctions. |

### 10.2 GDPR Compliance

| Right | Implementation |
|-------|---------------|
| **Right to Access** | Recruiter can export all their conversation history and preference data via `/api/v1/agent/action-log` |
| **Right to Erasure** | DELETE endpoint removes recruiter's preference vectors, conversation history, and action logs (pseudonymized) |
| **Right to Rectification** | Recruiters can edit explicit preferences and correct learned implicit preferences |
| **Data Minimization** | Only recruiter ID (pseudonymized) linked to preference data. No PII in agent context. |
| **Purpose Limitation** | Preference data used only for candidate ranking. Not shared across tenants. |
| **Storage Limitation** | Conversation history auto-pruned after 90 days. Preference data retained until recruiter deletion. |

---

## 11. Database Schema

### 11.1 New Tables

```sql
-- Recruiter preference profiles
CREATE TABLE recruiter_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    explicit_preferences JSONB NOT NULL DEFAULT '{}',
    implicit_preference_vector vector(1536),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(recruiter_id)
);

-- Agent conversation sessions
CREATE TABLE agent_conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_sessions_recruiter ON agent_conversation_sessions(recruiter_id, created_at DESC);

-- Agent conversation messages
CREATE TABLE agent_conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_conversation_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'agent', 'system')),
    content TEXT NOT NULL,
    cards JSONB DEFAULT '[]',
    actions JSONB DEFAULT '[]',
    sources JSONB DEFAULT '[]',
    confidence NUMERIC(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_messages_session ON agent_conversation_messages(session_id, created_at);

-- Agent action audit log (EU AI Act compliance)
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES agent_conversation_sessions(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('source', 'rank', 'outreach', 'preference_update', 'proactive_alert', 'intent_parse')),
    agent_name TEXT NOT NULL CHECK (agent_name IN ('orchestrator', 'sourcing', 'ranking', 'outreach', 'preference_engine')),
    input_pseudonymized TEXT NOT NULL,
    output_pseudonymized TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_actions_recruiter ON agent_actions(recruiter_id, created_at DESC);
CREATE INDEX idx_agent_actions_type ON agent_actions(action_type, created_at);

-- Proactive alerts
CREATE TABLE agent_proactive_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL CHECK (alert_type IN ('new_match', 'pipeline_update', 'feedback_reminder', 'weekly_digest')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_alerts_recruiter ON agent_proactive_alerts(recruiter_id, is_read, created_at DESC);

-- Preference learning log (tracks how preferences evolved)
CREATE TABLE preference_learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('approval', 'rejection', 'explicit_statement', 'outreach_edit', 'outreach_response')),
    candidate_id UUID REFERENCES candidates(id),
    job_id UUID,
    features_before JSONB,
    features_after JSONB,
    preference_delta JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_preference_events_recruiter ON preference_learning_events(recruiter_id, created_at DESC);
```

### 11.2 Existing Tables Used by Agent

| Table | Usage |
|-------|-------|
| `candidates` | SourcingAgent queries candidates (tenant-scoped) |
| `candidate_skills` | Vector search on skill embeddings + structured filter |
| `candidate_timeline` | Preference learning: tracks recruiter interactions per candidate |
| `organizations` | Tenant isolation boundary |
| `users` | Links recruiter to preference profile and conversation sessions |
| `client_contacts` | Agent accesses client job requirements |
| `audit_log` | Agent actions written here + separate `agent_actions` for AI audit |

---

## 12. UI/UX Design

### 12.1 Layout

Three-panel responsive layout:

```
┌─────────────────────────────────────────────────────────────────┐
│  ATS Agent Portal — Recruiter Dashboard                        │
├──────────────┬──────────────────────────┬───────────────────────┤
│  Sidebar     │  Chat Panel (Center)     │  Context Panel (Right)│
│  (240px)     │  (flex)                  │  (320px)              │
│              │                          │                       │
│ [+ New Chat] │  ┌──────────────────┐    │  📋 Open Jobs         │
│              │  │ 🤖 Proactive     │    │  ────────────         │
│  Conversations│     Alert          │    │                       │
│  ─────────── │  │ I found 3 strong  │    │  TCS — Java Lead    │
│  • TCS Java  │     matches for     │    │  Wipro — PM          │
│  • Wipro PM  │     your TCS Java   │    │  Infy — Data Scientist│
│  • Infy Dev  │     role            │    │                       │
│              │     [View Matches]  │    │  ⭐ Top Matches       │
│  ⚙ Settings  │  └──────────────────┘    │  ────────────         │
│              │                          │                       │
│              │  ──────────────────────  │  1. Jane Doe          │
│              │                          │  Sr. Java Developer   │
│              │  👤 "Find candidates for │  ★★★★★ 92%            │
│              │   TCS Java role"         │  [View] [Submit]      │
│              │                          │                       │
│              │  🤖 Here are your top    │  2. John Smith        │
│              │     matches:             │  Sr. Python Dev       │
│              │                          │  ★★★★☆ 87%            │
│              │  ┌──────────────────┐    │  [View] [Submit]      │
│              │  │ 🃏 Jane Doe      │    │                       │
│              │  │ Title: Sr. Java  │    │  📊 Recent Activity   │
│              │  │ Exp: 7 years     │    │  ────────────         │
│              │  │ Fit: 92%         │    │  • Submitted Jane to  │
│              │  │ [View] [Submit]  │    │    TCS Java Lead      │
│              │  └──────────────────┘    │  • Rejected 2 candidates│
│              │  ┌──────────────────┐    │  • Updated preferences │
│              │  │ 🃏 John Smith    │    │                       │
│              │  │ ...              │    │                       │
│              │  └──────────────────┘    │                       │
│              │                          │                       │
│              │  ──────────────────────  │                       │
│              │  [Type a message...] 📎  │                       │
│              └──────────────────────────┴───────────────────────┘
```

### 12.2 Component Inventory

| Component | Props | State | Data Source |
|-----------|-------|-------|-------------|
| `ChatWindow` | `sessionId?`, `onAlertClick` | Local message queue, input text | SWR (history), SSE (streaming) |
| `MessageBubble` | `message: AgentMessage` | Expanded/collapsed | Props |
| `CandidateCard` | `candidate, fitScore, strengths, gaps, actions` | Expanded details | API on expand |
| `JobCard` | `job, submissionStatus` | Collapsed/expanded | SWR |
| `ProactiveAlert` | `alert` | Dismissed/read | SSE push |
| `PreferencePanel` | `recruiterId` | Edit mode | API (GET/PUT) |
| `ContextPanel` | `activeTab` | Tab selection | SWR (jobs, matches, activity) |
| `ActionButtons` | `actions: AgentAction[]` | Loading/success/error | API call on click |

### 12.3 Agent Message Schema

```typescript
interface AgentMessage {
  id: string;
  role: 'agent' | 'user' | 'system';
  content: string;                    // Natural language response
  cards: StructuredCard[];            // Visual cards embedded in message
  actions: AgentAction[];             // Action buttons below message
  sources: SourceRef[];               // Data provenance
  confidence?: number;                // 0.0 – 1.0
  isProactive?: boolean;              // Agent-initiated vs. user-initiated
  createdAt: string;                  // ISO timestamp
}

type StructuredCard =
  | { type: 'candidate'; data: CandidateProfile; fitScore: number; strengths: string[]; gaps: string[] }
  | { type: 'job'; data: JobRequisition }
  | { type: 'alert'; data: ProactiveAlertData }
  | { type: 'summary'; data: AgentSummaryData }
  | { type: 'preference'; data: PreferenceUpdateData };

interface AgentAction {
  id: string;
  label: string;                      // Button text: "Approve", "Submit", "Reject"
  type: 'approve' | 'reject' | 'submit' | 'edit_preference' | 'schedule_interview' | 'draft_outreach';
  payload: Record<string, unknown>;   // Candidate ID, job ID, etc.
  confirmation?: string;              // Confirmation dialog text
}

interface SourceRef {
  type: 'internal_db' | 'job_board' | 'sub_vendor' | 'client_portal';
  identifier: string;                 // Source-specific ID
  timestamp: string;
}
```

### 12.4 UX Principles

1. **AI output is always distinguishable** — "AI-generated" badge, distinct styling, confidence score visible
2. **Human approval gate** — Every submission, rejection, and outreach send requires explicit recruiter action
3. **Progressive disclosure** — Chat shows summaries; click to expand full candidate profile
4. **Preference transparency** — Recruiter can see, edit, and override all learned preferences
5. **Proactive but not annoying** — Alerts are batched (max 3/hour), configurable, dismissible
6. **Error recovery** — If agent is uncertain, it asks clarifying questions instead of guessing
7. **Consistent with ATS conventions** — Matches existing ATS color scheme, typography, and interaction patterns

---

## 13. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Backend Framework** | FastAPI (existing) | Already in use, async support, built-in OpenAPI, middleware ecosystem |
| **Agent Framework** | LangGraph (StateGraph) | Stateful agent loops, persistent memory, tool calling, MCP support, TypeScript SDK available |
| **LLM Provider** | OpenAI GPT-4o | Via Unified AI Middleware Gateway with PII redaction, ZDR agreement |
| **Vector Search** | pgvector (PostgreSQL extension) | Co-located with existing DB, hybrid search (vector + structured), no new infrastructure |
| **Memory Store** | LangChain InMemoryStore (session) + PostgreSQL (long-term) | Ephemeral session memory, persistent long-term for GDPR compliance |
| **Real-time Updates** | Server-Sent Events (SSE) | Simpler than WebSocket for server→client push; native FastAPI support |
| **Task Queue** | ARQ (Async Redis Queue) | Lightweight, works with existing Redis infrastructure, async-native |
| **Frontend** | Next.js 14 + React 18 + TypeScript + Tailwind CSS | No frontend exists; Next.js for SSR/SSG, Tailwind for rapid UI development |
| **State Management** | React Query (TanStack Query) + React state | Server-state caching + local UI state |
| **Styling** | Tailwind CSS + Headless UI components | Rapid development, accessible components, themeable |
| **Embedding Model** | OpenAI text-embedding-3-small (1536-dim) | Via AI Middleware Gateway; consistent with LLM provider |

---

## 14. Development Milestones

### Phase 1: Agent Foundation (Weeks 1–3)

**Deliverables:**
- New database tables: `recruiter_preferences`, `agent_conversation_sessions`, `agent_conversation_messages`, `agent_actions`, `agent_proactive_alerts`, `preference_learning_events`
- Alembic migration for all new tables
- Agent Gateway API: `/api/v1/agent/conversation` (POST), `/api/v1/agent/conversation/{session_id}` (GET)
- Orchestrator agent (LangGraph StateGraph) with basic intent parsing
- Preference Engine: JSONB storage for explicit preferences, GET/PUT endpoints
- Auth middleware integration: JWT validation, tenant isolation, recruiter context loading
- Basic chat UI: ChatWindow, MessageBubble, input field, SSE streaming

**Acceptance Criteria:**
- Recruiter can send a message and receive a streamed agent response
- Agent can parse simple intents ("show my preferences", "what jobs do I have open")
- Explicit preferences can be set and retrieved via API
- All agent actions are logged to `agent_actions` table

### Phase 2: Sourcing + Ranking (Weeks 4–7)

**Deliverables:**
- SourcingAgent: `search_candidates_db()`, `search_job_boards()`, `get_job_details()` tools
- pgvector integration: skill embeddings, hybrid search (vector + structured filters)
- RankingAgent: `compute_fit_score()`, `identify_gaps()`, `get_recruiter_preferences()` tools
- Fit score computation: weighted combination of skill match, experience match, preference alignment
- CandidateCard component: fit score visualization, strengths/gaps display, action buttons
- Quick Review mode: batch candidate review with approve/reject/flag

**Acceptance Criteria:**
- Recruiter can type "Find candidates for [job]" and receive ranked candidate cards
- Vector search returns relevant results within 500ms
- Fit scores correlate with recruiter approval rate (>85% of top-10 approved)
- Quick Review processes 50+ candidates in under 5 minutes

### Phase 3: Preference Learning (Weeks 8–10)

**Deliverables:**
- Implicit preference learning: pgvector embedding updates from recruiter actions
- Preference Learning Event tracking: `preference_learning_events` table writes
- Learning loop: auto-update implicit preferences after each review batch
- PreferencePanel UI: show explicit + implicit preferences, weekly learning digest
- Confidence scoring: agent confidence on responses, low-confidence flagging
- Bias monitoring: offline statistical bias checks on aggregated pseudonymized data

**Acceptance Criteria:**
- Implicit preferences update within 1 minute of recruiter action
- Preference accuracy >90% alignment with recruiter actions (measured weekly)
- Recruiter can view and override all learned preferences
- Weekly learning digest is generated and delivered to recruiter

### Phase 4: Outreach Agent (Weeks 11–12)

**Deliverables:**
- OutreachAgent: `get_candidate_contact()`, `get_job_context()`, `generate_outreach()`, `get_email_templates()` tools
- Template engine: job-specific templates with candidate personalization
- Draft approval flow: recruiter reviews, edits, approves outreach drafts
- Email integration: SendGrid/SMTP for delivery (after approval)
- Style learning: track recruiter edits to drafts, update outreach style preferences

**Acceptance Criteria:**
- Agent generates personalized outreach drafts within 3 seconds
- >60% of AI-drafted outreach used without major edits
- Recruiter approval required before any email is sent
- Outreach style preferences improve draft acceptance rate over time

### Phase 5: Chat UI Polish (Weeks 13–16)

**Deliverables:**
- Full Chat UI: sidebar, chat panel, context panel, responsive layout
- ProactiveAlert component: banner for agent-initiated alerts
- ContextPanel: open jobs, top matches, recent activity (tabbed)
- AI output distinction: "AI-generated" badges, visual styling
- Action buttons: approve, reject, submit, edit preferences, schedule interview
- Error states: loading, error, empty state, offline fallback
- Accessibility: WCAG 2.1 AA compliance

**Acceptance Criteria:**
- Chat UI renders in <200ms (Lighthouse)
- All AI-generated content is visually distinguishable
- Proactive alerts delivered within 2 seconds of generation
- WCAG 2.1 AA compliance verified

### Phase 6: Proactive Monitor (Weeks 17–18)

**Deliverables:**
- ARQ cron job: sourcing pulse every 30 minutes per active recruiter
- Proactive alert generation: match score threshold (default 0.85)
- Alert batching: max 3 alerts per hour per recruiter
- Notification preferences: recruiter can configure alert frequency and types
- SSE push: real-time alert delivery to Chat UI

**Acceptance Criteria:**
- Sourcing pulse completes for all recruiters within 30-minute window
- >70% of proactive alerts lead to recruiter review
- Alert fatigue: <10% of recruiters disable proactive alerts
- SSE latency <2 seconds from alert generation to UI display

### Phase 7: Compliance + Polish (Weeks 19–20)

**Deliverables:**
- EU AI Act audit trail: complete `agent_actions` log, export capability
- GDPR erasure: DELETE endpoint for recruiter data (preferences, conversations, actions)
- Bias monitoring: automated weekly bias reports, admin alerts
- Performance optimization: pgvector index tuning, agent response time optimization
- UX polish: micro-interactions, animations, loading states, empty states
- Integration testing: end-to-end recruiter workflow tests
- Security review: penetration testing, PII redaction verification

**Acceptance Criteria:**
- 100% of agent actions logged with pseudonymized input/output
- GDPR erasure completes within 24 hours of request
- Bias reports generated weekly, zero unaddressed bias flags
- p95 agent response time <15 seconds
- All integration tests passing

---

## 15. API Reference

### 15.1 Agent Gateway Endpoints

#### POST `/api/v1/agent/conversation`

Send a message to the agent and receive a streamed response.

**Request:**
```json
{
  "message": "Find me strong candidates for the TCS Java lead role",
  "session_id": "uuid-or-null-for-new-session"
}
```

**Response (SSE stream):**
```
event: message_start
data: {"session_id": "uuid", "timestamp": "2026-07-22T10:00:00Z"}

event: content
data: {"type": "text", "content": "Here are your top matches:"}

event: card
data: {"type": "candidate", "data": {...}, "fitScore": 0.92}

event: action
data: {"id": "approve_1", "label": "Approve", "type": "approve", "payload": {"candidate_id": "uuid"}}

event: message_end
data: {"confidence": 0.88, "sources": [{"type": "internal_db", "identifier": "candidates"}]}
```

**Error Response (400):**
```json
{
  "error": "Invalid message: too short",
  "code": "INVALID_INPUT"
}
```

#### GET `/api/v1/agent/conversation/{session_id}`

Retrieve conversation history for a session.

**Response:**
```json
{
  "session_id": "uuid",
  "title": "TCS Java Sourcing",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Find me strong candidates",
      "created_at": "2026-07-22T10:00:00Z"
    },
    {
      "id": "uuid",
      "role": "agent",
      "content": "Here are your top matches:",
      "cards": [...],
      "actions": [...],
      "sources": [...],
      "confidence": 0.88,
      "created_at": "2026-07-22T10:00:05Z"
    }
  ]
}
```

#### GET/PUT `/api/v1/agent/preferences`

Read or update explicit preferences.

**GET Response:**
```json
{
  "explicit": {
    "min_experience_years": 5,
    "required_visa_status": "US_work_authorization",
    "preferred_locations": ["NYC", "Remote"],
    "max_notice_period_days": 30
  },
  "implicit_scores": {
    "cloud_experience": 0.85,
    "leadership_experience": 0.72,
    "startup_experience": 0.30
  },
  "last_updated": "2026-07-22T10:00:00Z"
}
```

**PUT Request:**
```json
{
  "explicit": {
    "min_experience_years": 5,
    "required_visa_status": "US_work_authorization",
    "preferred_locations": ["NYC", "Remote"],
    "max_notice_period_days": 30,
    "preferred_industries": ["fintech", "healthcare"]
  }
}
```

#### GET `/api/v1/agent/proactive/alerts`

Retrieve proactive alerts for the current recruiter.

**Response:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "alert_type": "new_match",
      "title": "3 strong matches for TCS Java Lead",
      "body": "Jane Doe (92%), John Smith (87%), ...",
      "data": {"job_id": "uuid", "candidate_count": 3, "top_score": 0.92},
      "is_read": false,
      "created_at": "2026-07-22T09:30:00Z"
    }
  ]
}
```

#### GET `/api/v1/agent/action-log`

EU AI Act compliant audit trail.

**Query Params:** `?recruiter_id=uuid&start_date=2026-01-01&end_date=2026-07-22&limit=100`

**Response:**
```json
{
  "actions": [
    {
      "id": "uuid",
      "action_type": "source",
      "agent_name": "sourcing",
      "input_pseudonymized": "search: java lead, client: TCS",
      "output_pseudonymized": "returned 50 candidates",
      "created_at": "2026-07-22T10:00:00Z"
    }
  ],
  "total": 1247,
  "page": 1,
  "per_page": 100
}
```

---

## 16. Out-of-Scope for Version 1 (Cross-Reference with ats-ai.md)

| Feature (ats-ai.md) | Status in Agent Portal | Notes |
|---------------------|----------------------|-------|
| Multi-tenant foundation | ✅ Existing | Agent Gateway uses existing TenantMiddleware |
| RBAC | ✅ Existing | Agent endpoints use existing auth middleware |
| Candidate management | ✅ Existing | Agent queries existing Candidate model |
| Job requisition management | ✅ Existing | Agent uses existing job data |
| CRM & Outreach | ⚠️ Partial | Outreach Agent added; Exchange/Google Workspace sync in Phase 4+ |
| Client Submission Workflow | ✅ Existing | Agent integrates with existing client portal |
| Placement & Fee Tracking | ⚠️ Partial | Placement recording in MVP; fee tracking out of scope |
| Reporting | ⚠️ Partial | Agent action analytics in MVP; full dashboards in Phase 4+ |
| AI Resume Parsing | ⚠️ Future | Not in MVP agent scope; existing ATS feature |
| AI Chatbot (candidate-facing) | ⚠️ Future | Candidate-facing AI chatbot is separate from recruiter agent |
| AI Job Recommendations (candidate-facing) | ⚠️ Future | Separate from recruiter agent |
| Magic Link portals | ✅ Existing | Client portal magic links unchanged |
| Direct employer self-service | ❌ Out of scope | Per ats-ai.md V1 exclusion |
| Autonomous AI rejection | ❌ Never | Per EU AI Act compliance |
| External ATS/HRIS integrations | ❌ Out of scope | V1 exclusion |

---

## 17. Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An AI system that perceives its environment, makes decisions, and takes actions to achieve goals. In this system, the Orchestrator + Specialist Agents. |
| **Orchestrator Agent** | The central agent that receives user input, parses intent, delegates to specialists, and synthesizes responses. |
| **Specialist Agent** | A focused agent with a specific domain: Sourcing, Ranking, or Outreach. |
| **Preference Engine** | The component that stores, updates, and applies recruiter preferences (explicit + implicit). |
| **Explicit Preference** | A hard rule set directly by the recruiter (e.g., "only US work authorization"). |
| **Implicit Preference** | A learned pattern derived from recruiter actions (e.g., "consistently approves candidates with cloud experience"). |
| **Sourcing Pulse** | A periodic background check (every 30 min) for new candidate matches. |
| **Fit Score** | A 0–1 score representing how well a candidate matches a job requirement, weighted by recruiter preferences. |
| **Proactive Alert** | An agent-initiated notification when a strong candidate match is found. |
| **Structured Card** | A visual component embedded in agent messages showing candidate profiles, job details, or actions. |
| **PII Redaction** | The process of stripping personally identifiable information before sending data to external LLMs. |
| **ZDR** | Zero Data Retention — LLM provider agreement that no data is stored or used for training. |
| **EU AI Act** | European Union regulation on artificial intelligence, classifying candidate matching as High-Risk AI. |
| **pgvector** | A PostgreSQL extension for vector similarity search, used for skill embeddings and implicit preferences. |
| **LangGraph** | An open-source framework for building stateful, multi-actor applications with LLMs, used as the agent orchestration framework. |
| **SSE** | Server-Sent Events — a technology for pushing real-time updates from server to browser. |
| **ARQ** | Async Redis Queue — a lightweight async task queue for Python, used for the proactive monitor. |

---

## 18. Appendix

### A. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-22 | Agent framework: LangGraph over AutoGen | LangGraph has TypeScript SDK (full-stack consistency), lighter weight, better state management, MCP support |
| 2026-07-22 | Agent pattern: Orchestrator + Specialists over single agent | Multi-domain workflow (sourcing, ranking, outreach) benefits from specialization; easier to scale |
| 2026-07-22 | Memory: pgvector over separate vector DB | Co-located with existing PostgreSQL; no new infrastructure; hybrid search (vector + structured) |
| 2026-07-22 | Real-time: SSE over WebSocket | Simpler implementation; server→client only (no client→server push needed); native FastAPI support |
| 2026-07-22 | Task queue: ARQ over Celery | Existing Redis infrastructure; async-native; lighter weight; fewer dependencies |
| 2026-07-22 | Frontend: Next.js over Vue/Svelte | TypeScript support (consistent with LangGraph TS SDK); SSR for SEO on career pages; largest ecosystem |
| 2026-07-22 | Embedding model: OpenAI text-embedding-3-small | Consistent with LLM provider (GPT-4o); 1536-dim sufficient for skill matching; via AI Middleware Gateway |

### B. References

| Document | Location |
|----------|----------|
| Base ATS PRD | `/ats-ai.md` |
| Staffing Co. Scope Notes | `/notes.md` |
| AI-Native Features Spec | `/docs/second-opinion/2026-07-21-ai-native-features-spec-mimo-review.md` |
| Core Features Spec | `/docs/second-opinion/2026-07-21-core-features-spec-mimo-review.md` |
| Agent Architecture Design Spec | `/docs/superpowers/specs/2026-07-22-agent-first-recruiter-portal-design.md` |
| Existing Backend Models | `/backend/app/models/` |
| Existing Backend Routes | `/backend/app/routes/` |
| Existing Backend Services | `/backend/app/services/` |
