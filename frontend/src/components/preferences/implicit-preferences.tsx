/* ── ImplicitPreferences ────────────────────────────────────────────

   Learned patterns with confidence, strength bars, override/remove.
   Loads implicit scores from the API.
*/

"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Eye } from "lucide-react";
import { usePreferences } from "@/lib/api/hooks";

interface ImplicitPreference {
  id: string;
  pattern: string;
  confidence: "High" | "Medium" | "Low";
  strength: number; // 0-100
  evidence: string;
}

export function ImplicitPreferences() {
  const { data: prefs, isLoading } = usePreferences();
  const [showingEvidence, setShowingEvidence] = useState<string | null>(null);

  const implicitScores = prefs?.implicit_scores;

  const patterns = useMemo<ImplicitPreference[]>(() => {
    if (!implicitScores) return [];
    return Object.entries(implicitScores)
      .filter(([, score]) => score !== 0.5) // Only show non-neutral scores
      .map(([pattern, score]) => {
        const strength = Math.round(score * 100);
        const confidence: "High" | "Medium" | "Low" =
          score >= 0.7 ? "High" : score >= 0.6 ? "Medium" : "Low";
        return {
          id: pattern,
          pattern: pattern.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          confidence,
          strength,
          evidence: `Score: ${score.toFixed(2)} (0.0 = avoid, 1.0 = prefer)`,
        };
      })
      .sort((a, b) => Math.abs(b.strength - 50) - Math.abs(a.strength - 50));
  }, [implicitScores]);

  if (isLoading) {
    return <div className="text-sm text-text-tertiary">Loading learned patterns...</div>;
  }

  if (patterns.length === 0) {
    return (
      <div className="text-sm text-text-tertiary italic py-4 text-center">
        No learned patterns yet. The agent learns from your approval and rejection patterns.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {patterns.map((pattern) => (
        <div
          key={pattern.id}
          className="rounded-card border border-border bg-card p-4 space-y-2"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-text-primary">{pattern.pattern}</span>
                <Badge
                  variant={
                    pattern.confidence === "High"
                      ? "success"
                      : pattern.confidence === "Medium"
                      ? "lowConfidence"
                      : "destructive"
                  }
                  className="rounded-badge"
                >
                  {pattern.confidence}
                </Badge>
              </div>
              {/* Strength bar */}
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      pattern.strength > 50 ? "bg-primary" : "bg-danger"
                    }`}
                    style={{ width: `${pattern.strength}%` }}
                  />
                </div>
                <span className="text-xs text-text-tertiary w-8 text-right">
                  {pattern.strength}%
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={() =>
                  setShowingEvidence(
                    showingEvidence === pattern.id ? null : pattern.id
                  )
                }
              >
                <Eye className="h-3.5 w-3.5 text-text-tertiary" />
              </Button>
            </div>
          </div>
          {showingEvidence === pattern.id && (
            <div className="rounded-button bg-surface p-2 text-xs text-text-secondary">
              {pattern.evidence}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
