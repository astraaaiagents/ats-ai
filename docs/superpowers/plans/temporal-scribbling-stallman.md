# Plan: Chat UI Implementation

## Context

This is a **backend-only project** with a complete FastAPI API but **no frontend application**. The task is to scaffold a Next.js app from scratch and implement the full Chat UI as specified in `.scratch/wayfinder/task-chat-ui.md`. The UI follows a "Warm Indigo" theme with Inter font, 8px cards, 6px buttons, and a persistent right-side Command Panel.

The backend already has all the necessary API endpoints (auth, candidates, agent gateway with SSE streaming, preferences, proactive alerts). The frontend will consume these APIs and render the full component tree described in the spec.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Next.js | App Router (Next.js 15) | Modern, better for complex dashboards |
| UI library | shadcn/ui + Radix primitives | Accessible, customizable, matches design spec |
| Styling | Tailwind CSS + CSS custom properties | Warm Indigo theme via CSS vars |
| State | Zustand (global UI) + React Context (auth) + React Query (server state) | Lightweight, no boilerplate |
| API client | Custom fetch wrapper with auth/refresh | Simple, full control |
| SSE | fetch + ReadableStream reader | Auth header support, flexible |
| Font | Inter via `next/font/google` | Spec requirement |

## Implementation Phases

### Phase 1: Scaffold & Foundation

1. **Scaffold Next.js app**: `npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*" --no-turbopack`
2. **Install dependencies**: `shadcn/ui`, `@tanstack/react-query`, `zustand`, `lucide-react`
3. **Configure Tailwind** with Warm Indigo theme:
   - Colors: `surface-base: #faf9f7`, `surface-card: #f5f4f1`, `primary: #4f46e5`, `ai: #9333ea`, `text-primary: #1c1917`, `text-secondary: #57534e`
   - Fonts: Inter (variable), border-radius: 8px cards, 6px buttons
4. **Create CSS variables** in `globals.css`
5. **Create `cn()` utility** in `lib/utils.ts`

### Phase 2: Auth & API Layer

6. **API client** (`lib/api/client.ts`): Fetch wrapper with JWT Bearer token, auto-refresh on 401
7. **SSE module** (`lib/api/sse.ts`): Parse SSE events (`message_start`, `content`, `card`, `action`, `message_end`)
8. **Auth context** (`lib/auth/context.tsx`): `AuthProvider` with login/logout, localStorage token persistence
9. **Auth guard hook** (`hooks/use-auth-guard.ts`): Redirect to `/login` if unauthenticated
10. **Zustand UI store** (`lib/store/ui.ts`): Active tab, command panel state, search, notifications
11. **React Query provider** (`lib/query/client.tsx`): QueryClient with 60s stale time
12. **Login page** (`app/login/page.tsx`): Email/password form, calls `/api/v1/auth/login`

### Phase 3: Shared UI Components

13. **shadcn/ui components**: button, input, badge, avatar, dialog, dropdown-menu, popover, tabs, switch, slider, progress, scroll-area, toast, separator, tooltip
14. **Shared components**:
    - `Skeleton` — pulsing placeholder cards
    - `EmptyState` — "No activity yet" messages
    - `ErrorState` — "Couldn't load" + retry button
    - `Avatar` — initials-based avatar
    - `FitBadge` — score + stars
    - `SkillTags` — colored pill tags
    - `ConfirmDialog` — action confirmation

### Phase 4: Layout & Navigation

15. **Root layout** (`app/layout.tsx`): AuthProvider, QueryClientProvider, Inter font, AppShell
16. **AppShell** (`components/layout/app-shell.tsx`): TopNav + main content + CommandPanel
17. **TopNav** (`components/layout/top-nav.tsx`): Logo "⚡ ATS Agent", TabBar, SearchBar, NotificationBadge
18. **TabBar** (`components/layout/tab-bar.tsx`): Feed | Pipeline | Jobs | Preferences | Analytics
19. **SearchBar** (`components/layout/search-bar.tsx`): Cmd+K trigger, global search, quick results
20. **Keyboard shortcuts** (`hooks/use-keyboard-shortcut.ts`): Cmd+K for search

### Phase 5: Command Panel (Persistent Right Side)

21. **CommandPanel** (`components/command-panel/command-panel.tsx`): State manager, persistent across tabs
22. **CompactChat** (`components/command-panel/compact-chat.tsx`): 340px default, message thread, input bar, quick action chips
23. **MessageThread** (`components/command-panel/message-thread.tsx`): Scrollable messages, SSE streaming accumulation
24. **CommandMessage** (`components/command-panel/command-message.tsx`): User/agent bubble with role badge, content, inline actions
25. **InputBar** (`components/command-panel/input-bar.tsx`): Text input, attach, voice, send button
26. **QuickActionChips** (`components/command-panel/quick-action-chips.tsx`): /find, /submit, /schedule, /prefs, /outreach, /quick-review
27. **ExpandedDetail** (`components/command-panel/expanded-detail.tsx`): 440px, candidate profile, fit breakdown, strengths/gaps, skills, CTA actions
28. **SearchResults** (`components/command-panel/search-results.tsx`): Top 5 candidates/jobs/conversations
29. **SideBySideCompare** (`components/command-panel/side-by-side-compare.tsx`): Two 50% columns

