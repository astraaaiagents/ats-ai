/* ── AppShell ───────────────────────────────────────────────────────

   TopNav + main content + CommandPanel.
   Responsive: ≥1280px full two-panel; 1024-1279px collapsible.
*/

"use client";

import { type ReactNode, useState } from "react";
import { TopNav } from "./top-nav";
import { CommandPanel } from "@/components/command-panel/command-panel";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";
import { useSearch } from "@/lib/store/ui";

type TabKey = "feed" | "pipeline" | "jobs" | "preferences" | "analytics";

interface AppShellProps {
  children: ReactNode;
  defaultTab: TabKey;
}

export function AppShell({ children, defaultTab }: AppShellProps) {
  const [commandPanelOpen, setCommandPanelOpen] = useState(true);
  const { open: openSearch } = useSearch();

  // Cmd+K for global search
  useKeyboardShortcut("k", "metaKey", openSearch);

  return (
    <div className="flex h-screen flex-col">
      <TopNav activeTab={defaultTab} onPanelToggle={() => setCommandPanelOpen((v) => !v)} />
      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-y-auto p-4">
          {children}
        </main>
        {commandPanelOpen && (
          <aside className="hidden xl:block">
            <CommandPanel />
          </aside>
        )}
      </div>
    </div>
  );
}
