/* ── CommandMessage ─────────────────────────────────────────────────

   User/agent bubble with role badge, content, inline actions.
*/

"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system";
  content: string;
  timestamp: string;
  cards?: Record<string, any>[];
  actions?: Record<string, any>[];
}

interface CommandMessageProps {
  message: ChatMessage;
  onAction?: (actionId: string, payload: any) => void;
}

const ROLE_CONFIG = {
  user: {
    badge: "YOU",
    badgeVariant: "user" as const,
    align: "end" as const,
    avatarColor: "bg-info text-white",
  },
  agent: {
    badge: "AI",
    badgeVariant: "ai" as const,
    align: "start" as const,
    avatarColor: "bg-ai-light text-ai",
  },
  system: {
    badge: "SYSTEM",
    badgeVariant: "secondary" as const,
    align: "start" as const,
    avatarColor: "bg-surface-hover text-text-secondary",
  },
};

export function CommandMessage({ message, onAction }: CommandMessageProps) {
  const config = ROLE_CONFIG[message.role];

  return (
    <div className={cn("flex gap-2", config.align === "end" && "flex-row-reverse")}>
      <Avatar className="h-6 w-6">
        <AvatarFallback className={cn("text-[10px] font-bold", config.avatarColor)}>
          {config.badge[0]}
        </AvatarFallback>
      </Avatar>
      <div className={cn("max-w-[85%] space-y-1", config.align === "end" && "items-end")}>
        <div className="flex items-center gap-1.5">
          <Badge variant={config.badgeVariant} className="rounded-badge text-[9px]">
            {config.badge}
          </Badge>
          <span className="text-[10px] text-text-tertiary">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", timeZone: "UTC" })}
          </span>
        </div>
        <div
          className={cn(
            "rounded-card px-3 py-2 text-sm",
            message.role === "user"
              ? "bg-primary text-white"
              : message.role === "system"
              ? "bg-surface-hover text-text-secondary"
              : "bg-card text-text-primary"
          )}
        >
          {message.content}
          
          {message.cards && message.cards.length > 0 && (
            <div className="mt-3 flex flex-col gap-2">
              {message.cards.map((card, i) => {
                if (card.type === "candidate") {
                  const data = card.data as any;
                  return (
                    <div key={i} className="rounded-md border border-border bg-surface p-3 text-xs">
                      <div className="font-semibold text-text-primary">
                        {data?.first_name} {data?.last_name}
                      </div>
                      <div className="text-text-secondary">{data?.current_title}</div>
                      <div className="mt-1 flex items-center justify-between text-[10px]">
                        <span className="text-text-tertiary">Fit Score:</span>
                        <span className="font-medium text-success">{Math.round((card.fitScore as number || 0) * 100)}%</span>
                      </div>
                    </div>
                  );
                } else if (card.type === "outreach") {
                  const data = card.data as any;
                  return (
                    <div key={i} className="rounded-md border border-border bg-surface p-3 text-xs">
                      <div className="font-semibold text-text-primary">Draft: {data?.subject}</div>
                      <div className="mt-1 text-text-secondary line-clamp-3">{data?.body}</div>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          )}
          
          {message.actions && message.actions.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {message.actions.map((action, i) => (
                <Button 
                  key={action.id as string || i} 
                  size="sm" 
                  variant="secondary" 
                  className="h-7 text-xs"
                  onClick={() => onAction && onAction(action.id as string, action.payload)}
                >
                  {action.label as string}
                </Button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
