/* ── Skeleton ───────────────────────────────────────────────────────

   Pulsing placeholder cards for loading states.
*/

import { cn } from "@/lib/utils";

type SkeletonProps = React.HTMLAttributes<HTMLDivElement>;

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn("animate-pulse-subtle rounded-card bg-surface-hover", className)}
      {...props}
    />
  );
}

export function SkeletonCard({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-card border border-border bg-card p-4",
        className
      )}
      {...props}
    >
      <Skeleton className="h-4 w-3/4" />
      <div className="mt-3 space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
      </div>
    </div>
  );
}

export function SkeletonFeedItem({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-card border border-border bg-card p-4",
        className
      )}
      {...props}
    >
      <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
      </div>
    </div>
  );
}
