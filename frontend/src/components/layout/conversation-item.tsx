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
  onDelete?: () => void;
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

export function ConversationItem({ conversation, isActive, onClick, onDelete }: ConversationItemProps) {
  return (
    <div
      className={cn(
        "group relative flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors cursor-pointer",
        isActive
          ? "bg-primary/10 text-text-primary font-medium"
          : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* Icon */}
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold mt-0.5",
          isActive ? "bg-primary/20 text-primary" : "bg-surface-elevated text-text-tertiary"
        )}
      >
        {conversation.title?.[0]?.toUpperCase() || "💬"}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="truncate text-xs font-medium leading-snug">
          {conversation.title || "New conversation"}
        </div>
        <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-text-tertiary">
          <span className="truncate flex-1">{conversation.preview || "No messages yet"}</span>
          <span className="shrink-0">{timeAgo(conversation.lastMessageAt)}</span>
        </div>
      </div>

      {/* Actions / Status */}
      <div className="flex shrink-0 items-center gap-1">
        {onDelete && (
          <button
            type="button"
            className="opacity-0 group-hover:opacity-100 rounded p-1 text-text-tertiary hover:bg-danger/10 hover:text-danger transition-all"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            aria-label="Delete conversation"
            title="Delete conversation"
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        )}
        {isActive && (
          <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
        )}
      </div>
    </div>
  );
}
