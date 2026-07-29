/* ── QuickReviewOverlay ─────────────────────────────────────────────

   Full-screen overlay with card, action buttons, progress bar,
   keyboard shortcuts hint.
*/

"use client";

import { useState, useEffect, useCallback } from "react";
import { ReviewProgress } from "./review-progress";
import { ReviewCard } from "./review-card";
import { ReviewActions } from "./review-actions";
import { KeyboardHint } from "./keyboard-hint";
import { ReviewSummary } from "./review-summary";
import { X } from "lucide-react";
import { type PipelineCandidate } from "@/components/pipeline/types";

interface QuickReviewOverlayProps {
  candidates: PipelineCandidate[];
  batch_size?: number;
  onClose: () => void;
}

export function QuickReviewOverlay({
  candidates,
  batch_size = 20,
  onClose,
}: QuickReviewOverlayProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [approved, setApproved] = useState<string[]>([]);
  const [rejected, setRejected] = useState<string[]>([]);

  const batch = candidates.slice(0, batch_size);
  const current = batch[currentIndex];
  const isComplete = currentIndex >= batch.length;

  const handleApprove = useCallback(() => {
    if (!current) return;
    setApproved((prev) => [...prev, current.id]);
    setCurrentIndex((i) => i + 1);
  }, [current]);

  const handleReject = useCallback(() => {
    if (!current) return;
    setRejected((prev) => [...prev, current.id]);
    setCurrentIndex((i) => i + 1);
  }, [current]);

  // Keyboard navigation
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (isComplete) return;
      if (e.key === "ArrowLeft") handleReject();
      if (e.key === "ArrowRight") handleApprove();
      if (e.key === " ") {
        e.preventDefault();
        // View details — could open expanded detail
      }
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleApprove, handleReject, onClose, isComplete]);

  if (isComplete || batch.length === 0) {
    return (
      <div className="fixed inset-0 z-50 bg-surface flex items-center justify-center">
        <div className="w-full max-w-lg p-8">
          <ReviewSummary
            approved={approved}
            rejected={rejected}
            total={batch.length}
            onClose={onClose}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-surface flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <div className="flex items-center gap-4">
          <h2 className="text-sm font-semibold text-text-primary">Quick Review</h2>
          <ReviewProgress current={currentIndex + 1} total={batch.length} />
        </div>
        <button
          onClick={onClose}
          className="rounded-button p-1.5 text-text-tertiary hover:bg-hover hover:text-text-secondary"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Card */}
      <div className="flex-1 flex items-center justify-center p-8">
        {current && <ReviewCard candidate={current} />}
      </div>

      {/* Actions */}
      <div className="border-t border-border px-6 py-4">
        <ReviewActions onApprove={handleApprove} onReject={handleReject} onViewDetails={() => {}} />
        <KeyboardHint />
      </div>
    </div>
  );
}
