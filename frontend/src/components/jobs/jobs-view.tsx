/* ── JobsView ───────────────────────────────────────────────────────

   Card-based job list loaded from client-contacts API.
*/

"use client";

import { useState, useMemo } from "react";
import { JobsFilters } from "./jobs-filters";
import { JobCard } from "./job-card";
import { EmptyState } from "@/components/shared/empty-state";
import { type Job } from "@/lib/api/types";
import { useClientContacts } from "@/lib/api/hooks";

export function JobsView() {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [domainFilter, setDomainFilter] = useState<string[]>([]);
  const [clientSearch, setClientSearch] = useState("");
  const [roleSearch, setRoleSearch] = useState("");

  const { data: contactsResponse, isLoading } = useClientContacts();

  // Transform client contacts to Job format
  const jobs = useMemo<Job[]>(() => {
    if (!contactsResponse) return [];
    const contacts = Array.isArray(contactsResponse)
      ? contactsResponse
      : (contactsResponse as { data?: Array<Record<string, unknown>> }).data || [];
    return contacts.map((contact: Record<string, unknown>) => ({
      id: String(contact.id || ""),
      req_id: String(contact.req_id || contact.job_id || ""),
      client_name: String(contact.organization_name || contact.client || "Unknown Client"),
      role_title: String(contact.title || "Untitled Position"),
      location: String(contact.location || "Remote"),
      status: (contact.status as Job["status"]) || "needs_attention",
      domains: (contact.domains as string[]) || [],
      candidate_count: Number(contact.candidate_count || 0),
      pipeline_summary: String(contact.pipeline_summary || "0R · 0S · 0I"),
      agent_insight: String(contact.agent_insight || ""),
    }));
  }, [contactsResponse]);

  const filtered = useMemo(() => {
    return jobs.filter((job) => {
      if (statusFilter !== "all" && job.status !== statusFilter) return false;
      if (domainFilter.length > 0 && !domainFilter.some((d) => job.domains.includes(d))) return false;
      if (clientSearch && !job.client_name.toLowerCase().includes(clientSearch.toLowerCase())) return false;
      if (roleSearch && !job.role_title.toLowerCase().includes(roleSearch.toLowerCase())) return false;
      return true;
    });
  }, [jobs, statusFilter, domainFilter, clientSearch, roleSearch]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-card border border-border p-4 animate-pulse">
            <div className="h-4 bg-border/50 rounded w-1/3 mb-2" />
            <div className="h-3 bg-border/50 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (filtered.length === 0) {
    return (
      <EmptyState
        title={jobs.length === 0 ? "No jobs yet" : "No jobs match your filters"}
        description={jobs.length === 0 ? "Client contacts will appear here when added." : "Try adjusting your search criteria."}
      />
    );
  }

  return (
    <div className="space-y-4">
      <JobsFilters
        clientSearch={clientSearch}
        roleSearch={roleSearch}
        statusFilter={statusFilter}
        domainFilter={domainFilter}
        onClientSearchChange={setClientSearch}
        onRoleSearchChange={setRoleSearch}
        onStatusFilterChange={setStatusFilter}
        onDomainFilterChange={setDomainFilter}
      />
      <div className="space-y-3">
        {filtered.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </div>
  );
}
