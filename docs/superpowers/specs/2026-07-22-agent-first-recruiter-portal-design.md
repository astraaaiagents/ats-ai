# Design Spec: Agent-First AI-Native Recruiter Client Portal

**Date:** 2026-07-22
**Status:** Approved
**Scope:** Recruiter-facing client portal with self-learning AI agent
**PRD Reference:** ats-ai.md (base ATS), notes.md (staffing co. scope)

---

## 1. System Overview

The client portal is an **agent-first** experience where the recruiter interacts through natural language conversation. A central orchestrator agent coordinates specialist agents that handle sourcing, ranking, and outreach. The agent **learns** each recruiter's candidate matching preferences over time, becoming more accurate at surfacing relevant candidates.

**Key principle:** The recruiter initiates or receives proactive suggestions from the agent. Every action (especially candidate submission) requires explicit human approval.

---

## 2. Component Architecture

### 2.1 Core Components

| Component | Responsibility | Tech |
|-----------|---------------|------|
| **Chat UI** | Conversational interface with structured cards | Next.js + React + Tailwind |
| **Agent Gateway** | FastAPI endpoint receiving messages, routing to orchestrator, streaming responses | FastAPI + new `/api/v1/agent/` routes |
| **Orchestrator Agent** | Central coordinator. Parses intent, delegates to specialists, synthesizes responses | LangGraph StateGraph |
| **Sourcing Agent** | Searches internal candidate DB, job boards, sub-vendors. Returns candidate lists | LangChain tool + pgvector |
| **Ranking Agent** | Applies learned recruiter preferences to rank candidates. Computes fit scores + gap analysis | Preference engine + LLM scoring |
| **Outreach Agent** | Drafts personalized emails/messages. Recruiter approves before sending | Template engine + LLM |
| **Preference Engine** | Stores/updates recruiter preference profiles. Learns from approvals, rejections, edits | PostgreSQL JSONB + pgvector |
| **Memory Store** | Session context + long-term memory of interactions | LangChain InMemoryStore + pgvector |
| **Proactive Monitor** | Background service checking for new matches, pipeline changes, alerts | ARQ task queue + cron |

### 2.2 Data Flows

**Reactive (recruiter initiates):**
```
Recruiter: "Find me strong candidates for the TCS Java lead role"
  → Agent Gateway receives message
  → Orchestrator parses intent → delegates to SourcingAgent
  → SourcingAgent searches DB (vector + structured filters)
  → Results → RankingAgent applies learned preferences
  → Orchestrator synthesizes → returns structured candidate cards to Chat UI
```

**Proactive (agent initiates):**
```
Proactive Monitor detects new candidates matching open jobs
  → Monitor triggers Orchestrator with "sourcing pulse"
  → Orchestrator delegates to SourcingAgent + RankingAgent
  → Top matches → Orchestrator generates proactive alert
  → Alert pushed to Chat UI via SSE: "I found 3 strong matches for your TCS Java role"
```

---

## 3. Agent Architecture

### 3.1 Orchestrator Pattern

Hierarchical multi-agent pattern. The Orchestrator wraps specialist agents as callable tools, enabling dynamic delegation based on user intent.

**Orchestrator responsibilities:**
- Receive messages from Chat UI via Agent Gateway
- Parse intent using LLM function calling / tool selection
- Delegate to specialists by calling their tools
- Synthesize specialist outputs into coherent responses
- Manage conversation state and trigger proactive checks
- Act as data pipeline controller between specialists

### 3.2 Specialist Agents (MVP)

| Agent | System Prompt Focus | Tools Available | Output |
|-------|--------------------|-----------------|--------|
| **SourcingAgent** | Candidate sourcing expert. Search across internal databases, job boards, sub-vendors. | `search_candidates_db()`, `search_job_boards()`, `search_sub_vendors()`, `get_job_details()` | List of candidate profiles with match metadata |
| **RankingAgent** | Candidate ranking expert. Evaluate fit against job requirements using learned recruiter preferences. | `compute_fit_score()`, `identify_gaps()`, `get_recruiter_preferences()`, `compare_candidates()` | Ranked list with fit scores, strength/gap analysis |
| **OutreachAgent** | Outreach expert. Draft personalized, job-specific messages to engage candidates. | `get_candidate_contact()`, `get_job_context()`, `generate_outreach()`, `get_email_templates()` | Drafted email/message with subject, body, CTA |

### 3.3 Agent Communication

The Orchestrator does NOT pass raw candidate data between specialists. Each specialist receives only the data it needs, minimizing LLM context window usage and cost.

```
Orchestrator receives: "Find me strong candidates for TCS Java role #123"
  → Orchestrator calls: SourcingAgent.search_candidates_db(query="Java lead", filters={client:"TCS"})
  → SourcingAgent returns: [Candidate A, Candidate B, Candidate C]
  → Orchestrator calls: RankingAgent.compute_fit_score(candidates=[...], job_id=123)
  → RankingAgent returns: [{candidate: A, score: 0.92, strengths: [...], gaps: [...]}]
  → Orchestrator synthesizes → returns structured cards to Chat UI
```

