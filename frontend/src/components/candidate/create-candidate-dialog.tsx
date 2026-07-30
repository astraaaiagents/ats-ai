/* ── CreateCandidateDialog ───────────────────────────────────────────

   Dialog modal with form for creating a new candidate.
   Uses useCreateCandidate mutation hook.
*/

"use client";

import { useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateCandidate } from "@/lib/api/hooks";
import type { CandidateSkillInput } from "@/lib/api/types";

interface CreateCandidateDialogProps {
  open: boolean;
  onClose: () => void;
}

interface CandidateFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  current_title: string;
  current_employer: string;
  location: string;
  salary_expectation_min: string;
  salary_expectation_max: string;
  visa_status: string;
  notice_period_days: string;
  source: string;
  skills: CandidateSkillInput[];
}

const initialFormData: CandidateFormData = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  current_title: "",
  current_employer: "",
  location: "",
  salary_expectation_min: "",
  salary_expectation_max: "",
  visa_status: "",
  notice_period_days: "",
  source: "",
  skills: [],
};

export function CreateCandidateDialog({ open, onClose }: CreateCandidateDialogProps) {
  const [form, setForm] = useState<CandidateFormData>(initialFormData);
  const [error, setError] = useState<string | null>(null);
  const createMutation = useCreateCandidate();

  const handleChange = useCallback(
    (field: keyof CandidateFormData, value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      setError(null);
    },
    [],
  );

  const handleSkillChange = useCallback(
    (index: number, field: keyof CandidateSkillInput, value: string | number | null) => {
      setForm((prev) => {
        const skills = [...prev.skills];
        skills[index] = { ...skills[index], [field]: value };
        return { ...prev, skills };
      });
    },
    [],
  );

  const addSkill = useCallback(() => {
    setForm((prev) => ({
      ...prev,
      skills: [...prev.skills, { skill_name: "", proficiency: null, years_experience: null }],
    }));
  }, []);

  const removeSkill = useCallback((index: number) => {
    setForm((prev) => ({
      ...prev,
      skills: prev.skills.filter((_, i) => i !== index),
    }));
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      // Validate required fields
      if (!form.first_name.trim() || !form.last_name.trim() || !form.email.trim()) {
        setError("First name, last name, and email are required.");
        return;
      }

      // Build payload
      const payload = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim().toLowerCase(),
        phone: form.phone.trim() || null,
        current_title: form.current_title.trim() || null,
        current_employer: form.current_employer.trim() || null,
        location: form.location.trim() || null,
        salary_expectation_min: form.salary_expectation_min ? Number(form.salary_expectation_min) : null,
        salary_expectation_max: form.salary_expectation_max ? Number(form.salary_expectation_max) : null,
        visa_status: form.visa_status.trim() || null,
        notice_period_days: form.notice_period_days ? Number(form.notice_period_days) : null,
        source: form.source.trim() || null,
        skills: form.skills.filter((s) => s.skill_name.trim()),
      };

      createMutation.mutate(payload, {
        onError: (err: Error) => {
          setError(err.message || "Failed to create candidate.");
        },
        onSuccess: () => {
          setForm(initialFormData);
          onClose();
        },
      });
    },
    [form, createMutation, onClose],
  );

  const handleClose = useCallback(() => {
    setForm(initialFormData);
    setError(null);
    onClose();
  }, [onClose]);

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Candidate</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Required Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                First Name <span className="text-danger">*</span>
              </label>
              <Input
                value={form.first_name}
                onChange={(e) => handleChange("first_name", e.target.value)}
                placeholder="Jane"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Last Name <span className="text-danger">*</span>
              </label>
              <Input
                value={form.last_name}
                onChange={(e) => handleChange("last_name", e.target.value)}
                placeholder="Doe"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Email <span className="text-danger">*</span>
              </label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => handleChange("email", e.target.value)}
                placeholder="jane@example.com"
                required
              />
            </div>
          </div>

          {/* Optional Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Phone</label>
              <Input
                type="tel"
                value={form.phone}
                onChange={(e) => handleChange("phone", e.target.value)}
                placeholder="+1 (555) 000-0000"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Current Title</label>
              <Input
                value={form.current_title}
                onChange={(e) => handleChange("current_title", e.target.value)}
                placeholder="Senior Engineer"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Current Employer</label>
              <Input
                value={form.current_employer}
                onChange={(e) => handleChange("current_employer", e.target.value)}
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Location</label>
              <Input
                value={form.location}
                onChange={(e) => handleChange("location", e.target.value)}
                placeholder="San Francisco, CA"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Visa Status</label>
              <Input
                value={form.visa_status}
                onChange={(e) => handleChange("visa_status", e.target.value)}
                placeholder="US Citizen"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Notice Period (days)</label>
              <Input
                type="number"
                value={form.notice_period_days}
                onChange={(e) => handleChange("notice_period_days", e.target.value)}
                placeholder="30"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Source</label>
              <Input
                value={form.source}
                onChange={(e) => handleChange("source", e.target.value)}
                placeholder="LinkedIn, Referral, etc."
              />
            </div>
          </div>

          {/* Salary */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Salary Expectation (min)</label>
              <Input
                type="number"
                value={form.salary_expectation_min}
                onChange={(e) => handleChange("salary_expectation_min", e.target.value)}
                placeholder="120000"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Salary Expectation (max)</label>
              <Input
                type="number"
                value={form.salary_expectation_max}
                onChange={(e) => handleChange("salary_expectation_max", e.target.value)}
                placeholder="150000"
              />
            </div>
          </div>

          {/* Skills */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-medium text-text-secondary">Skills</label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addSkill}
                className="text-xs h-7"
              >
                + Add Skill
              </Button>
            </div>
            {form.skills.length === 0 ? (
              <p className="text-xs text-text-tertiary italic">No skills added yet.</p>
            ) : (
              <div className="space-y-2">
                {form.skills.map((skill, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      value={skill.skill_name}
                      onChange={(e) => handleSkillChange(index, "skill_name", e.target.value)}
                      placeholder="Skill name"
                      className="flex-1 h-8 text-xs"
                    />
                    <Input
                      type="number"
                      value={skill.proficiency ?? ""}
                      onChange={(e) => handleSkillChange(index, "proficiency", Number(e.target.value) || null)}
                      placeholder="Prof."
                      className="w-20 h-8 text-xs"
                    />
                    <Input
                      type="number"
                      step="0.5"
                      value={skill.years_experience ?? ""}
                      onChange={(e) => handleSkillChange(index, "years_experience", Number(e.target.value) || null)}
                      placeholder="Yrs"
                      className="w-16 h-8 text-xs"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-text-tertiary hover:text-danger"
                      onClick={() => removeSkill(index)}
                    >
                      <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-input border border-danger bg-danger/10 px-3 py-2 text-xs text-danger">
              {error}
            </div>
          )}

          {/* Footer */}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Candidate"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
