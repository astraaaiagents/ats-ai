/* ── FeedActions ────────────────────────────────────────────────────

   Approve, Review, Reject buttons.
*/

"use client";

import { useCommandPanel } from "@/lib/store/ui";
import { Button } from "@/components/ui/button";

interface FeedActionsProps {
  type: "agent" | "user" | "system" | "alert";
  candidateId?: string;
}

export function FeedActions({ type, candidateId }: FeedActionsProps) {
  const { setExpandedCandidate } = useCommandPanel();

  // Only show actions for agent and alert types
  if (type === "user" || type === "system") return null;

  return (
    <div className="flex items-center gap-1 shrink-0">
      {type === "agent" && (
        <>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs text-success hover:bg-success-light hover:text-success"
            onClick={() => candidateId && setExpandedCandidate(candidateId)}
          >
            Approve
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs text-text-secondary hover:bg-hover"
            onClick={() => candidateId && setExpandedCandidate(candidateId)}
          >
            Review
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs text-danger hover:bg-danger-light hover:text-danger"
            onClick={() => candidateId && setExpandedCandidate(candidateId)}
          >
            Reject
          </Button>
        </>
      )}
      {type === "alert" && (
        <>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs text-primary hover:bg-primary-light hover:text-primary"
            onClick={() => candidateId && setExpandedCandidate(candidateId)}
          >
            Review
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs text-text-tertiary hover:bg-hover"
          >
            Dismiss
          </Button>
        </>
      )}
    </div>
  );
}
