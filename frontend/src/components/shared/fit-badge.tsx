/* ── FitBadge ───────────────────────────────────────────────────────

   Fit score display with score number and star rating.
*/

import { cn } from "@/lib/utils";

interface FitBadgeProps {
  score: number; // 0-100
  size?: "sm" | "md" | "lg";
  className?: string;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "text-success";
  if (score >= 60) return "text-primary";
  if (score >= 40) return "text-warning";
  return "text-danger";
}

function getStars(score: number): number {
  return Math.round(score / 20);
}

export function FitBadge({ score, size = "md", className }: FitBadgeProps) {
  const color = getScoreColor(score);
  const stars = getStars(score);
  const textSize = size === "lg" ? "text-lg" : size === "sm" ? "text-xs" : "text-sm";
  const iconSize = size === "lg" ? "text-base" : "text-xs";

  return (
    <div className={cn("inline-flex items-center gap-1", className)}>
      <span className={cn("font-semibold", textSize, color)}>
        {score}%
      </span>
      <span className={cn("text-yellow-500", iconSize)}>
        {"★".repeat(stars)}{"☆".repeat(5 - stars)}
      </span>
    </div>
  );
}
