/* ── Preferences View Page ──────────────────────────────────────────

   Redirects to /?tab=preferences for backward compatibility.
*/

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function PreferencesPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/?tab=preferences");
  }, [router]);

  return null;
}
