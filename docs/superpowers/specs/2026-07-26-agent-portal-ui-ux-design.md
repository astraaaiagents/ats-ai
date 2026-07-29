# UI/UX Design Specification
## Agent-First AI-Native Recruiter Client Portal

**Date:** 2026-07-26
**Status:** Approved Design
**Based on:** PRD (`agent-ats-ai.md`), Hybrid Interaction Paradigm (brainstorming output)

---

## 1. Interaction Paradigm: Hybrid

The UI combines three interaction modes, accessible from any view:

| Mode | Role | Access |
|------|------|--------|
| **Activity Feed** | Primary default view. Chronological timeline of agent suggestions, recruiter actions, system events. Agent participates as a collaborator. | Top-level tab |
| **Pipeline / Kanban** | Job-scoped visual pipeline (Sourced → Reviewing → Submitted → Interviewing → Placed). For bottleneck spotting and stage management. | Top-level tab |
| **Command Panel** | Persistent right-side panel. Full agent conversation always visible. Natural language and slash commands. Three states (see §4). | Always present, right panel |

**Navigation:** Top-level tab bar (Feed | Pipeline | Jobs | Preferences | Analytics). No sidebars. Command panel persists across all tab switches.

---

## 2. Layout

### 2.1 Page Structure

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

### 2.2 Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| ≥1280px | Full two-panel layout (main + command panel at 340px) |
| 1024–1279px | Command panel collapses to icon; expands on click |
| 768–1023px | Single column; command panel becomes bottom sheet |
| <768px | Mobile-optimized; tabs become bottom nav; command panel is full-screen overlay |

---

## 3. Visual Theme: Warm Indigo

### 3.1 Color Palette

```
Surface base:        #faf9f7  (warm off-white)
Surface raised:      #f5f4f1  (card backgrounds)
Surface hover:       #eeedea  (hover states)
Border:              #e2e0db  (dividers, outlines)

Primary:             #4f46e5  (indigo 600 — main CTAs, active states)
Primary light:       #eef2ff  (indigo 50 — badge backgrounds)
Primary hover:       #4338ca  (indigo 700)

Success:             #16a34a  (green 600)
Warning:             #d97706  (amber 600)
Error:               #dc2626  (red 600)
AI/Agent:            #9333ea  (purple 600)

Text primary:        #1c1917  (warm black)
Text secondary:      #57534e  (warm gray 600)
Text tertiary:       #a8a29e  (warm gray 400)

Shadow:              rgba(0, 0, 0, 0.04) — card shadows
Overlay:             rgba(28, 25, 23, 0.3) — modals
```

### 3.2 Typography

Font stack: `Inter, 'SF Pro Text', system-ui, -apple-system, sans-serif`

```
H1: 24px / 700 / 1.2    — page titles
H2: 18px / 600 / 1.3    — section headings
H3: 15px / 600 / 1.4    — card titles
Body: 14px / 400 / 1.5  — main UI text
Body small: 13px / 400 / 1.5 — secondary info
Caption: 11px / 500 / 1.4   — labels, timestamps, badges
```

### 3.3 Spacing

4px base scale: 4, 8, 12, 16, 24, 32, 48, 64

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Inner padding in badges, tight gaps |
| `space-2` | 8px | Card content padding, button padding |
| `space-3` | 12px | Section spacing within panels |
| `space-4` | 16px | Panel padding, card outer margins |
| `space-6` | 24px | Section margins, page margins |
| `space-8` | 32px | Large section breaks |

### 3.4 Border Radius

| Element | Radius |
|---------|--------|
| Cards, panels | 8px |
| Buttons, inputs | 6px |
| Badges, chips | 4px |
| Avatars | 50% |
| Pill tags | 9999px |

---

## 4. Component States

### 4.1 Command Panel: Three States

| State | Width | When | Features |
|-------|-------|------|----------|
| **Compact Chat** | 340px | Default | Conversation thread, input bar, quick action chips |
| **Expanded Detail** | 440px | On candidate/job card click | Full profile: avatar, contact, fit breakdown, strengths/gaps, skills, CTA buttons. Breadcrumb "← Back to chat" |
| **Side-by-Side Compare** | 440px (split) | On /compare command | Two 50% columns. Side-by-side fit scores, skills, gaps. Only for candidate comparison |