### Phase 6: FeedView (Default Route)

30. **FeedView** (`components/views/feed-view.tsx`): Reverse-chronological timeline, grouped by date
31. **DateGroup** (`components/feed/date-group.tsx`): "Today", "Yesterday", date headers
32. **FeedItem** (`components/feed/feed-item.tsx`): Agent/user/system/alert with left border color
33. **FeedBadge** (`components/feed/feed-badge.tsx`): AI-GENERATED, LOW CONFIDENCE, AGENT SUGGESTION, PREFERENCE UPDATED, LEARNING
34. **FeedActions** (`components/feed/feed-actions.tsx`): Approve, Review, Reject buttons
35. **InlineCard** (`components/feed/inline-card.tsx`): CandidateCard, JobCard, AlertCard

### Phase 7: PipelineView

36. **PipelineView** (`components/views/pipeline-view.tsx`): 5-column Kanban, job selector, filters
37. **JobSelector** (`components/pipeline/job-selector.tsx`): Dropdown with search, "All Jobs" option, URL param `?job=uuid`
38. **PipelineFilters** (`components/pipeline/pipeline-filters.tsx`): Skill chips, fit score slider, experience, location, visa
39. **PipelineColumn** (`components/pipeline/pipeline-column.tsx`): × 5 columns (Sourced → Reviewing → Submitted → Interviewing → Placed)
40. **ColumnHeader** (`components/pipeline/column-header.tsx`): Name + count + Quick Review button
41. **PipelineCard** (`components/pipeline/pipeline-card.tsx`): Name, title, fit badge, skill tags, stage actions

### Phase 8: JobsView

42. **JobsView** (`components/views/jobs-view.tsx`): Card-based job list with mock data (no Job model in backend)
43. **JobsFilters** (`components/jobs/jobs-filters.tsx`): Client search, role keyword, status dropdown, domain multi-select
44. **JobCard** (`components/jobs/job-card.tsx`): Header, pipeline summary, agent insight, color-coded status border
45. **PipelineSummary** (`components/jobs/pipeline-summary.tsx`): "8R · 3S · 1I" format
46. **AgentInsight** (`components/jobs/agent-insight.tsx`): "Strong pipeline", "Pipeline too thin", etc.

### Phase 9: PreferencesView

47. **PreferencesView** (`components/views/preferences-view.tsx`): Explicit + implicit rules + weekly digest
48. **ExplicitPreferences** (`components/preferences/explicit-preferences.tsx`): Rule list with toggles, "Add Rule" button
49. **ImplicitPreferences** (`components/preferences/implicit-preferences.tsx`): Learned patterns with confidence, strength bars, override/remove
50. **LearningDigest** (`components/preferences/learning-digest.tsx`): Weekly summary banner with trends

### Phase 10: Quick Review Overlay

51. **QuickReviewOverlay** (`components/quick-review/quick-review-overlay.tsx`): Full-screen overlay, activated by /quick-review
52. **ReviewProgress** (`components/quick-review/review-progress.tsx`): X/20 candidates progress bar
53. **ReviewCard** (`components/quick-review/review-card.tsx`): Large candidate card with fit score, strengths, gaps, skills
54. **ReviewActions** (`components/quick-review/review-actions.tsx`): ← Reject | View Details | Approve →
55. **KeyboardHint** (`components/quick-review/keyboard-hint.tsx`): "← reject · → approve · space = details"
56. **ReviewSummary** (`components/quick-review/review-summary.tsx`): Approved/rejected count, preference changes

### Phase 11: Polish & Docker

57. **AnalyticsView** (`components/views/analytics-view.tsx`): Placeholder as specified
58. **Frontend Dockerfile** (`frontend/Dockerfile`): Multi-stage build
59. **Update docker-compose.yml**: Add frontend service, CORS config
60. **Accessibility audit**: WCAG 2.1 AA, color contrast, focus indicators, keyboard nav
61. **Responsive testing**: 1280px full, 1024px collapsible, 768px bottom sheet, <768px overlay

## Key Files to Create/Modify

