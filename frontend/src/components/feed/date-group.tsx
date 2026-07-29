/* ── DateGroup ──────────────────────────────────────────────────────

   "Today", "Yesterday", date headers.
*/

import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

interface DateGroupProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export function DateGroup({ label, children, className }: DateGroupProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="sticky top-0 z-10 bg-surface px-1 py-1.5">
        <span className="text-xs font-semibold text-text-tertiary">{label}</span>
      </div>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  );
}
