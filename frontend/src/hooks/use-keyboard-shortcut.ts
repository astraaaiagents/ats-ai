/* ── Keyboard Shortcut Hook ─────────────────────────────────────────

   Listen for key combinations and trigger callbacks.
   Uses Cmd+K for global search by default.
*/

import { useEffect } from "react";

export function useKeyboardShortcut(
  key: string,
  modifier: "metaKey" | "ctrlKey" | "altKey" | "shiftKey" = "metaKey",
  callback: () => void
) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === key && e[modifier] && !e.altKey) {
        e.preventDefault();
        callback();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [key, modifier, callback]);
}
