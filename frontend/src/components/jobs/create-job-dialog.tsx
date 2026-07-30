/* ── CreateJobDialog ─────────────────────────────────────────────────

   Dialog modal with form for creating a new job (client contact).
   Uses useCreateClientContact mutation hook.
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
import { useCreateClientContact } from "@/lib/api/hooks";
import type { ClientContactCreateRequest } from "@/lib/api/types";

interface CreateJobDialogProps {
  open: boolean;
  onClose: () => void;
}

interface JobFormData {
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  organization_name: string;
  title: string;
  location: string;
  description: string;
  status: string;
}

const initialFormData: JobFormData = {
  email: "",
  first_name: "",
  last_name: "",
  phone: "",
  organization_name: "",
  title: "",
  location: "",
  description: "",
  status: "active",
};

export function CreateJobDialog({ open, onClose }: CreateJobDialogProps) {
  const [form, setForm] = useState<JobFormData>(initialFormData);
  const [error, setError] = useState<string | null>(null);
  const createMutation = useCreateClientContact();

  const handleChange = useCallback(
    (field: keyof JobFormData, value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      setError(null);
    },
    [],
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      // Validate required fields
      if (!form.email.trim() || !form.first_name.trim() || !form.last_name.trim()) {
        setError("Email, first name, and last name are required.");
        return;
      }

      // Build payload
      const payload: ClientContactCreateRequest = {
        email: form.email.trim().toLowerCase(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone.trim() || null,
        organization_name: form.organization_name.trim() || null,
        title: form.title.trim() || null,
        location: form.location.trim() || null,
        description: form.description.trim() || null,
        status: form.status.trim() || "active",
      };

      createMutation.mutate(payload, {
        onError: (err: Error) => {
          setError(err.message || "Failed to create job.");
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
          <DialogTitle>Create Job</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Required Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Email <span className="text-danger">*</span>
              </label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => handleChange("email", e.target.value)}
                placeholder="contact@company.com"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                First Name <span className="text-danger">*</span>
              </label>
              <Input
                value={form.first_name}
                onChange={(e) => handleChange("first_name", e.target.value)}
                placeholder="John"
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
                placeholder="Smith"
                required
              />
            </div>
          </div>

          {/* Optional Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Organization</label>
              <Input
                value={form.organization_name}
                onChange={(e) => handleChange("organization_name", e.target.value)}
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Role Title</label>
              <Input
                value={form.title}
                onChange={(e) => handleChange("title", e.target.value)}
                placeholder="Senior Java Developer"
              />
            </div>
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
              <label className="block text-xs font-medium text-text-secondary mb-1">Location</label>
              <Input
                value={form.location}
                onChange={(e) => handleChange("location", e.target.value)}
                placeholder="Remote"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => handleChange("description", e.target.value)}
              placeholder="Job description..."
              rows={3}
              className="w-full rounded-input border border-border bg-elevated px-3 py-1.5 text-sm text-text-primary shadow-sm transition placeholder:text-text-tertiary focus:border-border-focus focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
            />
          </div>

          {/* Status */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Status</label>
            <select
              value={form.status}
              onChange={(e) => handleChange("status", e.target.value)}
              className="flex h-9 w-full rounded-input border border-border bg-elevated px-3 py-1.5 text-sm text-text-primary shadow-sm transition focus:border-border-focus focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="active">Active</option>
              <option value="on_hold">On Hold</option>
              <option value="filled">Filled</option>
              <option value="closed">Closed</option>
            </select>
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
              {createMutation.isPending ? "Creating..." : "Create Job"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
