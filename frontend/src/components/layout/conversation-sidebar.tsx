/* ── MainSidebar ────────────────────────────────────────────────────

   Left sidebar with navigation:
   1. Conversations (with conversation list)
   2. Feeds (navigation only)
   3. Pipeline (navigation only)
   4. Jobs (navigation only)
   5. Preferences (navigation only)
*/

"use client";

import { useState } from "react";
import { useConversations, type ActiveTab } from "@/lib/store/conversations";
import { useConversationManager } from "@/lib/api/hooks/conversations";
import { ConversationItem } from "./conversation-item";
import { UserChip } from "./user-chip";
import { cn } from "@/lib/utils";

const SECTIONS = [
  { key: "conversations", label: "Conversations", icon: "💬" },
  { key: "feed", label: "Feeds", icon: "📡" },
  { key: "pipeline", label: "Pipeline", icon: "🔄" },
  { key: "jobs", label: "Jobs", icon: "💼" },
  { key: "preferences", label: "Preferences", icon: "⚙️" },
] as const;

type SectionKey = (typeof SECTIONS)[number]["key"];

export function MainSidebar() {
  const { activeTab, setActiveTab, isSidebarOpen, conversations, activeConversationId } = useConversations();
  const { createConversation, selectConversation } = useConversationManager();
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = searchQuery
    ? conversations.filter((c) =>
        (c.title || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.preview || "").toLowerCase().includes(searchQuery.toLowerCase())
      )
    : conversations;

  if (!isSidebarOpen) return null;

  const isSectionActive = (sectionKey: SectionKey) => {
    if (sectionKey === "conversations") return activeConversationId !== null;
    return activeTab === sectionKey;
  };

  const handleSectionClick = (sectionKey: SectionKey) => {
    if (sectionKey === "conversations") {
      setActiveTab("feed");
      selectConversation(null);
    } else {
      setActiveTab(sectionKey as ActiveTab);
      selectConversation(null);
    }
  };

  return (
    <aside className="flex h-full w-[280px] shrink-0 flex-col border-r border-border bg-surface">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 py-3.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-indigo-400 text-sm font-bold text-white">
          A
        </div>
        <span className="text-base font-semibold text-text-primary">
          Agency<span className="text-ai">OS</span>
        </span>
      </div>

      {/* New Conversation Button */}
      <button
        className="mx-3 mb-2 flex items-center justify-center gap-2 rounded-lg bg-primary py-2 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
        onClick={() => {
          const conv = createConversation();
          selectConversation(conv.id);
        }}
      >
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        New Conversation
      </button>

      {/* Search */}
      <div className="mx-3 mb-2">
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-tertiary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search conversations…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-full rounded-md border border-border bg-surface-elevated pl-8 pr-3 text-xs text-text-primary placeholder-text-tertiary outline-none transition focus:border-primary"
          />
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {/* Section: Conversations */}
        <div className="mb-2">
          <button
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
              isSectionActive("conversations") ? "bg-primary/10 text-text-primary" : "text-text-secondary hover:bg-surface-hover"
            )}
            onClick={() => handleSectionClick("conversations")}
          >
            <span className="text-sm">{SECTIONS[0].icon}</span>
            <span className="text-xs font-semibold">{SECTIONS[0].label}</span>
          </button>

          {/* Conversation List (only shown when Conversations section is active) */}
          {isSectionActive("conversations") && (
            <div className="mt-1 ml-6 space-y-0.5">
              {filtered.length === 0 ? (
                <div className="px-3 py-2 text-center text-[10px] text-text-tertiary">
                  {searchQuery ? "No conversations found" : "No conversations yet"}
                </div>
              ) : (
                filtered.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conversation={conv}
                    isActive={conv.id === activeConversationId}
                    onClick={() => selectConversation(conv.id)}
                  />
                ))
              )}
            </div>
          )}
        </div>

        {/* Section: Feeds */}
        <div className="mb-1">
          <button
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
              isSectionActive("feed") ? "bg-primary/10 text-text-primary" : "text-text-secondary hover:bg-surface-hover"
            )}
            onClick={() => handleSectionClick("feed")}
          >
            <span className="text-sm">{SECTIONS[1].icon}</span>
            <span className="text-xs font-semibold">{SECTIONS[1].label}</span>
          </button>
        </div>

        {/* Section: Pipeline */}
        <div className="mb-1">
          <button
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
              isSectionActive("pipeline") ? "bg-primary/10 text-text-primary" : "text-text-secondary hover:bg-surface-hover"
            )}
            onClick={() => handleSectionClick("pipeline")}
          >
            <span className="text-sm">{SECTIONS[2].icon}</span>
            <span className="text-xs font-semibold">{SECTIONS[2].label}</span>
          </button>
        </div>

        {/* Section: Jobs */}
        <div className="mb-1">
          <button
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
              isSectionActive("jobs") ? "bg-primary/10 text-text-primary" : "text-text-secondary hover:bg-surface-hover"
            )}
            onClick={() => handleSectionClick("jobs")}
          >
            <span className="text-sm">{SECTIONS[3].icon}</span>
            <span className="text-xs font-semibold">{SECTIONS[3].label}</span>
          </button>
        </div>

        {/* Section: Preferences */}
        <div className="mb-1">
          <button
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
              isSectionActive("preferences") ? "bg-primary/10 text-text-primary" : "text-text-secondary hover:bg-surface-hover"
            )}
            onClick={() => handleSectionClick("preferences")}
          >
            <span className="text-sm">{SECTIONS[4].icon}</span>
            <span className="text-xs font-semibold">{SECTIONS[4].label}</span>
          </button>
        </div>
      </div>

      {/* User Chip */}
      <UserChip />
    </aside>
  );
}
