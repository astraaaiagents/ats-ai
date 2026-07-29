/* ── Analytics View Page ────────────────────────────────────────────

   Redirects to /?tab=analytics for backward compatibility.
*/

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AnalyticsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/?tab=analytics");
  }, [router]);

  return null;
}
