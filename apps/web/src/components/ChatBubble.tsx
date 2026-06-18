import { HeartHandshake, Stethoscope, Sparkles } from "lucide-react";
import { SaathiAvatar } from "@/components/characters/saathi-avatar";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  action?: "urgent_care" | "see_doctor" | "monitor" | "none";
  /** Show Saathi's avatar beside this assistant bubble (first in a run). */
  showAvatar?: boolean;
}

export function ChatBubble({ role, content, action, showAvatar = true }: ChatBubbleProps) {
  const isUser = role === "user";

  // Caring, never clinical. Saathi's voice — gentle direction, not an alarm.
  const actionBanner =
    action === "urgent_care" ? (
      <div className="mb-2 flex items-start gap-2 rounded-[12px] border border-danger-border bg-danger-bg px-3 py-2.5 text-sm text-danger">
        <HeartHandshake className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <span>
          <span className="font-semibold">Let&apos;s get you to a doctor right now.</span> If it feels
          serious, please go to the nearest hospital or call 112.
        </span>
      </div>
    ) : action === "see_doctor" ? (
      <div className="mb-2 flex items-start gap-2 rounded-[12px] border border-warning-border bg-warning-bg px-3 py-2.5 text-sm text-warning">
        <Stethoscope className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <span>This is worth mentioning to your doctor soon — I can help you book a visit.</span>
      </div>
    ) : action === "monitor" ? (
      <div className="mb-2 flex items-start gap-2 rounded-[12px] border border-marigold-border bg-marigold-bg px-3 py-2.5 text-sm text-[#9A6912]">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-marigold" aria-hidden />
        <span>Let&apos;s keep an eye on this together.</span>
      </div>
    ) : null;

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-3 text-sm leading-relaxed text-white whitespace-pre-wrap">
          {content}
        </div>
      </div>
    );
  }

  const concerned = action === "urgent_care" || action === "see_doctor";

  return (
    <div className="flex items-start gap-2">
      <div className="w-8 shrink-0 pt-1">
        {showAvatar && (
          <SaathiAvatar state={concerned ? "concerned" : "idle"} size={32} label={null} />
        )}
      </div>
      <div className="min-w-0 flex-1">
        {actionBanner}
        <div className="rounded-2xl rounded-tl-sm border border-saathi-border bg-saathi-bg px-4 py-3 text-sm leading-relaxed text-text whitespace-pre-wrap">
          {content}
        </div>
      </div>
    </div>
  );
}
