/* ── SkillTags ──────────────────────────────────────────────────────

   Colored pill tags for candidate skills.
*/

import { cn } from "@/lib/utils";

interface SkillTagsProps {
  skills: string[];
  maxDisplay?: number;
  className?: string;
}

const SKILL_COLORS = [
  "bg-primary-light text-primary",
  "bg-ai-light text-ai",
  "bg-info-light text-info",
  "bg-success-light text-success",
  "bg-warning-light text-warning",
  "bg-danger-light text-danger",
];

function getSkillColor(skill: string, index: number): string {
  return SKILL_COLORS[index % SKILL_COLORS.length];
}

export function SkillTags({ skills, maxDisplay = 5, className }: SkillTagsProps) {
  const displayed = skills.slice(0, maxDisplay);
  const remaining = skills.length - maxDisplay;

  return (
    <div className={cn("flex flex-wrap gap-1", className)}>
      {displayed.map((skill, i) => (
        <span
          key={skill}
          className={cn(
            "rounded-badge px-2 py-0.5 text-xs font-medium",
            getSkillColor(skill, i)
          )}
        >
          {skill}
        </span>
      ))}
      {remaining > 0 && (
        <span className="rounded-badge bg-surface-hover px-2 py-0.5 text-xs text-text-secondary">
          +{remaining}
        </span>
      )}
    </div>
  );
}
