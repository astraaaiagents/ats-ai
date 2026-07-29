# Question: How is the Chat UI implemented?

Based on the UI/UX Design Specification (`docs/superpowers/specs/2026-07-26-agent-portal-ui-ux-design.md`).

**Interaction Paradigm: Hybrid**
- **Activity Feed** (default view): Chronological timeline of agent suggestions, recruiter actions, system events
- **Pipeline / Kanban**: Job-scoped visual pipeline (Sourced → Reviewing → Submitted → Interviewing → Placed)
- **Command Panel**: Persistent right-side panel, always visible across all tabs

**Layout:**
- Top nav: ⚡ ATS Agent | Feed | Pipeline | Jobs | Prefs | Analytics
- Main content area (switches per tab) + Command Panel (persistent, right side)
- Responsive: ≥1280px full two-panel; 1024-1279px collapsible; 768-1023px bottom sheet; <768px full-screen overlay

**Visual Theme: Warm Indigo**
- Surface: #faf9f7 (base), #f5f4f1 (cards), #eeedea (hover)
- Primary: #4f46e5 (indigo 600), #eef2ff (indigo 50 badge bg)
- AI/Agent: #9333ea (purple 600)
- Text: #1c1917 (primary), #57534e (secondary), #a8a29e (tertiary)
- Font: Inter, border-radius: 8px cards, 6px buttons, 4px badges

**Command Panel: Three States**
1. **Compact Chat** (340px default): Message thread, input bar, quick action chips (/find, /submit, /schedule, /prefs, /outreach)
2. **Expanded Detail** (440px): Full candidate profile — avatar, contact, fit breakdown, strengths/gaps, skills tags, CTA buttons. Breadcrumb "← Back to chat"
3. **Side-by-Side Compare** (440px split): Two 50% columns for /compare command

**AI Output Badges (EU AI Act):**
- `AI-GENERATED` — Indigo 50 bg, Indigo 600 text
- `LOW CONFIDENCE` — Amber 50 bg, Amber 600 text (confidence <70%)
- `AGENT SUGGESTION` — Purple 50 bg, Purple 600 text (proactive)
- `PREFERENCE UPDATED` — Purple 50 bg, Purple 600 text
- `LEARNING` — Purple 50 bg, Purple 600 text (weekly digest)

**Views:**
1. **Activity Feed**: Reverse-chronological, grouped by date, left border color by type (indigo=AI, green=user, purple=learning, red=alert), inline actions (Approve/Review/Reject)
2. **Pipeline/Kanban**: 5 columns (Sourced → Reviewing → Submitted → Interviewing → Placed), job context bar, "+3 new matches" card, gap indicators, inline approve/reject
3. **Jobs List**: Card-based with client+role, req ID, location, candidate count, pipeline summary, color-coded left border (blue=healthy, yellow=needs attention, green=on track, red=critical)
4. **Preferences & Learning**: Explicit rules (toggle list) + Implicit learned patterns (confidence: High/Medium/Low, visual strength bar, override/remove/show evidence) + Weekly Learning Summary banner
5. **Analytics**: Placeholder for Phase 3+

**Job Selector (Pipeline View):**
- **Dropdown at top of PipelineView**: Shows current job name (e.g., "TCS — Java Lead") with chevron. Clicking opens a searchable dropdown of all open jobs.
- **Click-to-scope from Jobs tab**: Clicking any job card navigates to Pipeline tab scoped to that job.
- **"All Jobs" view**: First option in dropdown shows "All Jobs" — aggregates candidates across all open jobs into a single pipeline (color-coded by job). Useful for cross-job visibility.
- **URL encoding**: Selected job stored in URL query param (`/pipeline?job=uuid`). Deep-linkable.
- **Breadcrumb**: Shows current scope: "Pipeline > TCS — Java Lead" (or "Pipeline > All Jobs")

**Quick Review Mode (PRD Story 1.3):**
- **Activation**: `/quick-review` command in Command Panel, or "Quick Review" button in Pipeline column header (Sourced column).
- **Card-by-card flow**: Shows one candidate at a time in a centered card overlay. Large fit score, strengths, gaps, skills. Swipe-left to reject, swipe-right to approve. Keyboard: ← reject, → approve, space = view details.
- **Batch size**: Configurable (default 20, max 100). Recruiter sets batch size before starting.
- **Real-time preference updates**: Each approve/reject immediately updates implicit preferences (logged to `preference_learning_events`).
- **Summary at end**: After batch completes, shows summary: "You approved 14, rejected 6. Strong preference for AWS and leadership experience this round." Links to Preferences tab for verification.
- **Resume capability**: If recruiter leaves mid-batch, can resume from where they left off.
- **Component**: `QuickReviewOverlay` — full-screen overlay with card, action buttons, progress bar, keyboard shortcuts hint.

