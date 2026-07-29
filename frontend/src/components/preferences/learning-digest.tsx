/* ── LearningDigest ─────────────────────────────────────────────────

   Weekly summary banner with trends.
*/

"use client";

import { TrendingUp, TrendingDown, CheckCircle2, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function LearningDigest() {
  return (
    <div className="rounded-card border border-ai/20 bg-ai-light p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="learning" className="rounded-badge">
              LEARNING
            </Badge>
            <span className="text-xs text-text-tertiary">Weekly Summary — Jul 20–27</span>
          </div>
          <h3 className="text-sm font-semibold text-text-primary">
            Your agent learned 3 new patterns this week
          </h3>
          <div className="mt-2 space-y-1.5">
            <div className="flex items-center gap-2 text-xs text-text-secondary">
              <TrendingUp className="h-3.5 w-3.5 text-success" />
              <span>AWS experience preference strengthened (+12%)</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-text-secondary">
              <TrendingUp className="h-3.5 w-3.5 text-success" />
              <span>Leadership experience preference strengthened (+8%)</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-text-secondary">
              <TrendingDown className="h-3.5 w-3.5 text-warning" />
              <span>Notice period tolerance decreased (-5%)</span>
            </div>
          </div>
        </div>
        <Button size="sm" variant="outline" className="h-8 text-xs shrink-0 ml-4">
          Review
        </Button>
      </div>
    </div>
  );
}
