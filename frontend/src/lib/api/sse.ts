/* ── SSE Module ─────────────────────────────────────────────────────

   Parse SSE events from the agent conversation stream.
   Event types: message_start, content, card, action, message_end
*/

import { API_BASE } from "./client";
import type {
  SSEEvent,
  SSEMessageStart,
  SSEContent,
  SSECard,
  SSEAction,
  SSEMessageEnd,
} from "./types";

export type {
  SSEEvent,
  SSEMessageStart,
  SSEContent,
  SSECard,
  SSEAction,
  SSEMessageEnd,
};

/**
 * Parse a raw SSE text chunk into structured events.
 * SSE format:
 *   event: <type>
 *   data: <JSON>
 *   <blank line>
 */
export function parseSSE(raw: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  const lines = raw.split("\n");
  let event: string | null = null;
  let data = "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed === "") {
      if (event && data) {
        events.push(parseEvent(event, data));
      }
      event = null;
      data = "";
    } else if (trimmed.startsWith("event:")) {
      event = trimmed.slice(6).trim();
    } else if (trimmed.startsWith("data:")) {
      data = trimmed.slice(5).trimStart();
    }
  }

  // Handle last event without trailing blank line
  if (event && data) {
    events.push(parseEvent(event, data));
  }

  return events;
}

function parseEvent(type: string, data: string): SSEEvent {
  try {
    const parsed = JSON.parse(data);

    // Preserve the SSE event type for frontend dispatch
    const sse_type = type;

    switch (type) {
      case "message_start":
        return { ...parsed, sse_type } as unknown as SSEEvent;
      case "content":
        return { ...parsed, sse_type } as unknown as SSEEvent;
      case "card":
        return { ...parsed, sse_type } as unknown as SSEEvent;
      case "action":
        return { ...parsed, sse_type } as unknown as SSEEvent;
      case "message_end":
        return { ...parsed, sse_type } as unknown as SSEEvent;
      default:
        return { ...parsed, sse_type } as unknown as SSEEvent;
    }
  } catch (err) {
    console.error("Failed to parse SSE event data:", err, data);
    return { type: "content", content: "", sse_type: type } as unknown as SSEEvent;
  }
}

/**
 * Read an SSE stream and yield parsed events.
 * Automatically handles auth header.
 */
export async function* readSSEStream(
  url: string,
  body: unknown,
  onToken: () => string
): AsyncGenerator<SSEEvent> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = onToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${url}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`SSE error: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete events from buffer
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const events = parseSSE(part);
        console.log("[SSE] parsed events from chunk:", events.length, events);
        for (const event of events) {
          yield event;
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim()) {
      const events = parseSSE(buffer);
      for (const event of events) {
        yield event;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