**Search & Filter UI:**
- **Global search bar**: Always visible in TopNav (triggered by ⌘K or clicking the search icon). Searches across candidates, jobs, and conversations. Shows quick results as you type (top 5 candidates, top 5 jobs).
- **Pipeline filters**: Collapsible filter bar below job selector. Filters: skill (multi-select chips), fit score range (dual slider, 0–100%), experience range (years), location (text input), visa status (dropdown). Applied as URL query params (shareable).
- **Jobs filters**: Search by client name, role keyword. Dropdown filter by status (healthy/needs attention/on track/critical). Multi-select by domain (Java, Python, Data, etc.).
- **Command Panel search**: `/find java aws nyc` — natural language search that opens results in Command Panel Expanded Detail.
- **Search results in Command Panel**: Shows candidate cards with fit scores. Click to expand. "View in Pipeline" link to navigate to scoped pipeline.
- **Component**: `SearchBar` (TopNav), `PipelineFilters` (collapsible), `JobsFilters` (dropdown), `SearchResults` (Command Panel overlay).

**Component Tree:**
```
App
├── TopNav
│   ├── Logo ("⚡ ATS Agent")
│   ├── SearchBar (⌘K trigger, global search, quick results)
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
│   │   ├── JobSelector (dropdown with search, "All Jobs" option, breadcrumb)
│   │   ├── PipelineFilters (collapsible: skill chips, fit score slider, experience, location, visa)
│   │   ├── PipelineColumn × 5
│   │   │   ├── ColumnHeader (name + count + "Quick Review" button)
│   │   │   └── PipelineCard
│   │   │       ├── CandidateName
│   │   │       ├── RoleTitle
│   │   │       ├── FitBadge (score + stars)
│   │   │       ├── SkillTags
│   │   │       └── StageActions (→Review | Approve | Reject)
│   │   └── LoadingSkeleton / EmptyState / ErrorState
│   │
│   ├── JobsView
│   │   ├── JobsFilters (client search, role keyword, status dropdown, domain multi-select)
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
├── QuickReviewOverlay (full-screen, activated by /quick-review or column button)
│   ├── ProgressBar (X/20 candidates)
│   ├── CandidateCard (large: fit score, strengths, gaps, skills)
│   ├── ActionButtons (← Reject | View Details | Approve →)
│   ├── KeyboardHint ("← reject · → approve · space = details")
│   └── SummaryView (approved/rejected count, preference changes, "View Preferences" link)
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
    │   └── QuickActionChips (/find, /submit, /schedule, /prefs, /outreach, /quick-review)
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
    ├── SearchResults (overlay, triggered by global search or /find)
    │   ├── CandidateResults (top 5 with fit scores)
    │   ├── JobResults (top 5)
    │   └── ConversationResults (top 5)
    │
    └── SideBySideCompare (440px split)
        ├── CompareColumn × 2
        └── ComparisonActions
```

**Error & Empty States:**
- Feed: Skeleton items → "No activity yet. Start by typing a command." → "Couldn't load feed. [Retry]"
- Pipeline: Skeleton columns → "No candidates yet. Ask the agent to source." → "Couldn't load pipeline. [Retry]"
- Pipeline (no job selected): "Select a job to view its pipeline." (shown when JobSelector has no selection)
- Jobs: Skeleton cards → "No open jobs. They'll appear here when assigned." → "Couldn't load jobs. [Retry]"
- Jobs (no filter matches): "No jobs match your filters. Try adjusting the search."
- Preferences: Skeleton list → "No preferences yet. The agent learns from your actions." → "Couldn't load preferences. [Retry]"
- QuickReview: "No candidates available for review." (if batch is empty) → "Ask the agent to source candidates first."
- Command: "Thinking..." → Welcome message → "Agent temporarily unavailable. Please use manual search."
- Search: "No results for '{query}'." → "Try different keywords or use /find with natural language."

**Accessibility:** WCAG 2.1 AA, color contrast 4.5:1, focus indicators (2px indigo outline), keyboard nav (Tab/Enter/Space), ⌘K for /commands, prefers-reduced-motion respected

Resolve by scaffolding the Next.js app, implementing all views and the Command Panel, and connecting to the Agent Gateway API.
