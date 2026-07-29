/* ── Analytics View Page ────────────────────────────────────────────

   Placeholder for Phase 3+.
*/

"use client";

import { AppShell } from "@/components/layout/app-shell";
import { AnalyticsView } from "@/components/views/analytics-view";

export default function AnalyticsPage() {
  return (
    <AppShell defaultTab="analytics">
      <AnalyticsView />
    </AppShell>
  );
}
