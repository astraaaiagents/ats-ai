/* ── MessageThread ──────────────────────────────────────────────────

   Scrollable messages. SSE streaming accumulation.
*/

"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { CommandMessage } from "./command-message";

interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system";
  content: string;
  timestamp: string;
  cards?: Record<string, any>[];
  actions?: Record<string, any>[];
}

interface MessageThreadProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onAction?: (actionId: string, payload: any) => void;
}

export function MessageThread({ messages, isStreaming, onAction }: MessageThreadProps) {
  return (
    <ScrollArea className="flex-1">
      <div className="p-3 space-y-3">
        {messages.map((msg) => (
          <CommandMessage key={msg.id} message={msg} onAction={onAction} />
        ))}
        {isStreaming && (
          <div className="flex items-center gap-2 px-2 py-1">
            <div className="flex gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-subtle" style={{ animationDelay: "0ms" }} />
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-subtle" style={{ animationDelay: "150ms" }} />
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-subtle" style={{ animationDelay: "300ms" }} />
            </div>
            <span className="text-xs text-text-tertiary">AI is thinking…</span>
          </div>
        )}
        <div ref={(el) => el?.scrollIntoView({ behavior: "smooth" })} />
      </div>
    </ScrollArea>
  );
}
