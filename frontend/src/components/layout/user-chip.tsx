/* ── UserChip ───────────────────────────────────────────────────────

   Bottom user info chip in the sidebar.
*/

"use client";

import { useAuth } from "@/lib/auth/context";

export function UserChip() {
  const { user } = useAuth();

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : "U";

  return (
    <div className="flex items-center gap-2.5 border-t border-border px-3 py-2.5">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-indigo-500 to-purple-500 text-xs font-semibold text-white">
        {initials}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-xs font-medium text-text-primary">
          {user?.email?.split("@")[0] || "User"}
        </div>
        <div className="truncate text-[10px] text-text-tertiary">
          {user?.email || "Not signed in"}
        </div>
      </div>
    </div>
  );
}
