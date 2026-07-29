/* ── Feed View Page ─────────────────────────────────────────────────

   Redirects to /?tab=feed for backward compatibility.
*/

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function FeedPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/?tab=feed");
  }, [router]);

  return null;
}
