/* ── JobCard ────────────────────────────────────────────────────────

   Header, pipeline summary, agent insight, color-coded status border.
*/

"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { PipelineSummary } from "./pipeline-summary";
import { AgentInsight } from "./agent-insight";
import { type Job } from "@/lib/api/types";

const STATUS_BORDER: Record<Job["status"], string> = {
  healthy: "border-l-blue-500",
  needs_attention: "border-l-yellow-500",
  on_track: "border-l-green-500",
  critical: "border-l-red-500",
};

interface JobCardProps {
  job: Job;
}

export function JobCard({ job }: JobCardProps) {
  return (
    <div className={cn(
      "rounded-card border border-border bg-card border-l-4",
      STATUS_BORDER[job.status]
    )}>
      <div className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-text-primary">
              {job.client_name} — {job.role_title}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="rounded-badge text-[10px]">
                {job.req_id}
              </Badge>
              <span className="text-xs text-text-tertiary">{job.location}</span>
              {job.domains.map((d) => (
                <Badge key={d} variant="secondary" className="rounded-badge text-[10px]">
                  {d}
                </Badge>
              ))}
            </div>
          </div>
          <div className="text-right">
            <span className={cn(
              "text-xs font-medium",
              job.status === "healthy" && "text-blue-500",
              job.status === "needs_attention" && "text-yellow-500",
              job.status === "on_track" && "text-green-500",
              job.status === "critical" && "text-red-500",
            )}>
              {job.status.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
          </div>
        </div>

        {/* Pipeline Summary */}
        <PipelineSummary summary={job.pipeline_summary} count={job.candidate_count} />

        {/* Agent Insight */}
        <AgentInsight insight={job.agent_insight} />
      </div>
    </div>
  );
}
