/* ── Preferences View Page ──────────────────────────────────────────

   Explicit + implicit preferences.
*/

"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PreferencesView } from "@/components/preferences/preferences-view";

export default function PreferencesPage() {
  return (
    <AppShell defaultTab="preferences">
      <PreferencesView />
    </AppShell>
  );
}
