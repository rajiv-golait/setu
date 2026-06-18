"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getDocumentExplanation, getSummary } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { PatientSummary } from "@/lib/types";
import { cn } from "@/lib/cn";

export default function SummaryPage() {
  return (
    <Suspense fallback={<div className="px-5 py-10 text-center text-sm text-text-faint">Loading…</div>}>
      <SummaryContent />
    </Suspense>
  );
}

function SummaryContent() {
  const { patient, ready } = usePatient();
  const searchParams = useSearchParams();
  const docId = searchParams.get("docId");

  const [lang, setLang] = useState<"mr" | "en" | "hi">("mr");
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [fallbackText, setFallbackText] = useState<string | null>(null);
  const [isLiveAI, setIsLiveAI] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    const pref = (patient.langPref ?? "mr") as "mr" | "en" | "hi";
    setLang(pref === "hi" ? "hi" : pref === "en" ? "en" : "mr");
  }, [patient?.langPref, patient?.id, ready]);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getSummary(patient.id, lang)
      .then((s) => {
        setSummary(s);
        // Real reasoner (not the mock) → quiet "AI verified" reassurance.
        if (s.model && s.model !== "mock") setIsLiveAI(true);
      })
      .catch(async () => {
        // Fall back to the raw explanation from the last processed document.
        if (!docId) {
          setError("Summary not ready yet. Please try again in a moment.");
          return;
        }
        try {
          const data = await getDocumentExplanation(docId);
          setFallbackText(data.explanation ?? null);
          if (data.source === "live_ai") setIsLiveAI(true);
        } catch {
          setError("Could not load your summary. Please try again.");
        }
      });
  }, [patient?.id, ready, lang, docId]);

  const usesDevanagari = lang === "mr" || lang === "hi";

  return (
    <div
      className={cn("animate-setu-fade px-5 pb-8 pt-5", usesDevanagari && "font-devanagari")}
      lang={lang}
    >
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="font-display text-[23px] font-semibold tracking-tight">In simple words</h1>
          {isLiveAI && (
            <span className="rounded-full bg-success-bg px-2 py-0.5 text-xs font-semibold text-success">
              AI verified
            </span>
          )}
        </div>
        <div className="flex rounded-[11px] bg-[#E0E0D8] p-1">
          {(["mr", "hi", "en"] as const).map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => setLang(l)}
              className={cn(
                "rounded-lg px-3 py-1.5 text-[13px] font-semibold",
                lang === l ? "bg-white text-primary shadow-sm" : "text-text-muted",
              )}
            >
              {l === "mr" ? "मराठी" : l === "hi" ? "हिंदी" : "English"}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-danger">{error}</p>}
      {!summary && !fallbackText && !error && <p className="text-text-faint">Loading…</p>}

      {/* Fallback: show raw explanation text when structured summary isn't ready */}
      {!summary && fallbackText && (
        <div className="rounded-card border border-info-border bg-info-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-info-title">
            What we understood
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-[#3A5680]">
            {fallbackText}
          </p>
        </div>
      )}

      {summary && (
        <>
          <p className="text-xl font-semibold leading-relaxed">{summary.greeting}</p>

          <section className="mt-6">
            <h2 className="text-[13px] font-semibold uppercase tracking-wide text-primary-light">
              What we found
            </h2>
            <ul className="mt-3 space-y-2">
              {summary.what_we_found.map((line, i) => (
                <li key={i} className="flex gap-2 text-base">
                  <span className="text-success">✓</span>
                  {line}
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-6">
            <h2 className="text-[13px] font-semibold uppercase tracking-wide text-primary-light">
              Your medicines
            </h2>
            <div className="mt-3 flex flex-col gap-2.5">
              {summary.your_medicines.map((m) => (
                <div
                  key={m.name}
                  className="rounded-card border border-border bg-surface-raised p-4 shadow-card"
                >
                  <p className="font-sans font-semibold">{m.name}</p>
                  <p className={cn("mt-1 text-base", usesDevanagari && "font-devanagari")}>{m.how_to_take}</p>
                  <p className="mt-0.5 text-sm text-text-muted">{m.plain}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-6 rounded-card border border-warning-border bg-warning-bg p-4">
            <h2 className="text-[13px] font-semibold uppercase text-warning">What to watch</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[#7C3A06]">
              {summary.what_to_watch.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </section>

          <section className="mt-4 rounded-card border border-success-border bg-success-bg p-4">
            <h2 className="text-[13px] font-semibold uppercase text-success">Next steps</h2>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-success">
              {summary.next_steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </section>

          <p className="mt-5 text-sm italic text-text-faint">{summary.disclaimer}</p>
        </>
      )}

      {/* Secondary action — available once summary or fallback is showing */}
      {(summary || fallbackText) && (
        <div className="mt-6 space-y-2">
          <Link href="/brief">
            <button
              type="button"
              className="w-full rounded-card border border-border bg-surface-raised py-3.5 text-sm font-semibold text-text-muted shadow-card"
            >
              View doctor brief →
            </button>
          </Link>
          <Link href="/share">
            <button
              type="button"
              className="w-full rounded-card border border-primary/30 bg-[#EEF4F0] py-3.5 text-sm font-semibold text-primary shadow-card"
            >
              Share QR &amp; link with doctor →
            </button>
          </Link>
        </div>
      )}
    </div>
  );
}
