/* ── PipelineView ───────────────────────────────────────────────────

   5-column Kanban, job context bar, filters.
   Loads candidates from the API, filtered by pipeline status.
*/

"use client";

import { useState, useMemo } from "react";
import { JobSelector } from "./job-selector";
import { PipelineFilters } from "./pipeline-filters";
import { PipelineColumn } from "./pipeline-column";
import { PIPELINE_STAGES, type PipelineStage } from "@/lib/api/types";
import { EmptyState } from "@/components/shared/empty-state";
import { SkeletonCard } from "@/components/shared/skeleton";
import { type PipelineCandidate } from "./types";
import { useCandidates } from "@/lib/api/hooks";

export function PipelineView() {
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const { data: candidatesData, isLoading } = useCandidates({
    limit: 200,
  });

  // Transform API candidates to pipeline format
  const pipelineCandidates = useMemo<PipelineCandidate[]>(() => {
    if (!candidatesData?.data) return [];
    return candidatesData.data.map((c) => ({
      id: c.id,
      name: `${c.first_name} ${c.last_name}`,
      title: c.current_title || "Untitled",
      fitScore: 0, // Fit score computed by agent, not stored on candidate
      skills: c.skills.map((s) => s.skill_name),
      stage: (c.status as PipelineStage) || "sourced",
      jobId: selectedJob || undefined,
    }));
  }, [candidatesData, selectedJob]);

  const filteredCandidates = selectedJob
    ? pipelineCandidates.filter((c) => c.jobId === selectedJob)
    : pipelineCandidates;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex gap-4">
          {PIPELINE_STAGES.map((s) => (
            <SkeletonCard key={s} className="flex-1 h-64" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Job Selector */}
      <JobSelector selectedJob={selectedJob} onChange={setSelectedJob} />

      {/* Filters toggle */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setFiltersOpen((v) => !v)}
          className="text-xs text-text-secondary hover:text-text-primary transition"
        >
          {filtersOpen ? "Hide" : "Show"} Filters
        </button>
        <span className="text-xs text-text-tertiary">
          {filteredCandidates.length} candidates
        </span>
      </div>

      {/* Filters */}
      {filtersOpen && <PipelineFilters />}

      {/* Pipeline Columns */}
      {filteredCandidates.length === 0 ? (
        <EmptyState
          title="No candidates in pipeline"
          description="Ask your agent to source candidates or submit new profiles."
        />
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-4">
          {PIPELINE_STAGES.map((stage) => {
            const stageCandidates = filteredCandidates.filter((c) => c.stage === stage);
            return (
              <PipelineColumn
                key={stage}
                stage={stage}
                candidates={stageCandidates}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
