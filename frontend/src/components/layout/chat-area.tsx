/* ── ChatArea ───────────────────────────────────────────────────────

   Center area. Dynamic content based on activeTab:
   - Conversations: CompactChat for conversation management
   - Feeds: FeedView
   - Pipeline: PipelineView
   - Jobs: JobsView
   - Preferences: PreferencesView
*/

"use client";

import { useConversations } from "@/lib/store/conversations";
import { useConversationManager } from "@/lib/api/hooks/conversations";
import { CompactChat } from "@/components/command-panel/compact-chat";
import { FeedView } from "@/components/feed/feed-view";
import { PipelineView } from "@/components/pipeline/pipeline-view";
import { JobsView } from "@/components/jobs/jobs-view";
import { PreferencesView } from "@/components/preferences/preferences-view";

export function ChatArea() {
  const { activeTab } = useConversations();
  const { conversations, activeConversationId } = useConversationManager();

  const activeConv = conversations.find((c) => c.id === activeConversationId);

  // Determine what to show in the center area
  const showChat = activeTab === "feed" && activeConversationId !== null;
  const showFeed = activeTab === "feed" && !activeConversationId;
  const showPipeline = activeTab === "pipeline";
  const showJobs = activeTab === "jobs";
  const showPreferences = activeTab === "preferences";

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <div className="flex items-center gap-2">
          {showChat ? (
            <>
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-ai/10 text-xs font-semibold text-ai">
                AI
              </div>
              <span className="text-sm font-semibold text-text-primary">
                {activeConv?.title || "Agent Console"}
              </span>
            </>
          ) : (
            <>
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">
                {activeTab === "feed" && "📡"}
                {activeTab === "pipeline" && "🔄"}
                {activeTab === "jobs" && "💼"}
                {activeTab === "preferences" && "⚙️"}
              </div>
              <span className="text-sm font-semibold text-text-primary">
                {activeTab === "feed" && "Feeds"}
                {activeTab === "pipeline" && "Pipeline"}
                {activeTab === "jobs" && "Jobs"}
                {activeTab === "preferences" && "Preferences"}
              </span>
            </>
          )}
        </div>
        {showChat && (
          <div className="flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-semibold text-primary">
            <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
            Agent Active
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1">
        {showChat && <CompactChat />}
        {showFeed && <FeedView />}
        {showPipeline && <PipelineView />}
        {showJobs && <JobsView />}
        {showPreferences && <PreferencesView />}
      </div>
    </div>
  );
}
