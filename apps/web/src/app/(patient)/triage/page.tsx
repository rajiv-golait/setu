"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PrimaryButton } from "@/components/ui/buttons";
import { TriageResultCard } from "@/components/triage/triage-result-card";
import { listTriage, runTriage, symptomChatTriage } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import { useLocale } from "@/lib/hooks/use-locale";
import type { TriageResult } from "@/lib/types";

const SYMPTOM_OPTIONS = [
  "Persistent fever",
  "Chest pain",
  "Breathlessness",
  "Severe headache",
  "Dizziness",
  "Persistent cough",
  "Swelling",
  "Blurred vision",
];

const CONDITION_OPTIONS = ["Diabetes", "Hypertension", "Asthma", "Heart disease", "Pregnancy"];

const STEPS = ["About you", "Symptoms", "Conditions", "Guidance"] as const;

export default function TriagePage() {
  const { patient, ensurePatient } = usePatient();
  const { t } = useLocale();
  const [step, setStep] = useState(0);
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [conditions, setConditions] = useState<string[]>([]);
  const [age, setAge] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<TriageResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [chatResult, setChatResult] = useState<string | null>(null);

  useEffect(() => {
    if (!patient?.id) return;
    listTriage(patient.id)
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [patient?.id]);

  const toggle = (list: string[], set: (v: string[]) => void, item: string) => {
    set(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  };

  const runAssistant = async () => {
    if (symptoms.length === 0) return;
    setError(null);
    setLoading(true);
    try {
      const res = await symptomChatTriage({
        symptoms,
        existing_conditions: conditions,
        age: age ? parseInt(age, 10) : undefined,
      });
      setChatResult(res.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run symptom check");
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    setError(null);
    setLoading(true);
    try {
      const p = patient ?? (await ensurePatient());
      const result = await runTriage(p.id, {
        symptoms,
        existing_conditions: conditions,
        age: age ? parseInt(age, 10) : undefined,
      });
      setHistory((h) => [result, ...h]);
      setStep(3);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run triage");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <h1 className="text-[23px] font-semibold">{t("triage.title")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("triage.subtitle")}</p>

      <div className="mt-4 flex gap-2">
        {STEPS.map((label, i) => (
          <button
            key={label}
            type="button"
            onClick={() => setStep(i)}
            className={`flex-1 rounded-full border py-1 text-xs font-semibold ${
              step === i ? "border-primary bg-primary text-white" : "border-border"
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <p className="mt-2 text-sm font-semibold text-primary">{STEPS[step]}</p>

      {step === 0 && (
        <div className="mt-4">
          <label className="block text-sm font-semibold">Your age (optional)</label>
          <input
            type="number"
            min={0}
            max={120}
            value={age}
            onChange={(e) => setAge(e.target.value)}
            className="mt-2 w-full rounded-card border border-border px-4 py-3"
            placeholder="e.g. 45"
          />
          <PrimaryButton className="mt-4" onClick={() => setStep(1)}>
            Next
          </PrimaryButton>
        </div>
      )}

      {step === 1 && (
        <div className="mt-4">
          <p className="text-sm font-semibold">Symptoms today</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {SYMPTOM_OPTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => toggle(symptoms, setSymptoms, s)}
                className={`rounded-full border px-3 py-1.5 text-sm ${
                  symptoms.includes(s)
                    ? "border-primary bg-primary text-white"
                    : "border-border bg-surface-raised"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <button type="button" className="text-sm text-text-muted" onClick={() => setStep(0)}>
              Back
            </button>
            <PrimaryButton disabled={symptoms.length === 0} onClick={() => setStep(2)}>
              Next
            </PrimaryButton>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="mt-4">
          <p className="text-sm font-semibold">Existing conditions</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {CONDITION_OPTIONS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => toggle(conditions, setConditions, c)}
                className={`rounded-full border px-3 py-1.5 text-sm ${
                  conditions.includes(c)
                    ? "border-primary bg-[#EEF4F0] text-primary"
                    : "border-border bg-surface-raised"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" className="text-sm text-text-muted" onClick={() => setStep(1)}>
              Back
            </button>
            <PrimaryButton disabled={loading} onClick={submit}>
              {loading ? "Checking…" : t("triage.submit")}
            </PrimaryButton>
            <button
              type="button"
              disabled={loading}
              onClick={runAssistant}
              className="min-h-[44px] rounded-[13px] border border-border px-4 text-sm font-semibold text-primary"
            >
              Quick assistant
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="mt-4">
          {chatResult && (
            <p className="rounded-card border border-border bg-surface-raised p-4 text-sm text-text-muted">
              {chatResult}
            </p>
          )}
          {history[0] && <TriageResultCard result={history[0]} />}
          <PrimaryButton className="mt-4" onClick={() => setStep(0)}>
            Start over
          </PrimaryButton>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}

      {history.length > 1 && (
        <div className="mt-8 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">
            Recent guidance
          </h2>
          {history.slice(1).map((r) => (
            <TriageResultCard key={r.id} result={r} />
          ))}
        </div>
      )}

      <Link href="/doctors" className="mt-4 block text-center text-sm font-semibold text-primary">
        Find a doctor →
      </Link>
    </div>
  );
}
