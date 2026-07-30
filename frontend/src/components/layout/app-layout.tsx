/* ── AppLayout ──────────────────────────────────────────────────────

   Two-panel layout with collapsible sidebar:
   1. Left sidebar: Conversations, Feeds, Pipeline, Jobs, Preferences
   2. Center: Chat area (expands when sidebar is collapsed)
*/

"use client";

import { useEffect } from "react";
import { useConversations, type ActiveTab } from "@/lib/store/conversations";
import { MainSidebar } from "./conversation-sidebar";
import { ChatArea } from "./chat-area";

interface AppLayoutProps {
  defaultTab?: ActiveTab;
}

export function AppLayout({ defaultTab = "feed" }: AppLayoutProps) {
  const { activeTab, setActiveTab, isSidebarOpen, toggleSidebar } = useConversations();

  // Set default tab on mount if provided
  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab, setActiveTab]);

  // Update URL when active tab changes
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("tab") !== activeTab) {
      params.set("tab", activeTab);
      const newUrl = `${window.location.pathname}?${params.toString()}`;
      window.history.replaceState({}, "", newUrl);
    }
  }, [activeTab]);

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Left Sidebar */}
      <MainSidebar />

      {/* Center Chat Area - fills remaining space */}
      <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Toggle Button */}
        <button
          onClick={toggleSidebar}
          className={`absolute top-1/2 z-20 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-white shadow-md transition-all hover:bg-gray-50 focus:outline-none ${
            isSidebarOpen ? "left-0 -translate-x-1/2" : "left-2"
          }`}
          aria-label={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isSidebarOpen ? (
            <svg className="h-4 w-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          ) : (
            <svg className="h-4 w-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          )}
        </button>

        <ChatArea />
      </div>
    </div>
  );
}
