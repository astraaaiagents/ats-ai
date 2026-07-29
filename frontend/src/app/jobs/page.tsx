/* ── Jobs View Page ─────────────────────────────────────────────────

   Redirects to /?tab=jobs for backward compatibility.
*/

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function JobsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/?tab=jobs");
  }, [router]);

  return null;
}
