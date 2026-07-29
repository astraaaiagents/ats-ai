/* ── CompactChat ────────────────────────────────────────────────────

   340px default width. Message thread, input bar, quick action chips.
   Streams agent responses via SSE.
*/

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useCommandPanel } from "@/lib/store/ui";
import { MessageThread } from "./message-thread";
import { InputBar } from "./input-bar";
import { QuickActionChips } from "./quick-action-chips";
import { sendConversation } from "@/lib/api/hooks";
import type { SSEEvent, SSEContent, SSECard, SSEAction } from "@/lib/api/types";
import type { ChatMessage, ChatCard, ChatAction } from "./command-message";

export function CompactChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { setMode } = useCommandPanel();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    try {
      let agentContent = "";
      const cards: ChatCard[] = [];
      const actions: ChatAction[] = [];
      const streamingMsgId = (Date.now() + 1).toString();
      const agentMsgPlaceholder: ChatMessage = {
        id: streamingMsgId,
        role: "agent",
        content: "",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, agentMsgPlaceholder]);

      await sendConversation(text, sessionId, (event: SSEEvent & { sse_type?: string }) => {
        const et = (event as any).sse_type;
        if (et === "content") {
          agentContent += (event as any).content || "";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingMsgId ? { ...m, content: agentContent } : m
            )
          );
        } else if (et === "card") {
          const cardData = (event as any).data as ChatCard | undefined;
          if (cardData) {
            cards.push(cardData);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamingMsgId ? { ...m, cards: [...(m.cards || []), cardData] } : m
              )
            );
          }
        } else if (et === "action") {
          const actionPayload = (event as any).payload as ChatAction | undefined;
          if (actionPayload) {
            actions.push(actionPayload);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamingMsgId ? { ...m, actions: [...(m.actions || []), actionPayload] } : m
              )
            );
          }
        } else if (et === "message_start" && (event as any).session_id) {
          setSessionId((event as any).session_id);
        }
      });
    } catch (error) {
      console.error("SSE conversation error:", error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content: "AI temporarily unavailable — please use manual search.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsStreaming(false);
    }
  }, [isStreaming, sessionId]);

  const handleQuickAction = (action: string) => {
    handleSend(action);
  };

  const handleMessageAction = (actionId: string, payload: unknown) => {
    let text = actionId;
    const p = payload as { candidate_id?: string; action?: string } | undefined;
    if (p?.candidate_id) {
      const type = actionId.split('_')[0];
      text = `${type} candidate ${p.candidate_id}`;
    } else if (p?.action) {
      text = p.action;
    }
    handleSend(text);
  };

  return (
    <div className="flex h-full flex-col w-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <span className="text-xs font-semibold text-text-primary">Command Panel</span>
        <button
          onClick={() => setMode("closed")}
          className="text-text-tertiary hover:text-text-secondary"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <MessageThread messages={messages} isStreaming={isStreaming} onAction={handleMessageAction} />

      {/* Quick Actions */}
      <QuickActionChips onAction={handleQuickAction} />

      {/* Input */}
      <div className="border-t border-border bg-surface">
        <InputBar onSend={handleSend} disabled={isStreaming} />
        <div className="px-4 pb-2 text-center">
          <p className="text-[9px] text-text-tertiary leading-tight">
            AI responses may be inaccurate. This is an automated AI assistant. Please verify critical information.
          </p>
        </div>
      </div>
    </div>
  );
}
