/* ── Conversations Zustand Store ─────────────────────────────────────

   Manages conversation list, active conversation, and sidebar state
   for the two-panel layout (sidebar + chat).
*/

import { create } from "zustand";

export type ActiveTab = "conversations" | "feed" | "pipeline" | "jobs" | "preferences" | "analytics";

export interface StoredConversation {
  id: string;
  title: string | null;
  preview: string;
  lastMessageAt: string;
  messageCount: number;
  sessionId: string | null;
}

interface ConversationsState {
  conversations: StoredConversation[];
  activeConversationId: string | null;
  activeTab: ActiveTab;
  isSidebarOpen: boolean;
  isConversationsExpanded: boolean;
  setConversations: (conversations: StoredConversation[]) => void;
  addConversation: (conv: StoredConversation) => void;
  updateConversation: (id: string, updates: Partial<StoredConversation>) => void;
  deleteConversation: (id: string) => void;
  setActiveConversation: (id: string | null) => void;
  getActiveConversation: () => StoredConversation | undefined;
  setActiveTab: (tab: ActiveTab) => void;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  openSidebar: () => void;
  toggleConversationsExpanded: () => void;
  setConversationsExpanded: (expanded: boolean) => void;
}

const STORAGE_KEY = "ats_conversations";

function loadConversations(): StoredConversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveConversations(conversations: StoredConversation[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, 50)));
  } catch {
    // Storage full — ignore
  }
}

export const useConversations = create<ConversationsState>((set, get) => ({
  conversations: loadConversations(),
  activeConversationId: null,
  activeTab: "feed",
  isSidebarOpen: true,
  isConversationsExpanded: true,

  setConversations: (conversations) => {
    set({ conversations });
    saveConversations(conversations);
  },

  addConversation: (conv) => {
    set((state) => {
      const next = [conv, ...state.conversations].slice(0, 50);
      saveConversations(next);
      return {
        conversations: next,
        activeConversationId: conv.id,
        isConversationsExpanded: true,
        activeTab: "conversations",
      };
    });
  },

  updateConversation: (id, updates) => {
    set((state) => {
      const next = state.conversations.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      );
      saveConversations(next);
      return { conversations: next };
    });
  },

  deleteConversation: (id) => {
    set((state) => {
      const next = state.conversations.filter((c) => c.id !== id);
      saveConversations(next);
      return {
        conversations: next,
        activeConversationId:
          state.activeConversationId === id ? null : state.activeConversationId,
      };
    });
  },

  setActiveConversation: (id) =>
    set((state) => ({
      activeConversationId: id,
      isConversationsExpanded: id !== null ? true : state.isConversationsExpanded,
      activeTab: id !== null ? "conversations" : state.activeTab,
    })),

  getActiveConversation: () => {
    const { conversations, activeConversationId } = get();
    return conversations.find((c) => c.id === activeConversationId);
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  closeSidebar: () => set({ isSidebarOpen: false }),
  openSidebar: () => set({ isSidebarOpen: true }),

  toggleConversationsExpanded: () =>
    set((state) => ({ isConversationsExpanded: !state.isConversationsExpanded })),
  setConversationsExpanded: (expanded) => set({ isConversationsExpanded: expanded }),
}));
