/* ── Jobs View Page ─────────────────────────────────────────────────

   Job cards with mock data.
*/

"use client";

import { AppShell } from "@/components/layout/app-shell";
import { JobsView } from "@/components/jobs/jobs-view";

export default function JobsPage() {
  return (
    <AppShell defaultTab="jobs">
      <JobsView />
    </AppShell>
  );
}
