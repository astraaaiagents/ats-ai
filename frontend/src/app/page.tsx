/* ── Home Page (FeedView default) ───────────────────────────────────

   Redirects to /feed if authenticated, or /login if not.
*/

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/context";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (isAuthenticated) {
      router.replace("/feed");
    } else {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return null;
}
