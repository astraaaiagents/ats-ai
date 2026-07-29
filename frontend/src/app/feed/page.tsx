/* ── Feed View Page ─────────────────────────────────────────────────

   Default route. Shows the activity feed.
*/

"use client";

import { AppShell } from "@/components/layout/app-shell";
import { FeedView } from "@/components/feed/feed-view";

export default function FeedPage() {
  return (
    <AppShell defaultTab="feed">
      <FeedView />
    </AppShell>
  );
}
