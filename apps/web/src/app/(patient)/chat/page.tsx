"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { ChatBubble } from "@/components/ChatBubble";
import { SaathiAvatar, type SaathiState } from "@/components/characters/saathi-avatar";
import { getMemory, saathiChat } from "@/lib/api";
import { useLocale } from "@/lib/hooks/use-locale";
import { usePatient } from "@/lib/hooks/use-patient";
import {
  clearSaathiUnread,
  loadSaathiHistory,
  saveSaathiHistory,
  type SaathiMessage,
} from "@/lib/saathi-history";
import type { CurrentTruth } from "@/lib/types";
import { cn } from "@/lib/cn";

function groundingChips(memory: CurrentTruth | null, lang: "mr" | "hi" | "en"): string[] {
  if (!memory) return [];
  const meds = memory.entries.filter((e) => e.entry_type === "medication").length;
  const labs = memory.entries.filter((e) => e.entry_type === "lab_result").length;
  const allergies = memory.entries.filter((e) => e.entry_type === "allergy");
  const chips: string[] = [];
  const t = (en: string, mr: string, hi: string) => (lang === "mr" ? mr : lang === "hi" ? hi : en);
  if (meds > 0) chips.push(t(`your ${meds} medicine${meds > 1 ? "s" : ""}`, `तुमची ${meds} औषधे`, `आपकी ${meds} दवाइयाँ`));
  if (labs > 0) chips.push(t("your lab trends", "तुमचे रिपोर्ट", "आपकी रिपोर्ट"));
  if (allergies.length > 0) {
    const sub = String(allergies[0].value.substance ?? allergies[0].normalized_key);
    chips.push(t(`your ${sub} allergy`, `${sub} ची ॲलर्जी`, `${sub} एलर्जी`));
  }
  return chips;
}

function warmGreeting(name: string, lang: "mr" | "hi" | "en"): string {
  const first = name || (lang === "en" ? "friend" : "मित्रा");
  if (lang === "mr") return `नमस्कार ${name || "मित्रा"}! मी साथी. तुमच्या औषधांबद्दल किंवा रिपोर्टबद्दल काहीही विचारा — मी तुमच्या नोंदींमधून सोप्या भाषेत सांगेन.`;
  if (lang === "hi") return `नमस्ते ${name || "दोस्त"}! मैं साथी हूँ। अपनी दवाइयों या रिपोर्ट के बारे में कुछ भी पूछें — मैं आपके रिकॉर्ड से आसान भाषा में बताऊँगा।`;
  return `Hi ${first}! I'm Saathi. Ask me anything about your medicines or reports — I'll explain from your records, in simple words.`;
}

