/* ── Auth Guard Hook ────────────────────────────────────────────────

   Redirect to /login if unauthenticated.
   Use in layout or page components to protect routes.
*/

"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth/context";

const PUBLIC_PATHS = ["/login"];

export function useAuthGuard() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated && !PUBLIC_PATHS.includes(pathname)) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, pathname, router]);
}
