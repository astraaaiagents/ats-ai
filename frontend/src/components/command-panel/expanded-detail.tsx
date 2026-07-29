/* ── ExpandedDetail ─────────────────────────────────────────────────

   440px. Full candidate profile — avatar, contact, fit breakdown,
   strengths/gaps, skills tags, CTA buttons. Breadcrumb "← Back to chat".
*/

"use client";

import { ArrowLeft, Mail, Phone, MapPin, Clock } from "lucide-react";
import { useCommandPanel } from "@/lib/store/ui";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FitBadge } from "@/components/shared/fit-badge";
import { SkillTags } from "@/components/shared/skill-tags";
import { useCandidate } from "@/lib/api/hooks";

interface ExpandedDetailProps {
  candidateId: string;
}

export function ExpandedDetail({ candidateId }: ExpandedDetailProps) {
  const { setMode, setExpandedCandidate } = useCommandPanel();

  // Fetch live candidate data
  const { data: apiCandidate, isLoading, error } = useCandidate(candidateId);

  // Map API response to UI shape
  const candidate = apiCandidate ? {
    id: apiCandidate.id,
    name: `${apiCandidate.first_name} ${apiCandidate.last_name}`,
    title: apiCandidate.current_title || "Unknown Title",
    email: apiCandidate.email,
    phone: apiCandidate.phone || "No phone provided",
    location: apiCandidate.location || "Unknown Location",
    notice: apiCandidate.notice_period_days ? `${apiCandidate.notice_period_days} days` : "Unknown",
    fitScore: 85, // Stub for now, can come from candidate detail if added to backend
    strengths: ["React", "TypeScript", "Node.js"], // Stubs for UI design
    gaps: ["Kubernetes", "GraphQL"],
    skills: apiCandidate.skills?.map(s => s.skill_name) || [],
  } : null;

  if (isLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8" style={{ width: 440 }}>
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <p className="mt-4 text-xs text-text-secondary">Loading profile...</p>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="flex h-full flex-col p-8" style={{ width: 440 }}>
        <p className="text-sm text-error">Failed to load candidate profile.</p>
        <Button variant="outline" className="mt-4 w-fit" onClick={() => setExpandedCandidate(null)}>
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col" style={{ width: 440 }}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-text-secondary"
          onClick={() => {
            setExpandedCandidate(null);
          }}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <span className="text-xs font-semibold text-text-primary">Candidate Profile</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Avatar + Name */}
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-light text-primary text-lg font-semibold">
            {candidate.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-text-primary">{candidate.name}</h3>
            <p className="text-xs text-text-secondary">{candidate.title}</p>
          </div>
          <FitBadge score={candidate.fitScore} size="sm" />
        </div>

        {/* Contact Info */}
        <div className="space-y-1.5 text-xs text-text-secondary">
          <div className="flex items-center gap-2">
            <Mail className="h-3.5 w-3.5 text-text-tertiary" />
            <span>{candidate.email}</span>
          </div>
          <div className="flex items-center gap-2">
            <Phone className="h-3.5 w-3.5 text-text-tertiary" />
            <span>{candidate.phone}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="h-3.5 w-3.5 text-text-tertiary" />
            <span>{candidate.location}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-3.5 w-3.5 text-text-tertiary" />
            <span>{candidate.notice}</span>
          </div>
        </div>

        {/* Skills */}
        <div>
          <h4 className="mb-1.5 text-xs font-semibold text-text-primary">Skills</h4>
          <SkillTags skills={candidate.skills} maxDisplay={6} />
        </div>

        {/* Strengths */}
        <div>
          <h4 className="mb-1.5 text-xs font-semibold text-success">Strengths</h4>
          <div className="flex flex-wrap gap-1">
            {candidate.strengths.map((s) => (
              <Badge key={s} variant="success" className="rounded-badge">
                {s}
              </Badge>
            ))}
          </div>
        </div>

        {/* Gaps */}
        <div>
          <h4 className="mb-1.5 text-xs font-semibold text-warning">Gaps</h4>
          <div className="flex flex-wrap gap-1">
            {candidate.gaps.map((g) => (
              <Badge key={g} variant="lowConfidence" className="rounded-badge">
                {g}
              </Badge>
            ))}
          </div>
        </div>

        {/* Fit Breakdown */}
        <div>
          <h4 className="mb-1.5 text-xs font-semibold text-text-primary">Fit Breakdown</h4>
          <div className="space-y-1.5">
            {[
              { label: "Skills Match", score: 90 },
              { label: "Experience", score: 85 },
              { label: "Location", score: 100 },
              { label: "Notice Period", score: 75 },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <span className="w-24 text-[11px] text-text-secondary">{item.label}</span>
                <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${item.score}%` }}
                  />
                </div>
                <span className="w-8 text-right text-[11px] font-medium text-text-primary">
                  {item.score}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Actions */}
      <div className="flex gap-2 border-t border-border p-3">
        <Button size="sm" className="flex-1">
          Approve
        </Button>
        <Button size="sm" variant="outline" className="flex-1">
          Submit
        </Button>
        <Button size="sm" variant="outline" className="flex-1">
          Reject
        </Button>
      </div>
    </div>
  );
}