export default function ChatPage() {
  const { patient, ready } = usePatient();
  const { locale: lang } = useLocale();
  const [messages, setMessages] = useState<SaathiMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [memory, setMemory] = useState<CurrentTruth | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const usesDevanagari = lang === "mr" || lang === "hi";

  // Load any proactive history (e.g. a new-medicine message) and clear the unread flag.
  useEffect(() => {
    setMessages(loadSaathiHistory());
    clearSaathiUnread();
  }, []);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getMemory(patient.id).then(setMemory).catch(() => undefined);
  }, [patient?.id, ready]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading || !patient?.id) return;

    const userMsg: SaathiMessage = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const history = messages.slice(-11).map((m) => ({ role: m.role, content: m.content }));
      const res = await saathiChat(patient.id, text, history, lang);
      const assistantMsg: SaathiMessage = {
        role: "assistant",
        content: res.reply,
        action: res.action as SaathiMessage["action"],
      };
      const updated = [...next, assistantMsg];
      setMessages(updated);
      saveSaathiHistory(updated);
    } catch {
      const errMsg: SaathiMessage = {
        role: "assistant",
        content:
          lang === "mr"
            ? "माफ करा, सध्या उत्तर देता येत नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."
            : lang === "hi"
              ? "माफ़ करें, अभी जवाब नहीं दे पा रहा। थोड़ी देर बाद फिर कोशिश करें।"
              : "I couldn't reach my notes just now — please try again in a moment.",
        action: "none",
      };
      setMessages([...next, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  const chips = groundingChips(memory, lang);
  const headerState: SaathiState = loading ? "thinking" : "idle";

  if (!ready) {
    return <div className="px-5 py-10 text-center text-sm text-text-faint">Loading…</div>;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-surface" lang={lang}>
      {/* Header — Saathi's home */}
      <div className="shrink-0 border-b border-saathi-border bg-saathi-bg px-4 pb-2.5 pt-4">
        <div className="flex items-center gap-3">
          <SaathiAvatar state={headerState} size={44} label={null} />
          <div>
            <h1 className={cn("font-display text-[22px] font-semibold text-text", usesDevanagari && "font-devanagari")}>
              Saathi
            </h1>
            <p className="text-xs font-semibold text-saathi-deep">
              {lang === "mr" ? "तुमचा आरोग्य सोबती" : lang === "hi" ? "आपका सेहत साथी" : "your health companion"}
            </p>
          </div>
        </div>
        {chips.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            <span className="text-[11px] font-semibold text-text-muted">
              {lang === "mr" ? "साथीला माहीत आहे:" : lang === "hi" ? "साथी जानता है:" : "Saathi knows:"}
            </span>
            {chips.map((c) => (
              <span
                key={c}
                className={cn(
                  "rounded-full border border-saathi-border bg-white px-2 py-0.5 text-[11px] font-medium text-saathi-deep",
                  usesDevanagari && "font-devanagari",
                )}
              >
                {c}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="min-h-0 flex-1 space-y-2.5 overflow-y-auto overscroll-contain px-3 py-3">
        {messages.length === 0 && (
          <ChatBubble role="assistant" content={warmGreeting(patient?.displayName?.split(" ")[0] ?? "", lang)} />
        )}
        {messages.map((m, i) => (
          <ChatBubble
            key={i}
            role={m.role}
            content={m.content}
            action={m.action}
            showAvatar={m.role === "assistant" && (i === 0 || messages[i - 1]?.role !== "assistant")}
          />
        ))}
        {loading && (
          <div className="flex items-start gap-2">
            <div className="w-7 shrink-0 pt-0.5">
              <SaathiAvatar state="thinking" size={28} label={null} />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-saathi-border bg-saathi-bg px-3.5 py-2.5">
              <span className="flex gap-1">
                <span className="h-2 w-2 animate-saathi-dot rounded-full bg-saathi" style={{ animationDelay: "0ms" }} />
                <span className="h-2 w-2 animate-saathi-dot rounded-full bg-saathi" style={{ animationDelay: "180ms" }} />
                <span className="h-2 w-2 animate-saathi-dot rounded-full bg-saathi" style={{ animationDelay: "360ms" }} />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input — sits above bottom nav */}
      <div className="shrink-0 border-t border-border bg-surface-raised px-3 py-2.5 pb-[calc(env(safe-area-inset-bottom)+4.5rem)]">
        <div className="flex items-end gap-2">
          <textarea
            className={cn(
              "max-h-28 min-h-[44px] flex-1 resize-none rounded-[14px] border border-border bg-surface px-3.5 py-2.5 text-sm outline-none focus:border-saathi",
              usesDevanagari && "font-devanagari",
            )}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            placeholder={
              lang === "mr" ? "प्रश्न विचारा…" : lang === "hi" ? "प्रश्न पूछें…" : "Ask Saathi a question…"
            }
          />
          <button
            type="button"
            onClick={() => void send()}
            disabled={loading || !input.trim()}
            aria-label="Send"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-saathi text-white disabled:opacity-40"
          >
            <Send className="h-5 w-5" strokeWidth={1.8} />
          </button>
        </div>
      </div>
    </div>
  );
}
