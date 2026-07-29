/* ── ReviewSummary ──────────────────────────────────────────────────

   Approved/rejected count, preference changes.
*/

"use client";

import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, TrendingUp } from "lucide-react";

interface ReviewSummaryProps {
  approved: string[];
  rejected: string[];
  total: number;
  onClose: () => void;
}

export function ReviewSummary({ approved, rejected, total, onClose }: ReviewSummaryProps) {
  return (
    <div className="space-y-6 text-center">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">Review Complete</h2>
        <p className="text-sm text-text-secondary mt-1">
          You reviewed {total} candidates
        </p>
      </div>

      <div className="flex justify-center gap-8">
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            <CheckCircle2 className="h-5 w-5 text-success" />
            <span className="text-2xl font-semibold text-success">{approved.length}</span>
          </div>
          <span className="text-xs text-text-secondary">Approved</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            <XCircle className="h-5 w-5 text-danger" />
            <span className="text-2xl font-semibold text-danger">{rejected.length}</span>
          </div>
          <span className="text-xs text-text-secondary">Rejected</span>
        </div>
      </div>

      <div className="rounded-card border border-ai/20 bg-ai-light p-4 text-left">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="h-4 w-4 text-ai" />
          <span className="text-sm font-semibold text-ai">Preference Update</span>
        </div>
        <p className="text-xs text-text-secondary">
          Strong preference for AWS and leadership experience detected this round.
          Your implicit preferences have been updated.
        </p>
      </div>

      <Button onClick={onClose} className="w-full">
        Done
      </Button>
    </div>
  );
}
