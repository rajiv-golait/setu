/**
 * Drift classifier — PURE, READ-ONLY, NON-DIAGNOSTIC.
 *
 * Reads already-fetched CurrentTruth (lab value.trend) and VitalsSummary
 * (trends dict). Produces at most ONE nudge for display on Today.
 *
 * Safety contract:
 * - Output is always "worth mentioning to your doctor" — never a clinical alarm.
 * - Never names a disease, never recommends a dose change.
 * - "worse" → amber informational text only; "improving" → reassurance.
 * - If no non-stable signal exists, returns null (no nudge shown).
 */

import type { CurrentTruth, VitalsSummary } from "./types";

export type DriftDirection = "improving" | "stable" | "worse";

export interface DriftNudge {
  label: string;          // e.g. "Blood sugar" or "HbA1c"
  direction: DriftDirection;
  message: string;        // calm, non-diagnostic text for the patient
  saathiHint: string;     // text pushed to Saathi history (also non-diagnostic)
}

// Human-readable labels for vital types.
const VITAL_LABELS: Record<string, string> = {
  blood_sugar: "Blood sugar",
  blood_pressure: "Blood pressure",
  spo2: "Oxygen level",
  heart_rate: "Heart rate",
};

// Map reducer trend string → DriftDirection.
// Reducer uses "up"/"down"/"stable"; direction meaning is vital-dependent
// (e.g. "up" for blood_sugar → worse; "up" for spo2 → improving).
const WORSE_IS_UP = new Set(["blood_sugar", "blood_pressure", "heart_rate", "hba1c",
  "fasting_blood_sugar", "postprandial_blood_sugar", "ldl_cholesterol", "creatinine"]);
const WORSE_IS_DOWN = new Set(["spo2", "egfr"]);

function reducerTrendToDirection(
  reducerTrend: string,
  key: string,
): DriftDirection {
  if (reducerTrend === "stable") return "stable";
  const isUp = reducerTrend === "up";
  if (WORSE_IS_UP.has(key)) return isUp ? "worse" : "improving";
  if (WORSE_IS_DOWN.has(key)) return isUp ? "improving" : "worse";
  // Unknown key: treat directional change as worth noting but don't label worse/improving.
  return "stable"; // conservative — don't surface unknown keys
}

function makeMessage(label: string, direction: DriftDirection): { message: string; saathiHint: string } {
  if (direction === "improving") {
    return {
      message: `Your ${label.toLowerCase()} reading looks better than last time. Worth mentioning to your doctor.`,
      saathiHint: `Your ${label.toLowerCase()} is trending better than your last reading. Good to mention at your next visit.`,
    };
  }
  // "worse" — calm, no alarm language
  return {
    message: `Your ${label.toLowerCase()} reading has shifted since last time. Worth mentioning to your doctor.`,
    saathiHint: `Your ${label.toLowerCase()} reading has changed since the last one. I'd suggest mentioning it to your doctor at the next visit.`,
  };
}

/**
 * Returns the single most relevant non-stable drift nudge, or null if everything
 * is stable / there is insufficient history.
 *
 * Priority: labs first (from CurrentTruth value.trend), then vitals (from
 * VitalsSummary.trends). First non-stable signal wins.
 */
export function computeDriftNudge(
  truth: CurrentTruth | null,
  vitalsSummary: VitalsSummary | null,
): DriftNudge | null {
  // 1. Labs — already in current_truth entries, reducer computed the diff.
  for (const entry of truth?.entries ?? []) {
    if (entry.entry_type !== "lab_result") continue;
    const trend = entry.value?.trend as string | undefined;
    if (!trend || trend === "stable" || trend === "null") continue;
    const direction = reducerTrendToDirection(trend, entry.normalized_key);
    if (direction === "stable") continue;
    const label = (entry.value?.test_name as string | undefined) ?? entry.normalized_key;
    return { label, direction, ...makeMessage(label, direction) };
  }

  // 2. Vitals — VitalsSummary.trends already computed by the backend series query.
  for (const [vt, trend] of Object.entries(vitalsSummary?.trends ?? {})) {
    if (!trend || trend === "stable") continue;
    const direction = reducerTrendToDirection(trend, vt);
    if (direction === "stable") continue;
    const label = VITAL_LABELS[vt] ?? vt;
    return { label, direction, ...makeMessage(label, direction) };
  }

  return null;
}
