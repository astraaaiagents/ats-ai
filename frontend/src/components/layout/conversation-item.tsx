/* ── ConversationItem ───────────────────────────────────────────────

   Individual item in the conversation sidebar list.
*/

"use client";

import { cn } from "@/lib/utils";
import type { StoredConversation } from "@/lib/store/conversations";

interface ConversationItemProps {
  conversation: StoredConversation;
  isActive: boolean;
  onClick: () => void;
}

function timeAgo(dateString: string): string {
  const now = Date.now();
  const date = new Date(dateString).getTime();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return new Date(dateString).toLocaleDateString();
}

export function ConversationItem({ conversation, isActive, onClick }: ConversationItemProps) {
  return (
    <button
      className={cn(
        "flex w-full items-start gap-2.5 rounded-lg px-3 py-2.5 text-left transition-colors",
        isActive
          ? "bg-primary/10 text-text-primary"
          : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
      )}
      onClick={onClick}
    >
      {/* Icon */}
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold",
          isActive ? "bg-primary/20 text-primary" : "bg-surface-elevated text-text-tertiary"
        )}
      >
        {conversation.title?.[0]?.toUpperCase() || "AI"}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="truncate text-xs font-medium">{conversation.title || "New conversation"}</div>
        <div className="mt-0.5 flex items-center gap-2">
          <span className="truncate text-[10px] text-text-tertiary">{conversation.preview || "No messages yet"}</span>
          <span className="shrink-0 text-[10px] text-text-tertiary">{timeAgo(conversation.lastMessageAt)}</span>
        </div>
      </div>

      {/* Unread dot */}
      {isActive && (
        <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
      )}
    </button>
  );
}
