/* ── AgentInsight ───────────────────────────────────────────────────

   "Strong pipeline", "Pipeline too thin", etc.
*/

"use client";

import { cn } from "@/lib/utils";
import { Lightbulb } from "lucide-react";

interface AgentInsightProps {
  insight: string;
}

export function AgentInsight({ insight }: AgentInsightProps) {
  return (
    <div className={cn(
      "flex items-start gap-2 rounded-button bg-surface p-2 text-xs",
    )}>
      <Lightbulb className="h-3.5 w-3.5 shrink-0 text-ai mt-0.5" />
      <span className="text-text-secondary">{insight}</span>
    </div>
  );
}
