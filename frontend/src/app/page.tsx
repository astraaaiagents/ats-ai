/* ── Home Page ──────────────────────────────────────────────────────

   Parses ?tab= from URL and renders AppLayout.
   Redirects to /login if not authenticated.
*/

"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth/context";
import { AppLayout } from "@/components/layout/app-layout";
import type { ActiveTab } from "@/lib/store/conversations";

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();

  const tabParam = searchParams.get("tab") as ActiveTab | null;
  const validTabs: ActiveTab[] = ["feed", "pipeline", "jobs", "preferences", "analytics"];
  const defaultTab: ActiveTab = tabParam && validTabs.includes(tabParam) ? tabParam : "feed";

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) return null;

  return <AppLayout defaultTab={defaultTab} />;
}

export default function HomePage() {
  return (
    <Suspense fallback={null}>
      <HomeContent />
    </Suspense>
  );
}
