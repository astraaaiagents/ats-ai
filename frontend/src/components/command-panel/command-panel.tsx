/* ── CommandPanel ───────────────────────────────────────────────────

   Persistent right-side panel. Three states:
   1. Compact Chat (340px default)
   2. Expanded Detail (440px)
   3. Side-by-Side Compare (440px split)
*/

"use client";

import { useCommandPanel } from "@/lib/store/ui";
import { CompactChat } from "./compact-chat";
import { ExpandedDetail } from "./expanded-detail";
import { SideBySideCompare } from "./side-by-side-compare";

export function CommandPanel() {
  const { mode, expandedCandidateId, compareCandidates } = useCommandPanel();

  if (mode === "closed") return null;

  // Expanded detail takes priority
  if (mode === "expanded" && expandedCandidateId) {
    return (
      <div className="h-full border-l border-border bg-elevated">
        <ExpandedDetail candidateId={expandedCandidateId} />
      </div>
    );
  }

  // Compare takes priority
  if (mode === "compare" && compareCandidates.length === 2) {
    return (
      <div className="h-full border-l border-border bg-elevated">
        <SideBySideCompare
          candidateIdA={compareCandidates[0]}
          candidateIdB={compareCandidates[1]}
        />
      </div>
    );
  }

  // Default: compact chat
  return (
    <div className="h-full border-l border-border bg-elevated">
      <CompactChat />
    </div>
  );
}
