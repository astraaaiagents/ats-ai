/* ── Zustand UI Store ───────────────────────────────────────────────

   Global UI state: active tab, command panel, search, notifications.
   Lightweight, no boilerplate.
*/

import { create } from "zustand";

export type ActiveTab = "conversations" | "feed" | "pipeline" | "jobs" | "preferences" | "analytics";

export type CommandPanelMode = "compact" | "expanded" | "compare" | "closed";

export interface CommandPanelState {
  mode: CommandPanelMode;
  expandedCandidateId: string | null;
  compareCandidates: string[];
  setMode: (mode: CommandPanelMode) => void;
  setExpandedCandidate: (id: string | null) => void;
  addCompareCandidate: (id: string) => void;
  removeCompareCandidate: (id: string) => void;
  clearCompare: () => void;
  closePanel: () => void;
}

export interface NotificationState {
  count: number;
  unreadIds: Set<string>;
  markRead: (id: string) => void;
  markAllRead: () => void;
  increment: () => void;
}

export interface SearchState {
  query: string;
  isOpen: boolean;
  setQuery: (q: string) => void;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

// ── Command Panel Store ─────────────────────────────────────────────

const useCommandPanel = create<CommandPanelState>((set) => ({
  mode: "compact",
  expandedCandidateId: null,
  compareCandidates: [],
  setMode: (mode) => set({ mode }),
  setExpandedCandidate: (id) => set({ expandedCandidateId: id, mode: id ? "expanded" : "compact" }),
  addCompareCandidate: (id) =>
    set((state) => ({
      compareCandidates: state.compareCandidates.includes(id)
        ? state.compareCandidates
        : [...state.compareCandidates, id].slice(0, 2),
      mode: state.compareCandidates.length >= 1 ? "compare" : "compact",
    })),
  removeCompareCandidate: (id) =>
    set((state) => {
      const next = state.compareCandidates.filter((c) => c !== id);
      return {
        compareCandidates: next,
        mode: next.length === 2 ? "compare" : "compact",
      };
    }),
  clearCompare: () => set({ compareCandidates: [], mode: "compact" }),
  closePanel: () => set({ mode: "closed" }),
}));

// ── Notifications Store ─────────────────────────────────────────────

const useNotifications = create<NotificationState>((set) => ({
  count: 0,
  unreadIds: new Set(),
  markRead: (id) =>
    set((state) => {
      const next = new Set(state.unreadIds);
      next.delete(id);
      return { count: Math.max(0, state.count - 1), unreadIds: next };
    }),
  markAllRead: () => set({ count: 0, unreadIds: new Set() }),
  increment: () => set((state) => ({ count: state.count + 1 })),
}));

// ── Search Store ────────────────────────────────────────────────────

const useSearch = create<SearchState>((set) => ({
  query: "",
  isOpen: false,
  setQuery: (q) => set({ query: q }),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, query: "" }),
  toggle: () => set((state) => ({ isOpen: !state.isOpen, query: state.isOpen ? "" : state.query })),
}));

export { useCommandPanel, useNotifications, useSearch };
