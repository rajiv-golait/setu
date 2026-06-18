"use client";

import { useEffect, useRef, useState } from "react";
import { getMemory, listNotifications } from "@/lib/api";
import { pushSaathiMessage } from "@/lib/saathi-history";
import type { CurrentTruth, CurrentTruthEntry } from "@/lib/types";

export interface NewMedEvent {
  /** normalized_key of the newly-arrived medication. */
  key: string;
  name: string;
  doctor?: string;
}

function medKeys(truth: CurrentTruth | null): Set<string> {
  if (!truth) return new Set();
  return new Set(
    truth.entries.filter((e) => e.entry_type === "medication").map((e) => e.normalized_key),
  );
}

function medName(entry: CurrentTruthEntry): string {
  const v = entry.value;
  const name = v.name ?? (Array.isArray(v.values) ? (v.values[0] as Record<string, unknown>)?.name : undefined);
  return String(name ?? entry.normalized_key);
}

/**
 * Polls CurrentTruth (and notifications) while mounted so a doctor's new
 * prescription lights up the patient's Today within seconds — the demo
 * centerpiece. On a newly-appeared medication it:
 *   - returns the latest truth (so Today re-renders with the new med),
 *   - sets `newMed` (drives the marigold banner),
 *   - writes a proactive Saathi message into chat history.
 *
 * The very first load establishes the baseline silently (no false "new med").
 */
export function useLiveMemory(patientId: string | null, intervalMs = 5000) {
  const [truth, setTruth] = useState<CurrentTruth | null>(null);
  const [newMed, setNewMed] = useState<NewMedEvent | null>(null);
  const baseline = useRef<Set<string> | null>(null);

  useEffect(() => {
    if (!patientId) return;
    let active = true;

    const tick = async () => {
      if (document.visibilityState === "hidden" || !active) return;
      try {
        const next = await getMemory(patientId);
        if (!active) return;
        const keys = medKeys(next);

        if (baseline.current === null) {
          // First successful load — establish baseline, no event.
          baseline.current = keys;
          setTruth(next);
          return;
        }

        const added = Array.from(keys).filter((k) => !baseline.current!.has(k));
        setTruth(next);

        if (added.length > 0) {
          const entry = next.entries.find((e) => e.normalized_key === added[0]);
          const name = entry ? medName(entry) : "a new medicine";

          // Try to attribute the doctor from the latest notification.
          let doctor: string | undefined;
          try {
            const notifs = await listNotifications();
            const hit = notifs.find(
              (n) => (n.data as Record<string, unknown> | undefined)?.type === "new_prescription",
            );
            const d = hit?.data as Record<string, unknown> | undefined;
            if (d?.doctor) doctor = String(d.doctor);
          } catch {
            /* notifications optional */
          }

          baseline.current = keys;
          setNewMed({ key: added[0], name, doctor });
          pushSaathiMessage({
            role: "assistant",
            content: `${doctor ?? "Your doctor"} just added ${name} to your medicines. I've added it to your Today. Want me to remind you when it's time to take it?`,
            action: "monitor",
          });
        }
      } catch {
        /* transient — keep last truth, retry next tick */
      }
    };

    void tick();
    const timer = setInterval(tick, intervalMs);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [patientId, intervalMs]);

  const dismissNewMed = () => setNewMed(null);

  return { truth, newMed, dismissNewMed };
}
