/* ── Pipeline View Page ─────────────────────────────────────────────

   Redirects to /?tab=pipeline for backward compatibility.
*/

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function PipelinePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/?tab=pipeline");
  }, [router]);

  return null;
}
