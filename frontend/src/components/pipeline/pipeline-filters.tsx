/* ── PipelineFilters ────────────────────────────────────────────────

   Collapsible filter bar below job selector.
   Filters: skill (multi-select chips), fit score range, experience, location, visa.
*/

"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

const SKILL_CHIPS = [
  "Java", "Python", "React", "TypeScript", "AWS", "Docker",
  "Kubernetes", "Go", "Node.js", "PostgreSQL", "GraphQL",
];

export function PipelineFilters() {
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [fitRange, setFitRange] = useState([40, 100]);
  const [location, setLocation] = useState("");

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  return (
    <div className="rounded-card border border-border bg-card p-3 space-y-3">
      {/* Skills */}
      <div>
        <label className="mb-1.5 block text-xs font-medium text-text-secondary">Skills</label>
        <div className="flex flex-wrap gap-1.5">
          {SKILL_CHIPS.map((skill) => (
            <button
              key={skill}
              onClick={() => toggleSkill(skill)}
              className={cn(
                "rounded-badge border px-2 py-0.5 text-xs font-medium transition",
                selectedSkills.includes(skill)
                  ? "border-primary bg-primary-light text-primary"
                  : "border-border bg-surface text-text-secondary hover:border-primary/50"
              )}
            >
              {skill}
            </button>
          ))}
        </div>
      </div>

      {/* Fit Score Range */}
      <div>
        <label className="mb-1.5 block text-xs font-medium text-text-secondary">
          Fit Score: {fitRange[0]}–{fitRange[1]}%
        </label>
        <Slider
          value={fitRange}
          onValueChange={(v) => setFitRange(v as [number, number])}
          min={0}
          max={100}
          step={5}
          className="w-full"
        />
      </div>

      {/* Location */}
      <div>
        <label className="mb-1.5 block text-xs font-medium text-text-secondary">Location</label>
        <Input
          placeholder="e.g. San Francisco, CA"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="h-8 text-sm"
        />
      </div>
    </div>
  );
}
