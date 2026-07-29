/* ── ErrorState ─────────────────────────────────────────────────────

   "Couldn't load" messages with retry button.
*/

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export function ErrorState({
  message = "Couldn't load data. Please try again.",
  onRetry,
  retryLabel = "Retry",
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-card border border-danger/30 bg-danger-light p-8 text-center",
        className
      )}
    >
      <div className="mb-2 text-2xl">!</div>
      <p className="text-sm text-danger">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-4 border-danger text-danger hover:bg-danger hover:text-white"
        >
          {retryLabel}
        </Button>
      )}
    </div>
  );
}