---

## 4. Preference Learning & Memory

### 4.1 Two-Tier Preference Model

**Explicit Preferences** (PostgreSQL JSONB on `recruiter_preferences` table):
- Hard rules set by recruiter: "I only submit candidates with 5+ years Java", "Prefer within 50 miles of NYC", "Never submit without US work authorization"
- Updated via natural language: "Remember, I don't want candidates with less than 3 years experience"

**Implicit Preferences** (PostgreSQL pgvector embeddings + scoring metadata):
- Learned patterns from recruiter actions: consistent rejections of candidates from certain industries, preferred outreach phrasing, response patterns
- Auto-updated from: approvals, rejections (with optional reason), time-spent-on-card signals, outreach response rates

### 4.2 Learning Loop

1. Recruiter reviews N candidates from SourcingAgent
2. Recruiter approves/rejects with optional reason (e.g., "not enough leadership experience")
3. RankingAgent logs: approval/rejection + candidate features + job context
4. Preference Engine updates:
   - Explicit: no change (recruiter didn't state a rule)
   - Implicit: embedding vector adjusted — "leadership experience" gains higher weight
5. Next sourcing pulse: candidates with leadership experience get boosted fit scores

### 4.3 Memory Store

| Memory Type | Storage | Lifetime | Content |
|------------|---------|----------|---------|
| **Session Memory** | In-memory (LangChain InMemoryStore) | Current conversation | Recent messages, tools called, intermediate results |
| **Conversation Memory** | PostgreSQL `agent_conversation_messages` | Permanent (pseudonymized per GDPR) | Full conversation history, recruiter actions, agent responses |
| **Preference Memory** | PostgreSQL `recruiter_preferences` (JSONB + pgvector) | Permanent | Explicit rules + implicit preference vectors |
| **Action Memory** | PostgreSQL `agent_actions` | Permanent (audit trail) | Every tool call, agent decision, data accessed — EU AI Act compliance |

### 4.4 Preference Update Triggers

- **After each review batch:** Recruiter approves/rejects N candidates → implicit preferences updated
- **After explicit statement:** "I prefer candidates who know AWS" → explicit preference added
- **After outreach response:** Candidate responds positively → outreach style reinforced
- **Weekly digest:** Agent summarizes learning: "This week you preferred candidates with cloud experience. I've updated my ranking."

### 4.5 Privacy & Compliance (EU AI Act)

- All preference data is pseudonymized (linked to recruiter ID, not PII)
- Preference vectors stored separately from conversation content
- GDPR "right to be forgotten" = delete recruiter's preference vectors + conversation history
- Full audit trail in `agent_actions` table

---

## 5. API Architecture

### 5.1 Agent Gateway API (New Routes)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/agent/conversation` | POST | Send message to agent |
| `/api/v1/agent/conversation/{session_id}` | GET | Retrieve conversation history |
| `/api/v1/agent/preferences` | GET | Read recruiter preferences |
| `/api/v1/agent/preferences` | PUT | Update explicit preferences |
| `/api/v1/agent/preferences/implicit` | GET | Read implicit preference scores |
| `/api/v1/agent/proactive/alerts` | GET | Get proactive alerts |
| `/api/v1/agent/action-log` | GET | EU AI Act audit trail |

### 5.2 Agent Gateway Internal Flow

```
POST /api/v1/agent/conversation
  → Auth middleware: validate JWT, extract recruiter_id + tenant_id
  → Load recruiter's conversation session (from Memory Store)
  → Load recruiter's preference profile (from Preference Engine)
  → Create Orchestrator instance with model_client, tools, memory, preferences
  → Run orchestrator.run(task=user_message)
  → Stream response back to Chat UI
  → Log action to agent_actions table (audit)
```

### 5.3 Integration with Existing Backend

| Existing Component | Agent Integration |
|-------------------|-------------------|
| `Candidate` model | SourcingAgent queries via SQLAlchemy (tenant-scoped) |
| `CandidateSkill` model | Vector search on skill embeddings + structured filter |
| `CandidateTimeline` model | Used for preference learning (tracks recruiter interactions) |
| `Organization` model | Tenant isolation — agent never crosses tenant boundaries |
| `User` model | Links recruiter to preference profile and conversation sessions |
| `ClientContact` model | Agent accesses client job requirements |
| `AuditLog` model | Agent actions written here + separate `agent_actions` table |

### 5.4 Proactive Monitor

```
ARQ Cron Job (every 30 min)
  → For each active recruiter:
    1. Fetch open job requisitions
    2. Fetch recruiter's implicit + explicit preferences
    3. Query new candidates in DB (since last check)
    4. Run RankingAgent on new candidates
    5. If top match score > threshold → generate proactive alert
    6. Push alert to Chat UI (SSE)
```

---

## 6. UI/UX Architecture

### 6.1 Layout

Three-panel layout:
- **Left sidebar:** New chat button + conversation history
- **Center:** Chat panel with messages, structured cards, input field
- **Right context panel:** Open jobs, top matches, recent activity (tabbed)

### 6.2 Components

| Component | Responsibility | State |
|-----------|---------------|-------|
| `ChatWindow` | Message list, input, streaming responses | React state + SWR |
| `MessageBubble` | Renders agent/user messages with structured cards | Props |
| `CandidateCard` | Structured card: profile, fit score, actions | Fetches on expand |
| `JobCard` | Job details, submission status, client info | SWR |
| `ProactiveAlert` | Banner for agent-initiated alerts | SSE connection |
| `PreferencePanel` | Show/edit explicit preferences, learning summary | API call |
| `ContextPanel` | Right sidebar: jobs, matches, activity | Tabbed, context-aware |

### 6.3 Message Types (Agent Response Schema)

```typescript
type AgentMessage = {
  id: string;
  role: 'agent' | 'user';
  content: string;           // Natural language response
  cards: StructuredCard[];   // Candidate cards, job cards, action buttons
  actions: AgentAction[];    // Approve, reject, submit, edit preferences
  sources: SourceRef[];      // Data origin (DB, job board, etc.)
  confidence?: number;       // Agent's confidence in response
};

type StructuredCard =
  | CandidateCard    // Candidate profile with fit score
  | JobCard          // Job requisition details
  | AlertCard        // Proactive alert
  | SummaryCard      // Agent-generated summary
  | ActionCard;      // Interactive action buttons
```

### 6.4 UX Principles

1. AI output is always visually distinguishable (badge, styling)
2. Human approval gate on every submission
3. Progressive disclosure (summaries in chat, expand for details)
4. Preference transparency (recruiter sees what agent learned, can override)
5. Proactive but not annoying (alerts batched, configurable, non-blocking)

---

## 7. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend Framework | FastAPI (existing) | Already in use, async support, OpenAPI |
| Agent Framework | LangGraph (StateGraph) | Stateful agent loops, persistent memory, tool calling, MCP support, TypeScript available |
| LLM Provider | OpenAI GPT-4o (via AI Middleware Gateway) | Existing ats-ai.md architecture with PII redaction |
| Vector Search | pgvector (PostgreSQL extension) | Co-located with existing DB, hybrid search (vector + structured) |
| Memory Store | LangChain InMemoryStore (session) + PostgreSQL (long-term) | Ephemeral session, persistent long-term for GDPR |
| Real-time Updates | Server-Sent Events (SSE) | Simpler than WebSocket for server→client push |
| Task Queue | ARQ (Async Redis Queue) | Lightweight, works with existing Redis, async-native |
| Frontend | Next.js + React + Tailwind | No frontend exists; rapid development |
| State Management | React Query (SWR) + React state | Data fetching + local UI state |

---

## 8. Database Schema Additions

```sql
-- Recruiter preference profiles
CREATE TABLE recruiter_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    explicit_preferences JSONB NOT NULL DEFAULT '{}',
    implicit_preference_vector vector(1536),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Agent conversation sessions
CREATE TABLE agent_conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent conversation messages
CREATE TABLE agent_conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_conversation_sessions(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    cards JSONB,
    actions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent action audit log (EU AI Act compliance)
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES agent_conversation_sessions(id),
    action_type TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    input_pseudonymized TEXT NOT NULL,
    output_pseudonymized TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Proactive alerts
CREATE TABLE agent_proactive_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    alert_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 9. Implementation Roadmap

| Phase | Deliverables | Effort |
|-------|-------------|--------|
| **Phase 1: Agent Foundation** | Agent Gateway API, Orchestrator agent, basic chat endpoint, preference store (JSONB) | 2-3 weeks |
| **Phase 2: Sourcing + Ranking** | SourcingAgent, RankingAgent, pgvector integration, candidate search tools, fit scoring | 3-4 weeks |
| **Phase 3: Preference Learning** | Implicit preference learning loop, preference engine, learning summary UI | 2-3 weeks |
| **Phase 4: Outreach Agent** | OutreachAgent, email drafting, template engine, recruiter approval flow | 2 weeks |
| **Phase 5: Chat UI** | Next.js frontend, chat window, candidate cards, proactive alerts (SSE), preference panel | 3-4 weeks |
| **Phase 6: Proactive Monitor** | ARQ cron jobs, sourcing pulse, alert push, notification preferences | 1-2 weeks |
| **Phase 7: Compliance + Polish** | EU AI Act audit trail, GDPR erasure, bias monitoring, UX polish | 2 weeks |

---

## 10. Key Decisions Summary

| Decision | Choice |
|----------|--------|
| Agent pattern | Orchestrator + 3 specialist agents (Sourcing, Ranking, Outreach) |
| Agent framework | LangGraph (StateGraph) |
| Memory | Two-tier: explicit JSONB + implicit pgvector embeddings |
| UI paradigm | Chat-first with structured cards and context panel |
| Real-time | SSE for proactive alerts |
| MVP scope | Sourcing + Ranking + Preference Learning + Chat UI |
| Compliance | EU AI Act audit trail via `agent_actions` table |
| LLM routing | Through existing Unified AI Middleware Gateway (PII redaction) |
