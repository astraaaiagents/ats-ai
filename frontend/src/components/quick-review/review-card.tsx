/* ── ReviewCard ─────────────────────────────────────────────────────

   Large candidate card with fit score, strengths, gaps, skills.
*/

"use client";

import { FitBadge } from "@/components/shared/fit-badge";
import { SkillTags } from "@/components/shared/skill-tags";
import { type PipelineCandidate } from "@/components/pipeline/types";

interface ReviewCardProps {
  candidate: PipelineCandidate;
}

export function ReviewCard({ candidate }: ReviewCardProps) {
  return (
    <div className="w-full max-w-md rounded-card border border-border bg-card p-6 space-y-4 shadow-lg">
      {/* Avatar + Name + Score */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-primary-light text-primary text-xl font-semibold">
            {candidate.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">{candidate.name}</h3>
            <p className="text-sm text-text-secondary">{candidate.title}</p>
          </div>
        </div>
        <FitBadge score={candidate.fitScore} size="lg" />
      </div>

      {/* Skills */}
      <div>
        <h4 className="text-xs font-semibold text-text-primary mb-1.5">Skills</h4>
        <SkillTags skills={candidate.skills} maxDisplay={8} />
      </div>

      {/* Strengths */}
      <div>
        <h4 className="text-xs font-semibold text-success mb-1.5">Strengths</h4>
        <div className="flex flex-wrap gap-1">
          {["Strong technical background", "Relevant experience", "Good communication"].map((s) => (
            <span key={s} className="rounded-badge bg-success-light px-2 py-0.5 text-xs font-medium text-success">
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Gaps */}
      <div>
        <h4 className="text-xs font-semibold text-warning mb-1.5">Gaps</h4>
        <div className="flex flex-wrap gap-1">
          {["Limited Kubernetes experience", "No GraphQL background"].map((g) => (
            <span key={g} className="rounded-badge bg-warning-light px-2 py-0.5 text-xs font-medium text-warning">
              {g}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
