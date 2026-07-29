/* ── Domain-specific API hooks ───────────────────────────────────────

   React Query hooks for all agent portal endpoints:
   - useConversation() — POST /agent/conversation, SSE stream
   - useConversationHistory(sessionId) — GET /agent/conversation/{sessionId}
   - usePreferences() — GET /agent/preferences
   - useUpdatePreferences() — PUT /agent/preferences
   - useProactiveAlerts() — GET /agent/proactive/alerts
   - useActionLog() — GET /agent/action-log
   - useCandidates() — GET /candidates with filters
   - useClientContacts() — GET /client-contacts
*/

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./client";
import type {
  AgentMessageResponse,
  ConversationHistoryResponse,
  ConversationRequest,
  PreferenceResponse,
  PreferenceUpdate,
  ProactiveAlertResponse,
  ProactiveAlertsResponse,
  ActionLogEntry,
  CandidateResponse,
  PaginatedResponse,
  SSEEvent,
} from "./types";
import { readSSEStream } from "./sse";

/* ── Constants ─────────────────────────────────────────────────────── */

const QUERY_KEYS = {
  conversationHistory: (sessionId: string) => ["conversation", sessionId],
  preferences: ["preferences"] as const,
  proactiveAlerts: ["proactiveAlerts"] as const,
  actionLog: ["actionLog"] as const,
  candidates: ["candidates"] as const,
  clientContacts: ["clientContacts"] as const,
} as const;

/* ── Conversation (SSE streaming) ──────────────────────────────────── */

/**
 * Send a message to the agent and consume the SSE stream.
 * Returns all parsed SSE events from the stream.
 */
export async function sendConversation(
  message: string,
  sessionId?: string | null,
  onToken?: (event: SSEEvent) => void,
): Promise<SSEEvent[]> {
  const events: SSEEvent[] = [];

  for await (const event of readSSEStream("/agent/conversation", {
    message,
    session_id: sessionId,
  } as ConversationRequest, () => {
    const token = localStorage.getItem("access_token");
    return token || "";
  })) {
    events.push(event);
    onToken?.(event);
  }

  return events;
}

/**
 * React Query hook for sending conversation messages.
 * Returns a mutation with the SSE streaming capability.
 */
export function useConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      message,
      sessionId,
    }: {
      message: string;
      sessionId?: string | null;
    }) => {
      return sendConversation(message, sessionId);
    },
    onSuccess: (_data, variables) => {
      // Invalidate conversation history when a new message is sent
      if (variables.sessionId) {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.conversationHistory(variables.sessionId!),
        });
      }
    },
  });
}

/* ── Conversation History ──────────────────────────────────────────── */

export function useConversationHistory(sessionId: string | null) {
  return useQuery({
    queryKey: QUERY_KEYS.conversationHistory(sessionId || ""),
    queryFn: async () => {
      if (!sessionId) return null;
      return api.get<ConversationHistoryResponse>(
        `/agent/conversation/${sessionId}`,
      );
    },
    enabled: !!sessionId,
    staleTime: 30_000,
  });
}

/* ── Preferences ───────────────────────────────────────────────────── */

export function usePreferences() {
  return useQuery({
    queryKey: QUERY_KEYS.preferences,
    queryFn: () => api.get<PreferenceResponse>("/agent/preferences"),
    staleTime: 60_000,
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (updates: Record<string, unknown>) =>
      api.put<PreferenceResponse>("/agent/preferences", {
        explicit: updates,
      } as PreferenceUpdate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.preferences });
    },
  });
}

/* ── Proactive Alerts ──────────────────────────────────────────────── */

export function useProactiveAlerts(opts?: {
  unreadOnly?: boolean;
  limit?: number;
}) {
  const params = new URLSearchParams();
  if (opts?.unreadOnly) params.set("unread_only", "true");
  if (opts?.limit) params.set("limit", String(opts.limit));

  return useQuery({
    queryKey: [...QUERY_KEYS.proactiveAlerts, opts],
    queryFn: () =>
      api.get<ProactiveAlertsResponse>(
        `/agent/proactive/alerts?${params.toString()}`,
      ),
    staleTime: 30_000,
  });
}

/* ── Action Log ────────────────────────────────────────────────────── */

export function useActionLog(opts?: {
  startDate?: string;
  endDate?: string;
  actionType?: string;
  limit?: number;
  offset?: number;
}) {
  const params = new URLSearchParams();
  if (opts?.startDate) params.set("start_date", opts.startDate);
  if (opts?.endDate) params.set("end_date", opts.endDate);
  if (opts?.actionType) params.set("action_type", opts.actionType);
  if (opts?.limit) params.set("limit", String(opts.limit));
  if (opts?.offset) params.set("offset", String(opts.offset));

  return useQuery({
    queryKey: [...QUERY_KEYS.actionLog, opts],
    queryFn: async () => {
      const data = await api.get<Record<string, unknown>>(
        `/agent/action-log?${params.toString()}`,
      );
      return {
        data: (data as any).data ?? (data as any).results ?? [],
        total: (data as any).total ?? 0,
      } as { data: ActionLogEntry[]; total: number };
    },
    staleTime: 60_000,
  });
}

/* ── Candidates ────────────────────────────────────────────────────── */

export function useCandidates(opts?: {
  status?: string;
  search?: string;
  orgId?: string;
  limit?: number;
  offset?: number;
}) {
  const params = new URLSearchParams();
  if (opts?.status) params.set("status", opts.status);
  if (opts?.search) params.set("search", opts.search);
  if (opts?.orgId) params.set("org_id", opts.orgId);
  if (opts?.limit) params.set("limit", String(opts.limit));
  if (opts?.offset) params.set("offset", String(opts.offset));

  return useQuery({
    queryKey: [...QUERY_KEYS.candidates, opts],
    queryFn: async () => {
      const data = await api.get<PaginatedResponse<CandidateResponse>>(
        `/candidates?${params.toString()}`,
      );
      return data;
    },
    staleTime: 60_000,
  });
}

export function useCandidate(id: string | null) {
  return useQuery({
    queryKey: [...QUERY_KEYS.candidates, "detail", id],
    queryFn: async () => {
      const data = await api.get<CandidateResponse>(`/candidates/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

/* ── Client Contacts (Jobs) ────────────────────────────────────────── */

export function useClientContacts(opts?: {
  orgId?: string;
  status?: string;
}) {
  const params = new URLSearchParams();
  if (opts?.orgId) params.set("org_id", opts.orgId);
  if (opts?.status) params.set("status", opts.status);

  return useQuery({
    queryKey: [...QUERY_KEYS.clientContacts, opts],
    queryFn: async () => {
      return api.get<Array<Record<string, unknown>>>(
        `/client-contacts?${params.toString()}`,
      );
    },
    staleTime: 120_000,
  });
}
