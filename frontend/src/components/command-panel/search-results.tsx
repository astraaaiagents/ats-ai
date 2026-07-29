/* ── SearchResults ──────────────────────────────────────────────────

   Top 5 candidates/jobs/conversations in Command Panel.
*/

"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { FitBadge } from "@/components/shared/fit-badge";
import { useCommandPanel } from "@/lib/store/ui";

interface SearchResultsProps {
  query: string;
}

// Mock search results
const MOCK_CANDIDATES = [
  { id: "1", name: "Alex Johnson", title: "Senior Full-Stack Engineer", fitScore: 92 },
  { id: "2", name: "Maria Chen", title: "Backend Engineer (Go)", fitScore: 85 },
  { id: "3", name: "James Wilson", title: "DevOps Lead", fitScore: 78 },
  { id: "4", name: "Priya Patel", title: "Data Engineer", fitScore: 72 },
  { id: "5", name: "Tom Baker", title: "Frontend Engineer", fitScore: 68 },
];

export function SearchResults({ query }: SearchResultsProps) {
  const { setExpandedCandidate } = useCommandPanel();

  if (!query.trim()) {
    return (
      <div className="flex h-full items-center justify-center text-xs text-text-tertiary">
        Type to search candidates, jobs, and conversations
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-2 space-y-1">
        <div className="px-2 py-1.5 text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
          Candidates ({MOCK_CANDIDATES.length})
        </div>
        {MOCK_CANDIDATES.map((c) => (
          <button
            key={c.id}
            onClick={() => setExpandedCandidate(c.id)}
            className="flex w-full items-center gap-3 rounded-card px-2 py-2 text-left transition hover:bg-hover"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-light text-primary text-xs font-medium">
              {c.name.split(" ").map((n) => n[0]).join("")}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-text-primary truncate">{c.name}</div>
              <div className="text-[11px] text-text-secondary truncate">{c.title}</div>
            </div>
            <FitBadge score={c.fitScore} size="sm" />
          </button>
        ))}

        <div className="px-2 py-1.5 text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
          Jobs
        </div>
        <div className="rounded-card px-2 py-2 text-xs text-text-tertiary">
          No jobs match &quot;{query}&quot;
        </div>

        <div className="px-2 py-1.5 text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
          Conversations
        </div>
        <div className="rounded-card px-2 py-2 text-xs text-text-tertiary">
          No conversations match &quot;{query}&quot;
        </div>
      </div>
    </ScrollArea>
  );
}
