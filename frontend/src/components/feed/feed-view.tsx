/* ── FeedView ───────────────────────────────────────────────────────

   Reverse-chronological timeline, grouped by date.
   Merges data from action log, proactive alerts, and conversation history.
*/

"use client";

import { useMemo } from "react";
import { DateGroup } from "./date-group";
import { FeedBadge } from "./feed-badge";
import { FeedActions } from "./feed-actions";
import { EmptyState } from "@/components/shared/empty-state";
import { SkeletonFeedItem } from "@/components/shared/skeleton";
import { useActionLog, useProactiveAlerts } from "@/lib/api/hooks";
import type { FeedItemType } from "@/lib/api/types";

interface FeedItem {
  id: string;
  type: FeedItemType;
  content: string;
  badge?: string;
  created_at: string;
}

export function FeedView() {
  const { data: actionLogData, isLoading: loadingActions } = useActionLog({
    limit: 50,
  });
  const { data: alertsData, isLoading: loadingAlerts } = useProactiveAlerts({
    limit: 20,
  });

  const isLoading = loadingActions || loadingAlerts;

  // Merge action log entries and proactive alerts into unified feed items
  const feedItems = useMemo<FeedItem[]>(() => {
    const items: FeedItem[] = [];

    // Action log entries
    if (actionLogData?.data) {
      for (const entry of actionLogData.data) {
        const rawOutput = entry.output_pseudonymized || entry.input_pseudonymized || `${entry.agent_name}: ${entry.action_type}`;
        // Parse JSON content (from SSE events stored in action log) into readable text
        let displayContent = rawOutput;
        try {
          const parsed = JSON.parse(rawOutput);
          if (typeof parsed === "object") {
            // Extract the meaningful text from SSE-style JSON objects
            if (parsed.content) {
              displayContent = parsed.content;
            } else if (parsed.status) {
              displayContent = `Agent ${parsed.status}`;
            } else {
              // Fallback: join all values as "key: value"
              displayContent = Object.entries(parsed)
                .map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
                .join(" · ");
            }
          }
        } catch {
          // Not JSON — use as-is
        }
        items.push({
          id: `action-${entry.id}`,
          type: "agent",
          content: displayContent,
          badge: entry.action_type.toUpperCase(),
          created_at: entry.created_at,
        });
      }
    }

    // Proactive alerts
    if (alertsData?.alerts) {
      for (const alert of alertsData.alerts) {
        items.push({
          id: `alert-${alert.id}`,
          type: "alert",
          content: alert.body || alert.title,
          badge: alert.alert_type.replace(/_/g, " ").toUpperCase(),
          created_at: alert.created_at,
        });
      }
    }

    // Sort by created_at descending
    items.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    return items;
  }, [actionLogData, alertsData]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonFeedItem key={i} />
        ))}
      </div>
    );
  }

  if (feedItems.length === 0) {
    return (
      <EmptyState
        title="No activity yet"
        description="Your agent will start suggesting candidates soon."
      />
    );
  }

  // Group by date (UTC-based to avoid SSR/CSR timezone mismatch)
  const grouped = new Map<string, FeedItem[]>();
  for (const item of feedItems) {
    const date = new Date(item.created_at);
    // Use UTC date components for consistent grouping across SSR/CSR
    const utcYear = date.getUTCFullYear();
    const utcMonth = date.getUTCMonth();
    const utcDay = date.getUTCDate();

    const today = new Date();
    const yesterday = new Date();
    yesterday.setUTCDate(today.getUTCDate() - 1);

    const todayKey = `${today.getUTCFullYear()}-${today.getUTCMonth()}-${today.getUTCDate()}`;
    const yesterdayKey = `${yesterday.getUTCFullYear()}-${yesterday.getUTCMonth()}-${yesterday.getUTCDate()}`;
    const dateKey = `${utcYear}-${utcMonth}-${utcDay}`;

    let label: string;
    if (dateKey === todayKey) {
      label = "Today";
    } else if (dateKey === yesterdayKey) {
      label = "Yesterday";
    } else {
      // Use toISOString for consistent UTC-based date string
      label = date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        timeZone: "UTC",
      });
    }

    if (!grouped.has(label)) grouped.set(label, []);
    grouped.get(label)!.push(item);
  }

  return (
    <div className="space-y-6">
      {Array.from(grouped.entries()).map(([label, items]) => (
        <DateGroup key={label} label={label}>
          {items.map((item) => (
            <FeedItemCard key={item.id} item={item} />
          ))}
        </DateGroup>
      ))}
    </div>
  );
}

function FeedItemCard({ item }: { item: FeedItem }) {
  const borderColor = {
    agent: "border-primary",
    user: "border-success",
    system: "border-ai",
    alert: "border-danger",
  }[item.type];

  return (
    <div className={`rounded-card border border-border bg-card border-l-4 ${borderColor} p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            {item.badge && <FeedBadge badge={item.badge} />}
            <span className="text-[11px] text-text-tertiary">
              {new Date(item.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                timeZone: "UTC",
              })}
            </span>
          </div>
          <p className="text-sm text-text-primary">{item.content}</p>
        </div>
        <FeedActions type={item.type} />
      </div>
    </div>
  );
}
