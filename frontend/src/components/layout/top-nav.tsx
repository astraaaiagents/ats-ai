/* ── TopNav ─────────────────────────────────────────────────────────

   Logo + TabBar + SearchBar + NotificationBadge.
*/

"use client";

import { Search, Bell, PanelRightClose, PanelRightOpen } from "lucide-react";
import { TabBar } from "./tab-bar";
import { useSearch } from "@/lib/store/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type TabKey = "conversations" | "feed" | "pipeline" | "jobs" | "preferences" | "analytics";

interface TopNavProps {
  activeTab: TabKey;
  onPanelToggle?: () => void;
}

export function TopNav({ activeTab, onPanelToggle }: TopNavProps) {
  const { query, setQuery, isOpen, close } = useSearch();

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-elevated px-4">
      {/* Left: Logo + Tabs */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-semibold text-text-primary">
          {"⚡"} ATS Agent
        </span>
        <TabBar activeTab={activeTab} />
      </div>

      {/* Center: Search */}
      <div className="hidden md:flex flex-1 max-w-md mx-4">
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary" />
          <Input
            placeholder="Search candidates, jobs, conversations…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-8 pl-9 pr-16 rounded-input bg-surface border-0 text-sm"
          />
          <kbd className="absolute right-2 top-1/2 -translate-y-1/2 rounded-button border border-border bg-surface px-1.5 py-0.5 text-[10px] text-text-tertiary">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Notifications + Panel toggle */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" className="relative h-8 w-8">
          <Bell className="h-4 w-4 text-text-secondary" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-danger" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onPanelToggle}
        >
          {onPanelToggle ? (
            <PanelRightClose className="h-4 w-4 text-text-secondary" />
          ) : (
            <PanelRightOpen className="h-4 w-4 text-text-secondary" />
          )}
        </Button>
      </div>

      {/* Search overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
          <div className="fixed inset-0 bg-black/40" onClick={close} />
          <div className="relative z-50 w-full max-w-lg rounded-card border border-border bg-elevated shadow-lg animate-fade-in">
            <div className="flex items-center gap-2 border-b border-border px-4">
              <Search className="h-5 w-5 text-text-tertiary" />
              <input
                autoFocus
                placeholder="Search candidates, jobs, conversations…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-transparent py-3 text-sm text-text-primary placeholder-text-tertiary outline-none"
              />
              <kbd className="rounded-button border border-border bg-surface px-2 py-1 text-xs text-text-tertiary">
                ESC
              </kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2 text-sm text-text-secondary">
              <div className="px-3 py-2 text-xs font-medium text-text-tertiary uppercase tracking-wider">
                Quick Results
              </div>
              <div className="px-3 py-1.5 rounded-button hover:bg-hover cursor-pointer text-text-primary">
                No results for &quot;{query || "your search"}&quot;
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
