/* ── InputBar ───────────────────────────────────────────────────────

   Text input, attach, voice, send button.
*/

"use client";

import { useState, type FormEvent } from "react";
import { Paperclip, Mic, Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface InputBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-1 p-2"
    >
      <button
        type="button"
        className="rounded-button p-1.5 text-text-tertiary hover:bg-hover hover:text-text-secondary transition"
        title="Attach file"
      >
        <Paperclip className="h-4 w-4" />
      </button>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask me anything…"
        className={cn(
          "flex-1 bg-transparent text-sm text-text-primary placeholder-text-tertiary outline-none",
          "disabled:opacity-50"
        )}
        disabled={disabled}
      />
      <button
        type="button"
        className="rounded-button p-1.5 text-text-tertiary hover:bg-hover hover:text-text-secondary transition"
        title="Voice input"
      >
        <Mic className="h-4 w-4" />
      </button>
      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className={cn(
          "rounded-button p-1.5 text-white transition",
          text.trim() && !disabled
            ? "bg-primary hover:bg-primary-hover"
            : "bg-surface-hover text-text-tertiary"
        )}
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}
