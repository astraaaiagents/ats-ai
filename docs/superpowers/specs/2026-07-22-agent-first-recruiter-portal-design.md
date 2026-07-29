# Design Spec: Agent-First AI-Native Recruiter Client Portal

**Date:** 2026-07-22
**Status:** Approved
**Scope:** Recruiter-facing client portal with self-learning AI agent
**PRD Reference:** agent-ats-ai.md (base ATS), notes.md (staffing co. scope)
**UI/UX Reference:** docs/superpowers/specs/2026-07-26-agent-portal-ui-ux-design.md

---

## 1. System Overview

The client portal is an **agent-first** experience where the recruiter interacts through a **hybrid interface**: an Activity Feed for chronological awareness, a Pipeline/Kanban for visual stage management, and a persistent Command Panel for agent conversation. A central orchestrator agent coordinates specialist agents that handle sourcing, ranking, and outreach. The agent **learns** each recruiter's candidate matching preferences over time, becoming more accurate at surfacing relevant candidates.

**Key principle:** The recruiter initiates or receives proactive suggestions from the agent. Every action (especially candidate submission) requires explicit human approval.

---

## 2. Component Architecture

### 2.1 Core Components

| Component | Responsibility | Tech |
|-----------|---------------|------|
| **Agent Portal UI** | Hybrid interface: Activity Feed, Pipeline/Kanban, Jobs list, Preferences, Command Panel | Next.js + React + Tailwind + Warm Indigo theme |
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
  → Command Panel receives message
  → Orchestrator parses intent → delegates to SourcingAgent
  → SourcingAgent searches DB (vector + structured filters)
  → Results → RankingAgent applies learned preferences
  → Orchestrator synthesizes → returns structured candidate cards to Command Panel
  → Feed item posted to Activity Feed
```

**Proactive (agent initiates):**
```
Proactive Monitor detects new candidates matching open jobs
  → Monitor triggers Orchestrator with "sourcing pulse"
  → Orchestrator delegates to SourcingAgent + RankingAgent
  → Top matches → Orchestrator generates proactive alert
  → Alert pushed to Command Panel via SSE + Feed item posted
```

---

## 3. Agent Architecture

### 3.1 Orchestrator Pattern

Hierarchical multi-agent pattern. The Orchestrator wraps specialist agents as callable tools, enabling dynamic delegation based on user intent.

**Orchestrator responsibilities:**
- Receive messages from Command Panel via Agent Gateway
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
  → Orchestrator synthesizes → returns structured cards to Command Panel
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
  → Stream response back to Command Panel
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
    6. Push alert to Command Panel (SSE) + post Feed item
```

---

## 6. UI/UX Architecture

### 6.1 Interaction Paradigm: Hybrid

The UI combines three interaction modes, accessible from any view:

| Mode | Role | Access |
|------|------|--------|
| **Activity Feed** | Primary default view. Chronological timeline of agent suggestions, recruiter actions, system events. Agent participates as a collaborator. | Top-level tab |
| **Pipeline / Kanban** | Job-scoped visual pipeline (Sourced → Reviewing → Submitted → Interviewing → Placed). For bottleneck spotting and stage management. | Top-level tab |
| **Command Panel** | Persistent right-side panel. Full agent conversation always visible. Natural language and slash commands. Three states (see §6.3). | Always present, right panel |

**Navigation:** Top-level tab bar (Feed | Pipeline | Jobs | Preferences | Analytics). No sidebars. Command panel persists across all tab switches.

### 6.2 Layout

#### 6.2.1 Page Structure

```
┌──────────────────────────────────────────────────────────────────┐
│  Top Nav: ⚡ ATS Agent | Feed | Pipeline | Jobs | Prefs | Ana   │
├──────────────────────────────────────────┬───────────────────────┤
│                                          │                       │
│   Main Content Area                      │  Command Panel        │
│   (switches per tab)                     │  (persistent)         │
│                                          │                       │
│   Feed: activity timeline                │  Chat thread          │
│   Pipeline: 5-col kanban                │  Action buttons       │
│   Jobs: card list                        │  Inline cards         │
│   Preferences: explicit + implicit       │  Quick action chips   │
│   Analytics: charts (future)             │  /commands            │
│                                          │                       │
└──────────────────────────────────────────┴───────────────────────┘
```

#### 6.2.2 Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| ≥1280px | Full two-panel layout (main + command panel at 340px) |
| 1024–1279px | Command panel collapses to icon; expands on click |
| 768–1023px | Single column; command panel becomes bottom sheet |
| <768px | Mobile-optimized; tabs become bottom nav; command panel is full-screen overlay |