### New files (representative paths):
- `frontend/package.json` — Dependencies
- `frontend/next.config.ts` — Next.js config
- `frontend/tailwind.config.ts` — Tailwind + CSS vars
- `frontend/tsconfig.json` — TypeScript config
- `frontend/Dockerfile` — Frontend container
- `frontend/.env.example` — `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- `frontend/src/app/globals.css` — Tailwind + CSS custom properties
- `frontend/src/app/layout.tsx` — Root layout
- `frontend/src/app/page.tsx` — FeedView (default)
- `frontend/src/app/login/page.tsx` — Login page
- `frontend/src/app/pipeline/page.tsx` — PipelineView
- `frontend/src/app/jobs/page.tsx` — JobsView
- `frontend/src/app/preferences/page.tsx` — PreferencesView
- `frontend/src/app/analytics/page.tsx` — AnalyticsView (placeholder)
- `frontend/src/lib/api/client.ts` — API client
- `frontend/src/lib/api/sse.ts` — SSE streaming
- `frontend/src/lib/api/types.ts` — TypeScript types matching backend schemas
- `frontend/src/lib/auth/context.tsx` — AuthProvider
- `frontend/src/lib/store/ui.ts` — Zustand UI store
- `frontend/src/lib/query/client.tsx` — React Query provider
- `frontend/src/lib/utils.ts` — cn() utility
- `frontend/src/hooks/use-auth-guard.ts` — Auth guard
- `frontend/src/hooks/use-sse.ts` — SSE hook wrapper
- `frontend/src/hooks/use-keyboard-shortcut.ts` — Cmd+K handler
- `frontend/src/hooks/use-candidates.ts` — React Query candidate hooks
- `frontend/src/hooks/use-agent.ts` — React Query agent hooks
- `frontend/src/hooks/use-preferences.ts` — React Query preference hooks
- `frontend/src/components/layout/app-shell.tsx` — Main layout
- `frontend/src/components/layout/top-nav.tsx` — Top navigation
- `frontend/src/components/layout/tab-bar.tsx` — Tab navigation
- `frontend/src/components/layout/search-bar.tsx` — Global search
- `frontend/src/components/command-panel/command-panel.tsx` — Persistent panel
- `frontend/src/components/command-panel/compact-chat.tsx` — Chat view
- `frontend/src/components/command-panel/message-thread.tsx` — Message list + SSE
- `frontend/src/components/command-panel/input-bar.tsx` — Chat input
- `frontend/src/components/command-panel/expanded-detail.tsx` — Candidate detail
- `frontend/src/components/views/feed-view.tsx` — Activity feed
- `frontend/src/components/views/pipeline-view.tsx` — Kanban pipeline
- `frontend/src/components/views/jobs-view.tsx` — Job cards
- `frontend/src/components/views/preferences-view.tsx` — Preferences
- `frontend/src/components/quick-review/quick-review-overlay.tsx` — Full-screen review
- `frontend/src/components/shared/skeleton.tsx` — Loading skeletons
- `frontend/src/components/shared/empty-state.tsx` — Empty states
- `frontend/src/components/shared/error-state.tsx` — Error states

### Modified files:
- `docker-compose.yml` — Add frontend service, update CORS_ORIGINS
- `backend/app/config.py` — Ensure CORS_ORIGINS env var is read (already exists)

## API Endpoints the Frontend Consumes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/login` | POST | Login, get JWT tokens |
| `/api/v1/auth/refresh` | POST | Refresh expired access token |
| `/api/v1/candidates` | GET | List candidates (PipelineView, FeedView) |
| `/api/v1/candidates/{id}` | GET | Single candidate (ExpandedDetail) |
| `/api/v1/candidates/{id}/status` | PATCH | Update status (approve/reject) |
| `/api/v1/agent/conversation` | POST | Send message, receive SSE stream |
| `/api/v1/agent/conversation/{id}` | GET | Conversation history |
| `/api/v1/agent/preferences` | GET/PUT | Read/update preferences |
| `/api/v1/agent/proactive/alerts` | GET | Proactive alerts (FeedView) |
| `/api/v1/agent/action-log` | GET | Audit trail |

## Verification Steps

1. `cd frontend && npm run dev` — App starts on port 3000
2. Navigate to `/login`, enter credentials, verify redirect to `/` (FeedView)
3. Open browser Network tab — verify API calls include `Authorization: Bearer <token>`
4. Send a message in Command Panel — verify SSE events stream and render
5. Click Feed/Pipeline/Jobs/Prefs/Analytics tabs — verify URL changes and view switches
6. Command Panel persists across tab switches, compact/expanded states work
7. Press Cmd+K — verify search overlay opens
8. Pipeline job selector — dropdown shows jobs, clicking scopes pipeline
9. Quick Review — overlay opens, keyboard navigation works (← → space)
10. `docker compose up --build` — both api and frontend start, frontend calls backend
11. Responsive testing at 1280px, 1024px, 768px, 480px
12. Lighthouse/axe-core audit for WCAG 2.1 AA compliance
