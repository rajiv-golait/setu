"use client";

import { useCallback, useEffect, useState } from "react";
import { createPatient, getPatient } from "@/lib/api";

const STORAGE_KEY = "setu_patient";

export interface StoredPatient {
  id: string;
  token: string;
  displayName?: string;
}

function readStored(): StoredPatient | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredPatient) : null;
  } catch {
    return null;
  }
}

function writeStored(p: StoredPatient) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}

export function usePatient() {
  const [patient, setPatient] = useState<StoredPatient | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = readStored();
    if (!stored) {
      setReady(true);
      return;
    }

    getPatient(stored.id)
      .then((record) => {
        const next: StoredPatient = {
          id: record.id,
          token: stored.token,
          displayName: record.display_name ?? undefined,
        };
        writeStored(next);
        setPatient(next);
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setPatient(null);
      })
      .finally(() => setReady(true));
  }, []);

  const ensurePatient = useCallback(async () => {
    const existing = readStored();
    if (existing) {
      setPatient(existing);
      return existing;
    }
    const created = await createPatient();
    const next: StoredPatient = {
      id: created.id,
      token: created.patient_token!,
      displayName: created.display_name ?? undefined,
    };
    writeStored(next);
    setPatient(next);
    return next;
  }, []);

  const clearPatient = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setPatient(null);
  }, []);

  return { patient, ready, ensurePatient, clearPatient, setPatient };
}