### 6.3 Command Panel States

| State | Width | When | Features |
|-------|-------|------|----------|
| **Compact Chat** | 340px | Default | Conversation thread, input bar, quick action chips |
| **Expanded Detail** | 440px | On candidate/job card click | Full profile: avatar, contact, fit breakdown, strengths/gaps, skills, CTA buttons. Breadcrumb "← Back to chat" |
| **Side-by-Side Compare** | 440px (split) | On `/compare` command | Two 50% columns. Side-by-side fit scores, skills, gaps. Only for candidate comparison |

### 6.4 Visual Theme: Warm Indigo

**Color Palette:**
- Surface base: `#faf9f7` (warm off-white), raised: `#f5f4f1`, hover: `#eeedea`, border: `#e2e0db`
- Primary: `#4f46e5` (indigo 600), light: `#eef2ff` (indigo 50), hover: `#4338ca` (indigo 700)
- Success: `#16a34a` (green 600), Warning: `#d97706` (amber 600), Error: `#dc2626` (red 600)
- AI/Agent: `#9333ea` (purple 600)
- Text: primary `#1c1917`, secondary `#57534e`, tertiary `#a8a29e`

**Typography:** Font stack `Inter, 'SF Pro Text', system-ui, -apple-system, sans-serif`
- H1: 24px/700, H2: 18px/600, H3: 15px/600, Body: 14px/400, Body small: 13px/400, Caption: 11px/500

**Spacing:** 4px base scale (4, 8, 12, 16, 24, 32, 48, 64)
**Border Radius:** Cards/panels 8px, Buttons/inputs 6px, Badges/chips 4px, Avatars 50%, Pill tags 9999px

### 6.5 AI Output Distinction (EU AI Act)

All AI-generated content must be visually distinguishable:

| Badge | Color | When |
|-------|-------|------|
| `AI-GENERATED` | Indigo 50 bg, Indigo 600 text | Standard AI output |
| `LOW CONFIDENCE` | Amber 50 bg, Amber 600 text | Confidence <70% |
| `AGENT SUGGESTION` | Purple 50 bg, Purple 600 text | Proactive (unsolicited) output |
| `PREFERENCE UPDATED` | Purple 50 bg, Purple 600 text | Preference learning events |
| `LEARNING` | Purple 50 bg, Purple 600 text | Weekly digest, learning summaries |

Every AI output shows a confidence percentage (0–100%). Low-confidence assertions (<70%) require manual confirmation before actions.

### 6.6 View Specifications

#### 6.6.1 Activity Feed

- Chronological, reverse-chronological (newest first)
- Grouped by date: "Today", "Yesterday", date headers
- Feed item types: agent match, user message, submission event, learning digest, system alert
- Each item: left border color indicates type (indigo=AI, green=user action, purple=learning, red=alert)
- Inline actions on agent items: Approve, Review, Reject buttons
- Clicking a candidate name opens Command Panel in Expanded Detail state
- Clicking a job link navigates to Pipeline view scoped to that job

#### 6.6.2 Pipeline / Kanban

- 5 columns: Sourced → Reviewing → Submitted → Interviewing → Placed
- Column header: name + count badge
- Column widths: flex, with minimum 160px per column
- Job context bar at top with job title, req ID, "new since yesterday" counter
- Candidate cards within columns: name, title, experience, fit score + stars, skill tags
- Agent integration: "+3 new matches" card in Sourced column; gap indicators on candidate cards
- Actions: Approve/Reject inline on Reviewing cards; "→ Review" link on Sourced cards

#### 6.6.3 Jobs List

- Card-based list of all open jobs
- Each card shows: client + role, req ID, location, candidate count, pipeline summary (e.g., "8R · 3S · 1I")
- Color-coded left border: blue=healthy, yellow=needs attention, green=on track, red=critical
- Agent insights: per-card status line ("Strong pipeline", "Pipeline too thin", "No candidates yet")
- Click opens Pipeline view scoped to that job

#### 6.6.4 Preferences & Learning

**Explicit Preferences** (hard rules): list of active rules with toggle, "Add Rule" button
**Implicit / Learned Preferences**: learned patterns with name, confidence level (High/Medium/Low), evidence count, visual strength bar (0–100%)
**Weekly Learning Summary**: banner with stats, trends, Accept/Revert/Dismiss actions

#### 6.6.5 Command Panel (Detail State)

Content: avatar + name + contact info + location + work authorization; current role vs. target role; fit score breakdown (Skills Match, Experience, Preference Alignment); strengths (green) and gaps (red); skills as colored pill tags; action buttons (Approve & Submit, View Resume, Draft Outreach, Reject, Compare, Save for later); source attribution.

