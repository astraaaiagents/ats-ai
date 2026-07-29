/* ── Badge ──────────────────────────────────────────────────────────

   shadcn/ui-style badge with variants for different semantic types.
*/

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-badge px-2 py-0.5 text-xs font-medium transition",
  {
    variants: {
      variant: {
        default: "bg-primary-light text-primary",
        secondary: "bg-surface-card text-text-secondary",
        destructive: "bg-danger-light text-danger",
        outline: "border border-border text-text-secondary",
        ai: "bg-primary-light text-primary",
        lowConfidence: "bg-warning-light text-warning",
        agentSuggestion: "bg-ai-light text-ai",
        preferenceUpdated: "bg-ai-light text-ai",
        learning: "bg-ai-light text-ai",
        success: "bg-success-light text-success",
        user: "bg-info-light text-info",
        alert: "bg-danger-light text-danger",
        submitted: "bg-primary-light text-primary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
