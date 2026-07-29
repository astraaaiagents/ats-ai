/* ── JobsFilters ────────────────────────────────────────────────────

   Client search, role keyword, status dropdown, domain multi-select.
*/

"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface JobsFiltersProps {
  clientSearch: string;
  roleSearch: string;
  statusFilter: string;
  domainFilter: string[];
  onClientSearchChange: (v: string) => void;
  onRoleSearchChange: (v: string) => void;
  onStatusFilterChange: (v: string) => void;
  onDomainFilterChange: (v: string[]) => void;
}

const DOMAINS = ["Java", "Python", "React", "AWS", "Kubernetes", "Spark", "Microservices", "Go", "Data", "DevOps"];
const STATUSES = ["all", "healthy", "needs_attention", "on_track", "critical"] as const;

const STATUS_LABELS: Record<string, string> = {
  all: "All Statuses",
  healthy: "Healthy",
  needs_attention: "Needs Attention",
  on_track: "On Track",
  critical: "Critical",
};

const STATUS_COLORS: Record<string, string> = {
  all: "",
  healthy: "text-blue-500",
  needs_attention: "text-yellow-500",
  on_track: "text-green-500",
  critical: "text-red-500",
};

export function JobsFilters({
  clientSearch,
  roleSearch,
  statusFilter,
  domainFilter,
  onClientSearchChange,
  onRoleSearchChange,
  onStatusFilterChange,
  onDomainFilterChange,
}: JobsFiltersProps) {
  const toggleDomain = (domain: string) => {
    onDomainFilterChange(
      domainFilter.includes(domain)
        ? domainFilter.filter((d) => d !== domain)
        : [...domainFilter, domain]
    );
  };

  return (
    <div className="rounded-card border border-border bg-card p-3 space-y-3">
      <div className="flex flex-wrap gap-3">
        {/* Client Search */}
        <div className="flex-1 min-w-[160px]">
          <Input
            placeholder="Client name…"
            value={clientSearch}
            onChange={(e) => onClientSearchChange(e.target.value)}
            className="h-8 text-sm"
          />
        </div>

        {/* Role Search */}
        <div className="flex-1 min-w-[160px]">
          <Input
            placeholder="Role keyword…"
            value={roleSearch}
            onChange={(e) => onRoleSearchChange(e.target.value)}
            className="h-8 text-sm"
          />
        </div>

        {/* Status Dropdown */}
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          className="h-8 rounded-input border border-border bg-elevated px-2 text-sm text-text-primary outline-none focus:border-border-focus"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      {/* Domain Chips */}
      <div className="flex flex-wrap gap-1.5">
        {DOMAINS.map((domain) => (
          <button
            key={domain}
            onClick={() => toggleDomain(domain)}
            className={cn(
              "rounded-badge border px-2 py-0.5 text-xs font-medium transition",
              domainFilter.includes(domain)
                ? "border-primary bg-primary-light text-primary"
                : "border-border bg-surface text-text-secondary hover:border-primary/50"
            )}
          >
            {domain}
          </button>
        ))}
      </div>
    </div>
  );
}
