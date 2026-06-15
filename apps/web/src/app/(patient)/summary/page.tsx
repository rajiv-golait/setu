"use client";

import { useEffect, useState } from "react";
import { Volume2 } from "lucide-react";
import { getSummary } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { PatientSummary } from "@/lib/types";
import { cn } from "@/lib/cn";

export default function SummaryPage() {
  const { patient, ready } = usePatient();
  const [lang, setLang] = useState<"mr" | "en">("mr");
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getSummary(patient.id, lang)
      .then(setSummary)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load summary"));
  }, [patient?.id, ready, lang]);

  const isMr = lang === "mr";

  return (
    <div
      className={cn("animate-setu-fade px-5 pb-8 pt-5", isMr && "font-devanagari")}
      lang={lang}
    >
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-[23px] font-semibold tracking-tight">Your summary</h1>
        <div className="flex rounded-[11px] bg-[#E0E0D8] p-1">
          {(["mr", "en"] as const).map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => setLang(l)}
              className={cn(
                "rounded-lg px-3 py-1.5 text-[13px] font-semibold",
                lang === l ? "bg-white text-primary shadow-sm" : "text-text-muted",
              )}
            >
              {l === "mr" ? "मराठी" : "English"}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-danger">{error}</p>}
      {!summary && !error && <p className="text-text-faint">Loading…</p>}

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
                  <p className={cn("mt-1 text-base", isMr && "font-devanagari")}>{m.how_to_take}</p>
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

          <button
            type="button"
            aria-label="Listen to this summary"
            className="mt-4 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-[13px] border border-border bg-surface-raised text-[15px] font-semibold text-primary"
          >
            <Volume2 className="h-[18px] w-[18px]" aria-hidden />
            Listen to this summary
          </button>
        </>
      )}
    </div>
  );
}
