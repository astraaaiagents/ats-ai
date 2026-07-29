/* ── JobSelector ────────────────────────────────────────────────────

   Dropdown with search, "All Jobs" option, breadcrumb.
*/

"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface JobSelectorProps {
  selectedJob: string | null;
  onChange: (jobId: string | null) => void;
}

const MOCK_JOBS = [
  { id: "all", name: "All Jobs" },
  { id: "job-1", name: "TCS — Java Lead" },
  { id: "job-2", name: "Infosys — Python Senior" },
  { id: "job-3", name: "Wipro — Data Engineer" },
];

export function JobSelector({ selectedJob, onChange }: JobSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filtered = MOCK_JOBS.filter((j) =>
    j.name.toLowerCase().includes(search.toLowerCase())
  );

  const selected = MOCK_JOBS.find((j) => j.id === selectedJob);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen((v) => !v)}
        className={cn(
          "flex w-full items-center justify-between rounded-card border border-border bg-card px-3 py-2 text-sm transition hover:border-primary/50",
          isOpen && "border-primary"
        )}
      >
        <span className="text-text-primary">
          {selected?.name || "All Jobs"}
        </span>
        <ChevronDown className={cn("h-4 w-4 text-text-tertiary transition", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute z-40 mt-1 w-full rounded-card border border-border bg-elevated shadow-lg animate-fade-in">
          <div className="flex items-center gap-2 border-b border-border px-3 py-2">
            <Search className="h-4 w-4 text-text-tertiary" />
            <Input
              placeholder="Search jobs…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-7 text-sm"
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto p-1">
            {filtered.map((job) => (
              <button
                key={job.id}
                onClick={() => {
                  onChange(job.id === "all" ? null : job.id);
                  setIsOpen(false);
                }}
                className={cn(
                  "flex w-full items-center justify-between rounded-button px-3 py-1.5 text-sm transition",
                  (job.id === "all" && !selectedJob) || selectedJob === job.id
                    ? "bg-primary text-white"
                    : "text-text-primary hover:bg-hover"
                )}
              >
                <span>{job.name}</span>
                {job.id === "all" && !selectedJob && <span className="text-xs">●</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
