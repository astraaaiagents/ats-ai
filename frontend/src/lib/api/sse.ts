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
    if (line === "") {
      if (event && data) {
        events.push(parseEvent(event, data));
      }
      event = null;
      data = "";
    } else if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      data = line.slice(5).trim();
    }
  }

  // Handle last event without trailing blank line
  if (event && data) {
    events.push(parseEvent(event, data));
  }

  return events;
}

function parseEvent(type: string, data: string): SSEEvent {
  const parsed = JSON.parse(data);

  switch (type) {
    case "message_start":
      return parsed as SSEMessageStart;
    case "content":
      return parsed as SSEContent;
    case "card":
      return parsed as SSECard;
    case "action":
      return parsed as SSEAction;
    case "message_end":
      return parsed as SSEMessageEnd;
    default:
      return parsed as SSEEvent;
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
  const response = await fetch(`${API_BASE}${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${onToken()}`,
    },
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
