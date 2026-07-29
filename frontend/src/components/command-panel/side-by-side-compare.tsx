/* ── SideBySideCompare ──────────────────────────────────────────────

   440px split. Two 50% columns for /compare command.
*/

"use client";

import { useCommandPanel } from "@/lib/store/ui";
import { FitBadge } from "@/components/shared/fit-badge";
import { SkillTags } from "@/components/shared/skill-tags";
import { useCandidate } from "@/lib/api/hooks";
import type { CandidateResponse } from "@/lib/api/types";

interface SideBySideCompareProps {
  candidateIdA: string;
  candidateIdB: string;
}

export function SideBySideCompare({ candidateIdA, candidateIdB }: SideBySideCompareProps) {
  const { clearCompare } = useCommandPanel();

  const { data: candA, isLoading: loadingA } = useCandidate(candidateIdA);
  const { data: candB, isLoading: loadingB } = useCandidate(candidateIdB);

  if (loadingA || loadingB) {
    return (
      <div className="flex h-full items-center justify-center p-8" style={{ width: 440 }}>
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <p className="ml-3 text-xs text-text-secondary">Loading comparison...</p>
      </div>
    );
  }

  const mapCandidate = (cand: CandidateResponse | undefined) => {
    if (!cand) return null;
    return {
      name: `${cand.first_name} ${cand.last_name}`,
      title: cand.current_title || "Unknown Title",
      fitScore: 85, // Stub for now
      skills: cand.skills?.map((s) => s.skill_name) || [],
      strengths: ["Stub Strength"], // Stub
    };
  };

  const a = mapCandidate(candA);
  const b = mapCandidate(candB);

  return (
    <div className="flex h-full relative" style={{ width: 440 }}>
      {/* Column A */}
      {a && (
        <div className="flex-1 border-r border-border p-3 space-y-3 overflow-y-auto">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-light text-primary text-xs font-medium">
              {a.name.split(" ").map((n: string) => n[0]).join("")}
            </div>
            <div>
              <div className="text-xs font-semibold text-text-primary">{a.name}</div>
              <div className="text-[11px] text-text-secondary">{a.title}</div>
            </div>
          </div>
          <FitBadge score={a.fitScore} size="sm" />
          <SkillTags skills={a.skills} />
          <div>
            <div className="text-[10px] font-semibold text-success mb-1">Strengths</div>
            {a.strengths.map((s: string) => (
              <div key={s} className="text-[11px] text-text-secondary">• {s}</div>
            ))}
          </div>
        </div>
      )}

      {/* Column B */}
      {b && (
        <div className="flex-1 p-3 space-y-3 overflow-y-auto">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ai-light text-ai text-xs font-medium">
              {b.name.split(" ").map((n: string) => n[0]).join("")}
            </div>
            <div>
              <div className="text-xs font-semibold text-text-primary">{b.name}</div>
              <div className="text-[11px] text-text-secondary">{b.title}</div>
            </div>
          </div>
          <FitBadge score={b.fitScore} size="sm" />
          <SkillTags skills={b.skills} />
          <div>
            <div className="text-[10px] font-semibold text-success mb-1">Strengths</div>
            {b.strengths.map((s: string) => (
              <div key={s} className="text-[11px] text-text-secondary">• {s}</div>
            ))}
          </div>
        </div>
      )}

      {/* Close */}
      <button
        onClick={clearCompare}
        className="absolute right-2 top-2 text-text-tertiary hover:text-text-secondary z-10"
      >
        ✕
      </button>
    </div>
  );
}
