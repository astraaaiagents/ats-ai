/* ── QuickActionChips ───────────────────────────────────────────────

   /find, /submit, /schedule, /prefs, /outreach, /quick-review
*/

"use client";

import { cn } from "@/lib/utils";

interface QuickActionChipsProps {
  onAction: (action: string) => void;
}

const ACTIONS = [
  { label: "/find", description: "Find candidates" },
  { label: "/submit", description: "Submit candidate" },
  { label: "/schedule", description: "Schedule interview" },
  { label: "/prefs", description: "Update preferences" },
  { label: "/outreach", description: "Draft outreach" },
  { label: "/quick-review", description: "Quick review" },
];

export function QuickActionChips({ onAction }: QuickActionChipsProps) {
  return (
    <div className="flex flex-wrap gap-1.5 px-3 py-2 border-t border-border">
      {ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => onAction(action.label)}
          className={cn(
            "rounded-badge border border-border bg-surface px-2 py-0.5 text-[11px] font-medium text-text-secondary transition hover:border-primary hover:text-primary"
          )}
          title={action.description}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
