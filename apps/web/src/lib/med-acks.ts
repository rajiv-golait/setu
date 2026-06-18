/**
 * Local "taken today" acknowledgements. Demo-scoped: stored per day in
 * sessionStorage so the celebratory check persists across the session without a
 * backend write. Keyed by med normalized_key + today's date.
 */
const KEY = "setu_med_acks";

function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

function load(): Record<string, string> {
  try {
    return JSON.parse(sessionStorage.getItem(KEY) ?? "{}") as Record<string, string>;
  } catch {
    return {};
  }
}

export function isTakenToday(medKey: string): boolean {
  return load()[medKey] === todayKey();
}

export function markTakenToday(medKey: string): void {
  try {
    const acks = load();
    acks[medKey] = todayKey();
    sessionStorage.setItem(KEY, JSON.stringify(acks));
  } catch {
    /* sessionStorage unavailable — non-fatal */
  }
}
