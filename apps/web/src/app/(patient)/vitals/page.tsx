"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { VitalTrendChart, formatVitalValue } from "@/components/vitals/vital-trend-chart";
import { createVital, listVitals } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import { useLocale } from "@/lib/hooks/use-locale";
import type { VitalReading, VitalType } from "@/lib/types";

export default function VitalsPage() {
  const router = useRouter();
  const { patient, ensurePatient } = usePatient();
  const { t } = useLocale();
  const [readings, setReadings] = useState<VitalReading[]>([]);
  const [vitalType, setVitalType] = useState<VitalType>("blood_pressure");
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [sugar, setSugar] = useState("");
  const [spo2, setSpo2] = useState("");
  const [hr, setHr] = useState("");
  const [loading, setLoading] = useState(false);

  const load = (pid: string) => {
    listVitals(pid)
      .then(setReadings)
      .catch(() => setReadings([]));
  };

  useEffect(() => {
    if (patient?.id) load(patient.id);
  }, [patient?.id]);

  const submit = async () => {
    setLoading(true);
    try {
      const p = patient ?? (await ensurePatient());
      let value: Record<string, unknown> = {};
      let unit = "";
      if (vitalType === "blood_pressure") {
        value = { systolic: parseInt(systolic, 10), diastolic: parseInt(diastolic, 10) };
        unit = "mmHg";
      } else if (vitalType === "blood_sugar") {
        value = { fasting: parseFloat(sugar) };
        unit = "mg/dL";
      } else if (vitalType === "spo2") {
        value = { percent: parseInt(spo2, 10) };
        unit = "%";
      } else {
        value = { bpm: parseInt(hr, 10) };
        unit = "bpm";
      }
      await createVital(p.id, { vital_type: vitalType, value, unit, source: "manual" });
      load(p.id);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Could not save");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-4">
      <button
        type="button"
        onClick={() => router.back()}
        className="mb-4 flex items-center gap-2 text-sm font-semibold text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <h1 className="text-[23px] font-semibold">{t("vitals.title")}</h1>
      <p className="mt-1 text-sm text-text-muted">
        For your records only — not a diagnosis.
      </p>

      <div className="mt-5 flex flex-wrap gap-2">
        {(
          [
            ["blood_pressure", "BP"],
            ["blood_sugar", "Sugar"],
            ["spo2", "SpO₂"],
            ["heart_rate", "Heart rate"],
          ] as const
        ).map(([type, label]) => (
          <button
            key={type}
            type="button"
            onClick={() => setVitalType(type)}
            className={`rounded-full border px-3 py-1.5 text-sm ${
              vitalType === type ? "border-primary bg-primary text-white" : "border-border"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-4 space-y-3">
        {vitalType === "blood_pressure" && (
          <div className="flex gap-2">
            <input
              placeholder="Systolic"
              value={systolic}
              onChange={(e) => setSystolic(e.target.value)}
              className="flex-1 rounded-card border border-border px-3 py-2"
            />
            <input
              placeholder="Diastolic"
              value={diastolic}
              onChange={(e) => setDiastolic(e.target.value)}
              className="flex-1 rounded-card border border-border px-3 py-2"
            />
          </div>
        )}
        {vitalType === "blood_sugar" && (
          <input
            placeholder="Fasting mg/dL"
            value={sugar}
            onChange={(e) => setSugar(e.target.value)}
            className="w-full rounded-card border border-border px-3 py-2"
          />
        )}
        {vitalType === "spo2" && (
          <input
            placeholder="SpO₂ %"
            value={spo2}
            onChange={(e) => setSpo2(e.target.value)}
            className="w-full rounded-card border border-border px-3 py-2"
          />
        )}
        {vitalType === "heart_rate" && (
          <input
            placeholder="BPM"
            value={hr}
            onChange={(e) => setHr(e.target.value)}
            className="w-full rounded-card border border-border px-3 py-2"
          />
        )}
      </div>

      <PrimaryButton className="mt-4" disabled={loading} onClick={submit}>
        {t("vitals.log")}
      </PrimaryButton>

      <VitalTrendChart readings={readings} vitalType={vitalType} />

      <div className="mt-8 space-y-3">
        {readings.slice(0, 10).map((r) => (
          <div
            key={r.id}
            className="rounded-card border border-border bg-surface-raised px-4 py-3 text-sm"
          >
            <div className="flex justify-between">
              <span className="font-semibold capitalize">{r.vital_type.replace("_", " ")}</span>
              <span className="text-text-muted">
                {new Date(r.measured_at).toLocaleString("en-IN", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <p className="mt-1">{formatVitalValue(r)}</p>
            {r.flag_message && (
              <p className="mt-1 text-xs text-warning">{r.flag_message}</p>
            )}
          </div>
        ))}
      </div>

      <Link href="/memory" className="mt-6 block text-center text-sm font-semibold text-primary">
        View in health memory →
      </Link>
    </div>
  );
}
