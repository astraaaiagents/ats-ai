/* ── ReviewActions ──────────────────────────────────────────────────

   ← Reject | View Details | Approve →
*/

"use client";

import { Button } from "@/components/ui/button";

interface ReviewActionsProps {
  onApprove: () => void;
  onReject: () => void;
  onViewDetails: () => void;
}

export function ReviewActions({ onApprove, onReject, onViewDetails }: ReviewActionsProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      <Button
        variant="outline"
        onClick={onReject}
        className="h-12 px-8 border-danger text-danger hover:bg-danger hover:text-white"
      >
        ← Reject
      </Button>
      <Button
        variant="ghost"
        onClick={onViewDetails}
        className="h-12 px-4 text-text-secondary"
      >
        View Details
      </Button>
      <Button
        onClick={onApprove}
        className="h-12 px-8 bg-success hover:bg-green-700"
      >
        Approve →
      </Button>
    </div>
  );
}
