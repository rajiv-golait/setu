import type { CurrentTruthEntry } from "@/lib/types";

export function medField(entry: CurrentTruthEntry, key: string): string {
  const v = entry.value;
  const val =
    v[key] ?? (Array.isArray(v.values) ? (v.values[0] as Record<string, unknown>)?.[key] : undefined);
  return val == null ? "" : String(val);
}

/** Plain-language "why" for a medicine — from its own instructions/frequency, never invented. */
export function medWhy(entry: CurrentTruthEntry): string {
  const instr = medField(entry, "instructions");
  if (instr) return instr;
  const freq = medField(entry, "frequency");
  const food = medField(entry, "relative_to_food");
  const parts = [freq, food].filter(Boolean);
  return parts.length ? parts.join(" · ") : "As prescribed by your doctor";
}
