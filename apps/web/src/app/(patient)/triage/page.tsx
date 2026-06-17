"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PrimaryButton } from "@/components/ui/buttons";
import { TriageResultCard } from "@/components/triage/triage-result-card";
import { listTriage, runTriage } from "@/lib/api";
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

export default function TriagePage() {
  const { patient, ensurePatient } = usePatient();
  const { t } = useLocale();
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [conditions, setConditions] = useState<string[]>([]);
  const [age, setAge] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<TriageResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patient?.id) return;
    listTriage(patient.id)
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [patient?.id]);

  const toggle = (list: string[], set: (v: string[]) => void, item: string) => {
    set(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
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

      <label className="mt-6 block text-sm font-semibold">Your age (optional)</label>
      <input
        type="number"
        min={0}
        max={120}
        value={age}
        onChange={(e) => setAge(e.target.value)}
        className="mt-2 w-full rounded-card border border-border px-4 py-3"
        placeholder="e.g. 45"
      />

      <p className="mt-5 text-sm font-semibold">Symptoms today</p>
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

      <p className="mt-5 text-sm font-semibold">Existing conditions</p>
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

      <PrimaryButton className="mt-6" disabled={loading || symptoms.length === 0} onClick={submit}>
        {loading ? "Checking…" : t("triage.submit")}
      </PrimaryButton>

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}

      {history.length > 0 && (
        <div className="mt-8 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">
            Recent guidance
          </h2>
          {history.map((r) => (
            <TriageResultCard key={r.id} result={r} />
          ))}
        </div>
      )}

      <Link href="/appointments/new" className="mt-6 block text-center text-sm font-semibold text-primary">
        Book a specialist directly →
      </Link>
    </div>
  );
}
