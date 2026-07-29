/* ── InlineCard ─────────────────────────────────────────────────────

   CandidateCard, JobCard, AlertCard for inline display in feed items.
*/

"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { FitBadge } from "@/components/shared/fit-badge";
import { SkillTags } from "@/components/shared/skill-tags";
import { Button } from "@/components/ui/button";

/* ── CandidateCard ────────────────────────────────────────────────── */

import { useCommandPanel } from "@/lib/store/ui";

interface CandidateCardProps {
  name: string;
  title: string;
  fitScore: number;
  skills: string[];
  candidateId?: string;
  className?: string;
}

export function CandidateCard({ name, title, fitScore, skills, candidateId, className }: CandidateCardProps) {
  const { setExpandedCandidate } = useCommandPanel();

  return (
    <div className={cn("rounded-card border border-border bg-card p-3 mt-2", className)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-light text-primary text-xs font-medium">
            {name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div>
            <div className="text-sm font-medium text-text-primary">{name}</div>
            <div className="text-xs text-text-secondary">{title}</div>
          </div>
        </div>
        <FitBadge score={fitScore} size="sm" />
      </div>
      <SkillTags skills={skills} maxDisplay={4} className="mt-2" />
      <div className="flex gap-2 mt-2">
        <Button
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={() => candidateId && setExpandedCandidate(candidateId)}
        >
          Approve
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="h-7 px-2 text-xs"
          onClick={() => candidateId && setExpandedCandidate(candidateId)}
        >
          Reject
        </Button>
      </div>
    </div>
  );
}

/* ── JobCard ──────────────────────────────────────────────────────── */

interface JobCardProps {
  clientName: string;
  roleTitle: string;
  reqId: string;
  candidateCount: number;
  status: "healthy" | "needs_attention" | "on_track" | "critical";
  className?: string;
}

const STATUS_BORDER = {
  healthy: "border-blue-500",
  needs_attention: "border-yellow-500",
  on_track: "border-green-500",
  critical: "border-red-500",
};

export function JobCard({ clientName, roleTitle, reqId, candidateCount, status, className }: JobCardProps) {
  return (
    <div className={cn("rounded-card border border-border bg-card border-l-4", STATUS_BORDER[status], className)}>
      <div className="p-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-text-primary">
              {clientName} — {roleTitle}
            </div>
            <div className="text-xs text-text-tertiary">{reqId}</div>
          </div>
          <Badge variant="outline" className="rounded-badge">
            {candidateCount} candidates
          </Badge>
        </div>
      </div>
    </div>
  );
}

/* ── AlertCard ────────────────────────────────────────────────────── */

interface AlertCardProps {
  title: string;
  body: string;
  className?: string;
}

export function AlertCard({ title, body, className }: AlertCardProps) {
  return (
    <div className={cn("rounded-card border border-warning/30 bg-warning-light p-3 mt-2", className)}>
      <div className="flex items-start gap-2">
        <span className="text-warning text-sm">⚠</span>
        <div>
          <div className="text-sm font-medium text-warning">{title}</div>
          <div className="text-xs text-warning/80 mt-0.5">{body}</div>
        </div>
      </div>
    </div>
  );
}