### 6.7 Component Tree

```
App
├── TopNav
│   ├── Logo ("⚡ ATS Agent")
│   ├── TabBar (Feed | Pipeline | Jobs | Preferences | Analytics)
│   └── NotificationBadge
│
├── MainContent (switches by active tab)
│   ├── FeedView
│   │   ├── DateGroup
│   │   │   └── FeedItem (agent | user | system | alert)
│   │   │       ├── Badge (AI-GENERATED | YOU | SUBMITTED | LEARNING | ALERT)
│   │   │       ├── Content
│   │   │       ├── InlineCard (CandidateCard | JobCard | AlertCard)
│   │   │       └── ActionButtons (Approve | Review | Reject)
│   │   └── LoadingSkeleton / EmptyState / ErrorState
│   │
│   ├── PipelineView
│   │   ├── JobContextBar
│   │   ├── PipelineColumn × 5
│   │   │   ├── ColumnHeader (name + count)
│   │   │   └── PipelineCard
│   │   │       ├── CandidateName
│   │   │       ├── RoleTitle
│   │   │       ├── FitBadge (score + stars)
│   │   │       ├── SkillTags
│   │   │       └── StageActions (→Review | Approve | Reject)
│   │   └── LoadingSkeleton / EmptyState / ErrorState
│   │
│   ├── JobsView
│   │   ├── JobCard
│   │   │   ├── JobHeader (client + role + req ID)
│   │   │   ├── PipelineSummary
│   │   │   ├── AgentInsight
│   │   │   └── StatusBorder (color-coded)
│   │   └── LoadingSkeleton / EmptyState / ErrorState
│   │
│   ├── PreferencesView
│   │   ├── ExplicitPreferences (rule list)
│   │   ├── ImplicitPreferences (learned list)
│   │   ├── LearningDigest
│   │   └── LoadingSkeleton / EmptyState / ErrorState
│   │
│   └── AnalyticsView (placeholder for Phase 3)
│
└── CommandPanel (persistent)
    ├── CompactChat (default, 340px)
    │   ├── MessageThread
    │   │   └── CommandMessage (user | agent)
    │   │       ├── RoleBadge
    │   │       ├── Content (text + optional cards)
    │   │       └── InlineActions
    │   ├── InputBar
    │   │   ├── TextInput
    │   │   ├── AttachButton
    │   │   ├── VoiceButton
    │   │   └── SendButton
    │   └── QuickActionChips (/find, /submit, /schedule, /prefs, /outreach)
    │
    ├── ExpandedDetail (440px)
    │   ├── BackButton ("← Back to chat")
    │   ├── CandidateProfile
    │   ├── FitScoreBreakdown
    │   ├── StrengthsGaps
    │   ├── SkillsTags
    │   ├── CTAActions
    │   └── SourceAttribution
    │
    └── SideBySideCompare (440px split)
        ├── CompareColumn × 2
        └── ComparisonActions
```

### 6.8 Message Types (Agent Response Schema)

```typescript
type FeedItemType = 'agent' | 'user' | 'system' | 'alert';

interface FeedItem {
  id: string;
  type: FeedItemType;
  content: string;
  badge?: string;                    // AI-GENERATED, LOW CONFIDENCE, etc.
  cards?: StructuredCard[];
  actions?: AgentAction[];
  created_at: string;
}

interface AgentMessage {
  id: string;
  role: 'agent' | 'user' | 'system';
  content: string;
  cards: StructuredCard[];
  actions: AgentAction[];
  sources: SourceRef[];
  confidence?: number;
  is_proactive?: boolean;
  created_at: string;
}

type StructuredCard =
  | { type: 'candidate'; data: CandidateProfile; fitScore: number; strengths: string[]; gaps: string[] }
  | { type: 'job'; data: JobRequisition }
  | { type: 'alert'; data: ProactiveAlertData }
  | { type: 'summary'; data: AgentSummaryData }
  | { type: 'preference'; data: PreferenceUpdateData };

interface AgentAction {
  id: string;
  label: string;
  type: 'approve' | 'reject' | 'submit' | 'edit_preference' | 'schedule_interview' | 'draft_outreach';
  payload: Record<string, unknown>;
  confirmation?: string;
}

interface SourceRef {
  type: 'internal_db' | 'job_board' | 'sub_vendor' | 'client_portal';
  identifier: string;
  timestamp: string;
}

const PIPELINE_STAGES = ['sourced', 'reviewing', 'submitted', 'interviewing', 'placed'] as const;
type PipelineStage = (typeof PIPELINE_STAGES)[number];

interface Job {
  id: string;
  req_id: string;
  client_name: string;
  role_title: string;
  location: string;
  status: 'healthy' | 'needs_attention' | 'on_track' | 'critical';
  domains: string[];
  candidate_count: number;
  pipeline_summary: string;
  agent_insight: string;
}
```

