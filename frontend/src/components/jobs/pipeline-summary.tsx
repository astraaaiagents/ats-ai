/* ── PipelineSummary ────────────────────────────────────────────────

   "8R · 3S · 1I" format.
*/

"use client";

import { cn } from "@/lib/utils";

interface PipelineSummaryProps {
  summary: string;
  count: number;
}

export function PipelineSummary({ summary, count }: PipelineSummaryProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <span className="rounded-badge bg-surface-hover px-2 py-0.5 text-xs font-mono text-text-secondary">
          {summary}
        </span>
      </div>
      <span className="text-xs text-text-tertiary">
        {count} candidate{count !== 1 ? "s" : ""}
      </span>
    </div>
  );
}
