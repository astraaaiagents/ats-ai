/* ── Conversation Hooks ─────────────────────────────────────────────

   Hooks for managing conversation list and creation.
   Uses localStorage for persistence (Phase 1).
   Can be swapped for API calls when backend adds GET /agent/conversations.
*/

import { useCallback } from "react";
import { useConversations, type StoredConversation } from "@/lib/store/conversations";

/**
 * Generate a short title from the first user message.
 */
function titleFromMessage(message: string): string {
  const cleaned = message.trim().replace(/\n+/g, " ");
  return cleaned.length > 50 ? cleaned.slice(0, 50) + "…" : cleaned || "New conversation";
}

/**
 * Hook to manage the conversation list.
 */
export function useConversationManager() {
  const {
    conversations,
    activeConversationId,
    addConversation,
    updateConversation,
    deleteConversation,
    setActiveConversation,
  } = useConversations();

  /**
   * Create a new conversation and add it to the list.
   */
  const createConversation = useCallback(
    (message?: string, sessionId?: string | null) => {
      const id = `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      const conv: StoredConversation = {
        id,
        title: message ? titleFromMessage(message) : "New conversation",
        preview: message?.slice(0, 80) || "",
        lastMessageAt: new Date().toISOString(),
        messageCount: 0,
        sessionId: sessionId ?? null,
      };
      addConversation(conv);
      return conv;
    },
    [addConversation]
  );

  /**
   * Update a conversation with a new message.
   */
  const appendMessage = useCallback(
    (id: string, message: string, role: "user" | "agent") => {
      const isUser = role === "user";
      updateConversation(id, {
        preview: isUser ? message.slice(0, 80) : (conversations.find((c) => c.id === id)?.preview || ""),
        lastMessageAt: new Date().toISOString(),
        messageCount: (conversations.find((c) => c.id === id)?.messageCount || 0) + 1,
      });
    },
    [conversations, updateConversation]
  );

  /**
   * Set the active conversation.
   */
  const selectConversation = useCallback(
    (id: string | null) => {
      setActiveConversation(id);
    },
    [setActiveConversation]
  );

  /**
   * Delete a conversation.
   */
  const removeConversation = useCallback(
    (id: string) => {
      deleteConversation(id);
    },
    [deleteConversation]
  );

  return {
    conversations,
    activeConversationId,
    createConversation,
    appendMessage,
    selectConversation,
    removeConversation,
  };
}

/**
 * Get the conversation list (for direct access without manager).
 */
export function useConversationsList() {
  return useConversations((state) => state.conversations);
}

/**
 * Get the active conversation ID.
 */
export function useActiveConversationId() {
  return useConversations((state) => state.activeConversationId);
}