### 6.9 UX Principles

1. **AI output is always distinguishable** — "AI-generated" badge, distinct styling, confidence score visible
2. **Human approval gate** — Every submission, rejection, and outreach send requires explicit recruiter action
3. **Progressive disclosure** — Feed shows summaries; click to expand full candidate profile in Command Panel
4. **Preference transparency** — Recruiter can see, edit, and override all learned preferences in dedicated tab
5. **Proactive but not annoying** — Alerts are batched (max 3/hour), configurable, dismissible
6. **Error recovery** — If agent is uncertain, it asks clarifying questions instead of guessing; graceful degradation to manual search
7. **Hybrid interaction** — Activity Feed as primary view, Pipeline for visual management, Command Panel for agent conversation — recruiter chooses the mode per task
8. **Consistent visual system** — Warm Indigo theme, 4px spacing scale, Inter typography, uniform border radius

---

## 7. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend Framework | FastAPI (existing) | Already in use, async support, OpenAPI |
| Agent Framework | LangGraph (StateGraph) | Stateful agent loops, persistent memory, tool calling, TypeScript available |
| LLM Provider | OpenAI GPT-4o (via AI Middleware Gateway) | Existing architecture with PII redaction |
| Vector Search | pgvector (PostgreSQL extension) | Co-located with existing DB, hybrid search (vector + structured) |
| Memory Store | LangChain InMemoryStore (session) + PostgreSQL (long-term) | Ephemeral session, persistent long-term for GDPR |
| Real-time Updates | Server-Sent Events (SSE) | Simpler than WebSocket for server→client push |
| Task Queue | ARQ (Async Redis Queue) | Lightweight, works with existing Redis, async-native |
| Frontend | Next.js + React + Tailwind + Warm Indigo theme | Hybrid interaction paradigm with Feed, Pipeline, Command Panel |
| State Management | React Query (SWR) + React state + Zustand | Server-state caching + local UI state + global panel state |
| UI Components | Headless UI + custom components | Accessible, themeable, WCAG 2.1 AA compliant |

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
| **Phase 1: Agent Foundation** | Agent Gateway API, Orchestrator agent, basic chat endpoint, preference store (JSONB), CommandPanel (Compact Chat) | 2-3 weeks |
| **Phase 2: Sourcing + Ranking** | SourcingAgent, RankingAgent, pgvector integration, candidate search tools, fit scoring, FeedView, PipelineView | 3-4 weeks |
| **Phase 3: Preference Learning** | Implicit preference learning loop, preference engine, PreferencesView, LearningDigest | 2-3 weeks |
| **Phase 4: Outreach Agent** | OutreachAgent, email drafting, template engine, recruiter approval flow | 2 weeks |
| **Phase 5: Agent Portal UI** | Full hybrid UI: TopNav, TabBar, FeedView, PipelineView, JobsView, CommandPanel (all 3 states), AI badges, error/empty states | 3-4 weeks |
| **Phase 6: Proactive Monitor** | ARQ cron jobs, sourcing pulse, alert push, notification preferences | 1-2 weeks |
| **Phase 7: Compliance + Polish** | EU AI Act audit trail, GDPR erasure, bias monitoring, UX polish | 2 weeks |

---

## 10. Key Decisions Summary

| Decision | Choice |
|----------|--------|
| Agent pattern | Orchestrator + 3 specialist agents (Sourcing, Ranking, Outreach) |
| Agent framework | LangGraph (StateGraph) |
| Memory | Two-tier: explicit JSONB + implicit pgvector embeddings |
| UI paradigm | Hybrid: Activity Feed + Pipeline/Kanban + Command Panel (3 states) |
| Navigation | Top-level tabs (Feed, Pipeline, Jobs, Preferences, Analytics); no sidebars |
| Visual theme | Warm Indigo: #4f46e5 primary, #faf9f7 surface, Inter typography |
| Real-time | SSE for proactive alerts |
| MVP scope | Sourcing + Ranking + Preference Learning + Hybrid UI |
| Compliance | EU AI Act audit trail via `agent_actions` table |
| LLM routing | Through existing Unified AI Middleware Gateway (PII redaction) |
