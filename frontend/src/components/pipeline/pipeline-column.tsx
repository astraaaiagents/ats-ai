/* ── PipelineColumn ─────────────────────────────────────────────────

   × 5 columns (Sourced → Reviewing → Submitted → Interviewing → Placed).
*/

"use client";

import { ColumnHeader } from "./column-header";
import { PipelineCard } from "./pipeline-card";
import { type PipelineCandidate } from "./types";
import { type PipelineStage } from "@/lib/api/types";

interface PipelineColumnProps {
  stage: PipelineStage;
  candidates: PipelineCandidate[];
}

const STAGE_LABELS: Record<PipelineStage, string> = {
  sourced: "Sourced",
  reviewing: "Reviewing",
  submitted: "Submitted",
  interviewing: "Interviewing",
  placed: "Placed",
};

const STAGE_COLORS: Record<PipelineStage, string> = {
  sourced: "bg-blue-500",
  reviewing: "bg-yellow-500",
  submitted: "bg-primary",
  interviewing: "bg-ai",
  placed: "bg-success",
};

export function PipelineColumn({ stage, candidates }: PipelineColumnProps) {
  return (
    <div className="flex min-w-[240px] max-w-[240px] flex-col rounded-card border border-border bg-surface">
      <ColumnHeader
        label={STAGE_LABELS[stage]}
        count={candidates.length}
        stageColor={STAGE_COLORS[stage]}
      />
      <div className="flex-1 space-y-2 p-2 overflow-y-auto">
        {candidates.map((c) => (
          <PipelineCard key={c.id} candidate={c} />
        ))}
        {candidates.length === 0 && (
          <div className="py-8 text-center text-xs text-text-tertiary">
            No candidates
          </div>
        )}
      </div>
    </div>
  );
}
