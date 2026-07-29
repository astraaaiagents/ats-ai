/* ── ExplicitPreferences ────────────────────────────────────────────

   Rule list with toggles, "Add Rule" button.
   Loads explicit preferences from the API.
*/

"use client";

import { useState, useMemo } from "react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Plus } from "lucide-react";
import { usePreferences, useUpdatePreferences } from "@/lib/api/hooks";

interface PreferenceRule {
  id: string;
  field: string;
  value: string;
  enabled: boolean;
}

export function ExplicitPreferences() {
  const { data: prefs, isLoading } = usePreferences();
  const updateMutation = useUpdatePreferences();

  const rules = useMemo<PreferenceRule[]>(() => {
    if (!prefs?.explicit) return [];
    return Object.entries(prefs.explicit).map(([field, value]) => ({
      id: field,
      field,
      value: String(value),
      enabled: true,
    }));
  }, [prefs?.explicit]);

  const toggleRule = (id: string) => {
    const rule = rules.find((r) => r.id === id);
    if (!rule) return;
    // Toggle by removing/re-adding the key
    const updates = { ...prefs?.explicit };
    if (updates[id] !== undefined) {
      delete updates[id];
      updateMutation.mutate(updates);
    }
  };

  if (isLoading) {
    return <div className="text-sm text-text-tertiary">Loading preferences...</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Active Rules</h3>
        <span className="text-xs text-text-tertiary">
          Last updated: {prefs?.last_updated ? new Date(prefs.last_updated).toLocaleDateString("en-US", { timeZone: "UTC" }) : "—"}
        </span>
      </div>

      {rules.length === 0 ? (
        <div className="text-sm text-text-tertiary italic py-4 text-center">
          No explicit rules set. Add rules to guide candidate sourcing.
        </div>
      ) : (
        <div className="space-y-2">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className={`flex items-center justify-between rounded-card border p-3 transition ${
                rule.enabled ? "border-border bg-card" : "border-border bg-surface opacity-60"
              }`}
            >
              <div>
                <div className="text-sm font-medium text-text-primary">{rule.field}</div>
                <div className="text-xs text-text-secondary">{rule.value}</div>
              </div>
              <Switch
                checked={rule.enabled}
                onCheckedChange={() => toggleRule(rule.id)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
