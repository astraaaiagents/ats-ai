/* ── ReviewProgress ─────────────────────────────────────────────────

   X/20 candidates progress bar.
*/

"use client";

import { Progress } from "@/components/ui/progress";

interface ReviewProgressProps {
  current: number;
  total: number;
}

export function ReviewProgress({ current, total }: ReviewProgressProps) {
  const percentage = Math.round((current / total) * 100);

  return (
    <div className="flex items-center gap-3 w-48">
      <Progress value={percentage} className="flex-1" />
      <span className="text-xs text-text-tertiary whitespace-nowrap">
        {current}/{total}
      </span>
    </div>
  );
}
