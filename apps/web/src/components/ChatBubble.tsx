import { cn } from "@/lib/cn";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  action?: "urgent_care" | "see_doctor" | "monitor" | "none";
}

export function ChatBubble({ role, content, action }: ChatBubbleProps) {
  const isUser = role === "user";

  const actionBanner =
    action === "urgent_care" ? (
      <div className="mb-2 rounded-[10px] border border-danger-border bg-danger-bg px-3 py-2 text-xs font-semibold text-danger">
        Emergency — go to hospital or call 112 immediately
      </div>
    ) : action === "see_doctor" ? (
      <div className="mb-2 rounded-[10px] border border-warning-border bg-warning-bg px-3 py-2 text-xs font-semibold text-warning">
        Please speak with your doctor soon
      </div>
    ) : null;

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("max-w-[80%]", !isUser && "w-full")}>
        {!isUser && actionBanner}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
            isUser
              ? "rounded-br-sm bg-primary text-white"
              : "rounded-bl-sm bg-surface-raised border border-border text-text",
          )}
        >
          {content}
        </div>
      </div>
    </div>
  );
}
