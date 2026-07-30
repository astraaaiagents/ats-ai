/* ── ChatArea ───────────────────────────────────────────────────────

   Center area. Dynamic content based on activeTab:
   - Conversations: CompactChat or Conversation Hub
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

function ConversationsHub() {
  const { conversations, createConversation, selectConversation } = useConversationManager();

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto p-6 bg-surface">
      <div className="mx-auto max-w-3xl w-full">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border pb-4 mb-6">
          <div>
            <h2 className="text-xl font-bold text-text-primary">Conversations</h2>
            <p className="text-xs text-text-secondary mt-1">
              Manage your AI agent interactions and past recruiter sessions
            </p>
          </div>
          <button
            onClick={() => {
              const conv = createConversation();
              selectConversation(conv.id);
            }}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-hover shadow-sm"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Conversation
          </button>
        </div>

        {/* Quick Starters */}
        <div className="mb-8">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary mb-3">
            Start a new task with AI
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              {
                title: "Source Candidates",
                prompt: "Source top 5 Java engineers with AWS experience",
                icon: "🎯",
              },
              {
                title: "Pipeline Review",
                prompt: "Review candidate fit scores for open positions",
                icon: "📊",
              },
              {
                title: "Draft Outreach",
                prompt: "Draft personalized outreach emails for top candidates",
                icon: "✉️",
              },
            ].map((starter, i) => (
              <button
                key={i}
                onClick={() => {
                  const conv = createConversation(starter.prompt);
                  selectConversation(conv.id);
                }}
                className="flex flex-col items-start p-3.5 rounded-card border border-border bg-surface-elevated hover:border-primary/50 hover:bg-primary/5 text-left transition group"
              >
                <span className="text-xl mb-2">{starter.icon}</span>
                <span className="text-xs font-bold text-text-primary group-hover:text-primary">
                  {starter.title}
                </span>
                <span className="text-[11px] text-text-tertiary mt-1 leading-relaxed">
                  &ldquo;{starter.prompt}&rdquo;
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Recent Conversations */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary mb-3">
            Recent Conversations ({conversations.length})
          </h3>
          {conversations.length === 0 ? (
            <div className="rounded-card border border-dashed border-border p-8 text-center bg-surface-elevated">
              <p className="text-sm font-medium text-text-secondary">No conversation history yet</p>
              <p className="text-xs text-text-tertiary mt-1 mb-4">
                Start a new conversation to begin chatting with your recruiter agent.
              </p>
              <button
                onClick={() => {
                  const conv = createConversation();
                  selectConversation(conv.id);
                }}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-white transition hover:bg-primary-hover"
              >
                Start First Conversation
              </button>
            </div>
          ) : (
            <div className="divide-y divide-border rounded-card border border-border bg-surface-elevated overflow-hidden">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className="flex items-center justify-between p-3.5 hover:bg-hover cursor-pointer transition"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1 pr-4">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary text-sm font-semibold">
                      💬
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-text-primary truncate">
                        {conv.title || "New conversation"}
                      </p>
                      <p className="text-[11px] text-text-tertiary truncate mt-0.5">
                        {conv.preview || "No messages yet"}
                      </p>
                    </div>
                  </div>
                  <div className="text-[10px] text-text-tertiary shrink-0">
                    {new Date(conv.lastMessageAt).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChatArea() {
  const { activeTab } = useConversations();
  const { conversations, activeConversationId } = useConversationManager();

  const activeConv = conversations.find((c) => c.id === activeConversationId);

  const isConversationsTab = activeTab === "conversations";
  const showChat = (isConversationsTab || activeTab === "feed") && activeConversationId !== null;
  const showConversationsHub = isConversationsTab && activeConversationId === null;
  const showFeed = activeTab === "feed" && activeConversationId === null;
  const showPipeline = activeTab === "pipeline";
  const showJobs = activeTab === "jobs";
  const showPreferences = activeTab === "preferences";

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5 bg-surface">
        <div className="flex items-center gap-2">
          {showChat ? (
            <>
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-ai/10 text-xs font-semibold text-ai">
                💬
              </div>
              <span className="text-sm font-semibold text-text-primary">
                {activeConv?.title || "Agent Console"}
              </span>
            </>
          ) : (
            <>
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">
                {isConversationsTab && "💬"}
                {activeTab === "feed" && "📡"}
                {activeTab === "pipeline" && "🔄"}
                {activeTab === "jobs" && "💼"}
                {activeTab === "preferences" && "⚙️"}
              </div>
              <span className="text-sm font-semibold text-text-primary">
                {isConversationsTab && "Conversations"}
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
      <div className="flex-1 overflow-hidden relative">
        {showChat && <CompactChat />}
        {showConversationsHub && <ConversationsHub />}
        {showFeed && <FeedView />}
        {showPipeline && <PipelineView />}
        {showJobs && <JobsView />}
        {showPreferences && <PreferencesView />}
      </div>
    </div>
  );
}
