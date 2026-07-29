/* ── FeedBadge ──────────────────────────────────────────────────────

   AI-GENERATED, LOW CONFIDENCE, AGENT SUGGESTION, PREFERENCE UPDATED, LEARNING.
*/

import { Badge } from "@/components/ui/badge";

interface FeedBadgeProps {
  badge: string;
}

const BADGE_MAP: Record<string, { variant: "ai" | "lowConfidence" | "agentSuggestion" | "preferenceUpdated" | "learning" | "success" | "user" | "alert" | "submitted" }> = {
  "AI-GENERATED": { variant: "ai" },
  "LOW CONFIDENCE": { variant: "lowConfidence" },
  "AGENT SUGGESTION": { variant: "agentSuggestion" },
  "PREFERENCE UPDATED": { variant: "preferenceUpdated" },
  "LEARNING": { variant: "learning" },
  "YOU": { variant: "user" },
  "SUBMITTED": { variant: "submitted" },
  "ALERT": { variant: "alert" },
};

export function FeedBadge({ badge }: FeedBadgeProps) {
  const config = BADGE_MAP[badge] || { variant: "ai" as const };
  return (
    <Badge variant={config.variant} className="rounded-badge">
      {badge}
    </Badge>
  );
}