### 4.2 AI Output Distinction (EU AI Act)

All AI-generated content must be visually distinguishable:

| Badge | Color | When |
|-------|-------|------|
| `AI-GENERATED` | Indigo 50 bg, Indigo 600 text | Standard AI output |
| `LOW CONFIDENCE` | Amber 50 bg, Amber 600 text | Confidence <70% |
| `AGENT SUGGESTION` | Purple 50 bg, Purple 600 text | Proactive (unsolicited) output |
| `PREFERENCE UPDATED` | Purple 50 bg, Purple 600 text | Preference learning events |
| `LEARNING` | Purple 50 bg, Purple 600 text | Weekly digest, learning summaries |

Every AI output also shows a confidence percentage (0–100%). Low-confidence assertions (<70%) require manual confirmation before actions.

### 4.3 Card States

| State | Visual | Applied to |
|-------|--------|------------|
| Default | White bg, subtle shadow | All cards |
| Hover | `#eeedea` background | Interactive cards |
| Selected | Indigo border (2px), `#eef2ff` bg | Active pipeline card |
| Loading | Skeleton pulse animation | Cards fetching data |
| Error | Red left border, error message | Failed actions |
| Empty | Dashed border, centered message | Empty pipeline columns |

---

## 5. View Specifications

### 5.1 Activity Feed

- Chronological, reverse-chronological (newest first)
- Grouped by date: "Today", "Yesterday", date headers
- Feed item types: agent match, user message, submission event, learning digest, system alert
- Each item: left border color indicates type (indigo=AI, green=user action, purple=learning, red=alert)
- Inline actions on agent items: Approve, Review, Reject buttons
- Clicking a candidate name opens Command Panel in Expanded Detail state
- Clicking a job link navigates to Pipeline view scoped to that job

### 5.2 Pipeline / Kanban

- 5 columns: Sourced → Reviewing → Submitted → Interviewing → Placed
- Column header: name + count badge
- Column widths: flex, with minimum 160px per column
- Job context bar at top with job title, req ID, "new since yesterday" counter
- Candidate cards within columns: name, title, experience, fit score + stars, skill tags
- Agent integration:
  - "+3 new matches" card in Sourced column
  - Gap indicators on candidate cards ("Gap: no cloud exp.")
  - Pipeline suggestions from agent in Command Panel
- Actions: Approve/Reject inline on Reviewing cards; "→ Review" link on Sourced cards
- Drag-and-drop for moving cards between stages (future enhancement; v1 uses buttons/commands)

### 5.3 Jobs List

- Card-based list of all open jobs
- Each card shows: client + role, req ID, location, candidate count, pipeline summary (e.g., "8R · 3S · 1I")
- Color-coded left border:
  - Blue = healthy pipeline, active sourcing
  - Yellow = needs attention, thin pipeline
  - Green = on track, good metrics
  - Red = critical (no candidates, approaching SLA)
- Agent insights: per-card status line ("Strong pipeline", "Pipeline too thin", "No candidates yet")
- Click opens Pipeline view scoped to that job

### 5.4 Preferences & Learning

Two sections:

**Explicit Preferences** (hard rules):
- List of active rules with toggle
- "Add Rule" button — opens command panel or inline form
- Each rule shows: rule text, status (active/inactive), edit/delete icons

**Implicit / Learned Preferences:**
- List of learned patterns with: name, confidence level (High/Medium/Low), evidence count
- Visual bar showing strength (0–100%)
- Per-item: Override (edit weight), Remove, "Show evidence" links
- Confidence thresholds:
  - High (green): 20+ consistent actions, auto-applied
  - Medium (amber): 10–19 actions, suggests but flags
  - Low (gray): <10 actions, visible but not applied

**Weekly Learning Summary:**
- Banner at bottom of preferences view
- Stats: candidates reviewed, approved, rejected, submitted
- Trends: "Strong preference for AWS (+22%) vs. last week"
- Actions: Accept, Revert to last week, Dismiss

### 5.5 Command Panel (Detail State)

Accessible from any view. Shows when user clicks a candidate name or card.

