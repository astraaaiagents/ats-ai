/* ── ColumnHeader ───────────────────────────────────────────────────

   Name + count + Quick Review button.
*/

"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ColumnHeaderProps {
  label: string;
  count: number;
  stageColor: string;
}

export function ColumnHeader({ label, count, stageColor }: ColumnHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-border px-3 py-2">
      <div className="flex items-center gap-2">
        <span className={cn("h-2 w-2 rounded-full", stageColor)} />
        <span className="text-xs font-semibold text-text-primary">{label}</span>
        <span className="rounded-badge bg-surface-hover px-1.5 py-0.5 text-[10px] text-text-tertiary">
          {count}
        </span>
      </div>
      {label === "Sourced" && count > 0 && (
        <Button size="sm" variant="ghost" className="h-6 px-2 text-[10px] text-primary hover:bg-primary-light">
          Quick Review
        </Button>
      )}
    </div>
  );
}
