/* ── KeyboardHint ───────────────────────────────────────────────────

   "← reject · → approve · space = details"
*/

"use client";

export function KeyboardHint() {
  return (
    <div className="flex items-center justify-center gap-4 mt-3 text-xs text-text-tertiary">
      <span>
        <kbd className="rounded-button border border-border bg-surface px-1.5 py-0.5 text-[10px]">←</kbd>{" "}
        reject
      </span>
      <span>
        <kbd className="rounded-button border border-border bg-surface px-1.5 py-0.5 text-[10px]">→</kbd>{" "}
        approve
      </span>
      <span>
        <kbd className="rounded-button border border-border bg-surface px-1.5 py-0.5 text-[10px]">space</kbd>{" "}
        details
      </span>
      <span>
        <kbd className="rounded-button border border-border bg-surface px-1.5 py-0.5 text-[10px]">esc</kbd>{" "}
        close
      </span>
    </div>
  );
}
