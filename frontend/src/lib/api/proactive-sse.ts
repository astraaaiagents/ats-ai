/* ── Proactive SSE Listener ─────────────────────────────────────────

   Opens an SSE connection to receive real-time proactive alerts.
   Auto-reconnects on disconnect with exponential backoff.
*/

import type { ProactiveAlertResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type ProactiveAlertHandler = (alert: ProactiveAlertResponse) => void;

let sseConnection: EventSource | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let handlers: Set<ProactiveAlertHandler> = new Set();
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30_000; // Cap at 30s

/**
 * Start the SSE connection for proactive alerts.
 * Automatically reconnects on disconnect.
 */
export function startProactiveSSE(onAlert: ProactiveAlertHandler): void {
  handlers.add(onAlert);

  if (sseConnection) return; // Already connected

  connectSSE();
}

/**
 * Stop the SSE connection and remove the handler.
 */
export function stopProactiveSSE(onAlert?: ProactiveAlertHandler): void {
  if (onAlert) handlers.delete(onAlert);
  if (handlers.size === 0) {
    closeSSE();
  }
}

function connectSSE(): void {
  const token = localStorage.getItem("access_token");
  if (!token) {
    // No token — can't connect, retry later
    scheduleReconnect();
    return;
  }

  const url = `${API_BASE}/agent/sse/stream?token=${encodeURIComponent(token)}`;

  try {
    sseConnection = new EventSource(url);
  } catch {
    scheduleReconnect();
    return;
  }

  sseConnection.onopen = () => {
    reconnectAttempts = 0;
  };

  sseConnection.addEventListener("alert", (event: MessageEvent) => {
    try {
      const alert: ProactiveAlertResponse = JSON.parse(event.data);
      handlers.forEach((handler) => handler(alert));
    } catch (err) {
      console.error("Failed to parse SSE alert:", err);
    }
  });

  sseConnection.addEventListener("heartbeat", () => {
    // Heartbeat — connection is alive
  });

  sseConnection.onerror = () => {
    sseConnection?.close();
    sseConnection = null;
    scheduleReconnect();
  };
}

function scheduleReconnect(): void {
  if (reconnectTimeout) return;

  // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (capped)
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
  reconnectAttempts++;

  reconnectTimeout = setTimeout(() => {
    reconnectTimeout = null;
    connectSSE();
  }, delay);
}

function closeSSE(): void {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  sseConnection?.close();
  sseConnection = null;
  reconnectAttempts = 0;
}
