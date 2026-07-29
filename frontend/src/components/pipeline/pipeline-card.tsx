/* ── PipelineCard ───────────────────────────────────────────────────

   Name, title, fit badge, skill tags, stage actions.
*/

"use client";

import { useCommandPanel } from "@/lib/store/ui";
import { FitBadge } from "@/components/shared/fit-badge";
import { SkillTags } from "@/components/shared/skill-tags";
import { Button } from "@/components/ui/button";
import { type PipelineCandidate } from "./types";

interface PipelineCardProps {
  candidate: PipelineCandidate;
}

export function PipelineCard({ candidate }: PipelineCardProps) {
  const { setExpandedCandidate } = useCommandPanel();

  return (
    <div className="rounded-card border border-border bg-card p-3 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-sm font-medium text-text-primary truncate">{candidate.name}</div>
          <div className="text-xs text-text-secondary truncate">{candidate.title}</div>
        </div>
        <FitBadge score={candidate.fitScore} size="sm" />
      </div>
      <SkillTags skills={candidate.skills} maxDisplay={3} />
      <div className="flex items-center gap-1 pt-1">
        <Button
          size="sm"
          variant="ghost"
          className="h-6 px-1.5 text-[10px] text-text-secondary hover:bg-hover"
          onClick={() => setExpandedCandidate(candidate.id)}
        >
          Review
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-6 px-1.5 text-[10px] text-success hover:bg-success-light hover:text-success"
          onClick={() => setExpandedCandidate(candidate.id)}
        >
          Approve
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-6 px-1.5 text-[10px] text-danger hover:bg-danger-light hover:text-danger"
          onClick={() => setExpandedCandidate(candidate.id)}
        >
          Reject
        </Button>
      </div>
    </div>
  );
}
