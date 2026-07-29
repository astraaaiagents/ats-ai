/* ── AnalyticsView ──────────────────────────────────────────────────

   Placeholder for Phase 3+.
*/

"use client";

import { EmptyState } from "@/components/shared/empty-state";

export function AnalyticsView() {
  return (
    <EmptyState
      icon={
        <svg className="h-12 w-12 text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      }
      title="Analytics — Coming Soon"
      description="Pipeline metrics, agent performance, and recruiter productivity dashboards will appear here."
    />
  );
}
