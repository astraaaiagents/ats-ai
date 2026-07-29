/* ── Pipeline View Page ─────────────────────────────────────────────

   Kanban pipeline view.
*/

"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PipelineView } from "@/components/pipeline/pipeline-view";

export default function PipelinePage() {
  return (
    <AppShell defaultTab="pipeline">
      <PipelineView />
    </AppShell>
  );
}
