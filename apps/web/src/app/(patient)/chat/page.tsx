"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { ChatBubble } from "@/components/ChatBubble";
import { getMemory, saathiChat } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { CurrentTruth } from "@/lib/types";
import { cn } from "@/lib/cn";

interface Message {
  role: "user" | "assistant";
  content: string;
  action?: "urgent_care" | "see_doctor" | "monitor" | "none";
}

const SESSION_KEY = "setu_saathi_history";

function loadHistory(): Message[] {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as Message[]) : [];
  } catch {
    return [];
  }
}

function saveHistory(msgs: Message[]) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(msgs.slice(-20)));
  } catch {}
}

export default function ChatPage() {
  const { patient, ready } = usePatient();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [memory, setMemory] = useState<CurrentTruth | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const lang = (patient?.langPref ?? "mr") as "mr" | "en" | "hi";
  const usesDevanagari = lang === "mr" || lang === "hi";

  // Load chat history from sessionStorage and memory on mount.
  useEffect(() => {
    setMessages(loadHistory());
  }, []);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getMemory(patient.id)
      .then(setMemory)
      .catch(() => undefined);
  }, [patient?.id, ready]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || loading || !patient?.id) return;

    const userMsg: Message = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const history = next
        .slice(-12)
        .map((m) => ({ role: m.role, content: m.content }));
      const res = await saathiChat(patient.id, text, history, lang);
      const assistantMsg: Message = {
        role: "assistant",
        content: res.reply,
        action: res.action as Message["action"],
      };
      const updated = [...next, assistantMsg];
      setMessages(updated);
      saveHistory(updated);
    } catch {
      const errMsg: Message = {
        role: "assistant",
        content:
          lang === "mr"
            ? "माफ करा, सध्या उत्तर देता येत नाही. डॉक्टरांशी बोला."
            : lang === "hi"
              ? "माफ़ करें, अभी उत्तर नहीं दे सकते। डॉक्टर से बात करें।"
              : "Sorry, I can't answer right now. Please speak with your doctor.",
        action: "none",
      };
      setMessages([...next, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  const meds = memory?.entries.filter((e) => e.entry_type === "medication") ?? [];

  return (
    <div className="flex h-screen flex-col" lang={lang}>
      {/* Header */}
      <div className="border-b border-border bg-surface-raised px-5 pt-5 pb-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">
          आपला आरोग्य सहायक
        </p>
        <h1 className={cn("text-[23px] font-semibold", usesDevanagari && "font-devanagari")}>
          Saathi
        </h1>
        {meds.length > 0 && (
          <p className="mt-1 text-xs text-text-muted">
            {meds.length} medicine{meds.length > 1 ? "s" : ""} on file
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="mt-8 text-center text-text-muted">
            <p className={cn("text-base", usesDevanagari && "font-devanagari")}>
              {lang === "mr"
                ? "तुमच्या आरोग्याबद्दल प्रश्न विचारा"
                : lang === "hi"
                  ? "अपनी सेहत के बारे में पूछें"
                  : "Ask about your health records"}
            </p>
            <p className="mt-2 text-xs">
              {lang === "en"
                ? "Saathi only knows what's in your health records."
                : lang === "mr"
                  ? "साथी फक्त तुमच्या नोंदींमधून उत्तर देतो."
                  : "साथी केवल आपके रिकॉर्ड से जवाब देता है।"}
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} action={m.action} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-surface-raised border border-border px-4 py-3">
              <span className="flex gap-1">
                <span className="h-2 w-2 animate-pulse-dot rounded-full bg-text-muted" style={{ animationDelay: "0ms" }} />
                <span className="h-2 w-2 animate-pulse-dot rounded-full bg-text-muted" style={{ animationDelay: "150ms" }} />
                <span className="h-2 w-2 animate-pulse-dot rounded-full bg-text-muted" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border bg-surface-raised px-4 py-3 pb-[calc(env(safe-area-inset-bottom)+80px)]">
        <div className="flex items-end gap-2">
          <textarea
            className={cn(
              "flex-1 resize-none rounded-[14px] border border-border bg-surface px-4 py-3 text-sm outline-none focus:border-primary",
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
              lang === "mr"
                ? "प्रश्न विचारा…"
                : lang === "hi"
                  ? "प्रश्न पूछें…"
                  : "Ask a question…"
            }
          />
          <button
            type="button"
            onClick={() => void send()}
            disabled={loading || !input.trim()}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary text-white disabled:opacity-40"
          >
            <Send className="h-5 w-5" strokeWidth={1.8} />
          </button>
        </div>
      </div>
    </div>
  );
}