Content:
- Avatar + name + contact info + location + work authorization
- Current role vs. target role (side by side)
- Fit score breakdown: Skills Match, Experience, Preference Alignment (three metric cards)
- Strengths (green) and Gaps (red) — side-by-side lists
- Skills as colored pill tags (matched skills in blue, gaps in gray with "(gap)" label)
- Action buttons: Approve & Submit, View Resume, Draft Outreach, Reject, Compare, Save for later
- Source attribution: "Sourced from Internal DB · Received Jul 24, 2026"

---

## 6. Interaction Patterns

### 6.1 Agent Command Flow

1. Recruiter types natural language or slash command in Command Panel input
2. Message appears in chat thread with "You" badge
3. Agent responds with streaming text + inline cards + action buttons
4. Response shows AI-GENERATED badge + confidence score
5. Each action (Approve, Submit, etc.) is logged to agent audit trail
6. Agent actions that modify state (move in pipeline, update prefs) post corresponding feed events

### 6.2 Proactive Alert Flow

1. Agent finds strong match or detects pipeline issue
2. Alert appears in Command Panel as an agent message with ALERT/SUGGESTION badge
3. Corresponding feed item posted to Activity Feed
4. If user is on another view, tab badge shows count
5. User can act or dismiss; dismissal suppressed same alert for 24h

### 6.3 Preference Update Flow

1. Recruiter says "Remember, I prefer candidates with AWS experience"
2. Agent confirms with "Added as explicit preference" + impact summary
3. Preference appears immediately in Preferences tab
4. Open searches re-run with new preference applied
5. Action logged with "Undo" option (visible for 30s)

---

## 7. Error & Empty States

| Component | Loading | Empty | Error |
|-----------|---------|-------|-------|
| Feed | Skeleton feed items (3x) | "No activity yet. Start by typing a command." | "Couldn't load feed. [Retry]" |
| Pipeline | Skeleton columns (5x) | "No candidates yet. Ask the agent to source." | "Couldn't load pipeline. [Retry]" |
| Jobs | Skeleton cards (3x) | "No open jobs. They'll appear here when assigned." | "Couldn't load jobs. [Retry]" |
| Preferences | Skeleton list items | "No preferences yet. The agent learns from your actions." | "Couldn't load preferences. [Retry]" |
| Command Panel | "Thinking..." with pulse | N/A (always chat) | "Agent temporarily unavailable. Please use manual search." (graceful degradation per PRD §7.3) |

---

## 8. Accessibility

- WCAG 2.1 AA compliance target
- Color contrast: all text meets 4.5:1 (normal) / 3:1 (large) ratios
- Focus indicators: 2px solid indigo outline
- Keyboard navigation: Tab through all interactive elements, Enter/Space to activate
- Screen reader labels on all icons and action buttons
- Semantic heading hierarchy (h1–h3)
- `/commands` accessible via keyboard shortcut ⌘K
- Motion: prefers-reduced-motion respected (no animations if set)

---

## 9. Component Tree

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

---

## 10. UI States per View

| View | Default | Loading | Empty | Error | Edge Cases |
|------|---------|---------|-------|-------|------------|
| Feed | Timeline of today's events grouped by time | 3 skeleton items with pulse | "No activity yet — type a command to start" | Inline error banner + retry | 50+ events: "Show 50 more" link |
| Pipeline | 5 columns with candidate cards | 5 skeleton columns | "No candidates — ask agent to source" | Inline error + retry | 20+ cards in one column: scroll; job has no req match: "No candidates match your preferences" |
| Jobs | Sorted job cards | 3 skeleton cards | "No open jobs assigned" | Inline error + retry | 20+ jobs: search filter bar appears; all jobs green: dismissible "All jobs on track" banner |
| Prefs | Explicit + implicit lists + weekly digest | Skeleton list items | "No preferences yet — agent learns from your actions" | Inline error + retry | 20+ learned: stacked bar view; all removed: "All preferences cleared" |
| Command | Chat thread or empty welcome | "Thinking..." | Welcome message: "Hi! I'm your recruiting assistant. Ask me to find candidates, check your pipeline, or update preferences." | "Agent unavailable — use manual search" | LLM rate limit: "Please wait 30s"; session expired: auto-refresh |
