/* ── TabBar ─────────────────────────────────────────────────────────

   Feed | Pipeline | Jobs | Preferences | Analytics.
*/

"use client";

import { usePathname, useRouter } from "next/navigation";

type TabKey = "conversations" | "feed" | "pipeline" | "jobs" | "preferences" | "analytics";

const TABS: { key: TabKey; label: string; path: string }[] = [
  { key: "conversations", label: "Conversations", path: "/?tab=conversations" },
  { key: "feed", label: "Feed", path: "/feed" },
  { key: "pipeline", label: "Pipeline", path: "/pipeline" },
  { key: "jobs", label: "Jobs", path: "/jobs" },
  { key: "preferences", label: "Preferences", path: "/preferences" },
  { key: "analytics", label: "Analytics", path: "/analytics" },
];

interface TabBarProps {
  activeTab: TabKey;
}

export function TabBar({ activeTab }: TabBarProps) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <nav className="flex gap-0.5" role="tablist">
      {TABS.map((tab) => {
        const isActive = activeTab === tab.key || pathname === tab.path;
        return (
          <button
            key={tab.key}
            role="tab"
            aria-selected={isActive}
            onClick={() => router.push(tab.path)}
            className={`rounded-button px-3 py-1 text-xs font-medium transition ${
              isActive
                ? "bg-primary text-white"
                : "text-text-secondary hover:bg-hover hover:text-text-primary"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
