"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { createPatient, getPatient, getPatientMe, setApiTokenProvider } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";

const STORAGE_KEY = "setu_patient";

export interface StoredPatient {
  id: string;
  token?: string;
  displayName?: string;
  langPref: string;
  onboardingCompleted: boolean;
}

interface PatientContextValue {
  patient: StoredPatient | null;
  ready: boolean;
  ensurePatient: () => Promise<StoredPatient>;
  clearPatient: () => void;
  setPatient: (p: StoredPatient | null) => void;
  refreshPatient: () => Promise<void>;
}

const PatientContext = createContext<PatientContextValue | null>(null);

function readStored(): StoredPatient | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<StoredPatient> & { id: string };
    return {
      id: parsed.id,
      token: parsed.token,
      displayName: parsed.displayName,
      langPref: parsed.langPref ?? "mr",
      onboardingCompleted: parsed.onboardingCompleted ?? false,
    };
  } catch {
    return null;
  }
}

function patientFromRecord(
  record: {
    id: string;
    display_name?: string | null;
    lang_pref?: string;
    onboarding_completed?: boolean;
  },
  extra?: Partial<StoredPatient>,
): StoredPatient {
  return {
    id: record.id,
    displayName: record.display_name ?? undefined,
    langPref: record.lang_pref ?? "mr",
    onboardingCompleted: record.onboarding_completed ?? false,
    ...extra,
  };
}

function writeStored(p: StoredPatient) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}

export function PatientProvider({ children }: { children: React.ReactNode }) {
  const [patient, setPatientState] = useState<StoredPatient | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const supabase = createClient();

    if (SUPABASE_ENABLED && supabase) {
      setApiTokenProvider(async () => {
        const { data: sessionData } = await supabase.auth.getSession();
        let session = sessionData.session;
        const expiresAt = session?.expires_at ?? 0;
        if (session && expiresAt * 1000 < Date.now() + 60_000) {
          const { data: refreshed } = await supabase.auth.refreshSession();
          session = refreshed.session ?? session;
        }
        return session?.access_token ?? null;
      });

      // Drop any anonymous-era patient id — always bind to the logged-in user.
      localStorage.removeItem(STORAGE_KEY);

      supabase.auth.getSession().then(({ data: { session } }) => {
        if (!session) {
          setReady(true);
          return;
        }
        getPatientMe()
          .then((record) => {
            const next = patientFromRecord(record);
            writeStored(next);
            setPatientState(next);
          })
          .catch(() => setPatientState(null))
          .finally(() => setReady(true));
      });

      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((_event, session) => {
        if (!session) {
          localStorage.removeItem(STORAGE_KEY);
          setPatientState(null);
          return;
        }
        localStorage.removeItem(STORAGE_KEY);
        getPatientMe()
          .then((record) => {
            const next = patientFromRecord(record);
            writeStored(next);
            setPatientState(next);
          })
          .catch(() => setPatientState(null));
      });

      return () => subscription.unsubscribe();
    }

    setApiTokenProvider(null);
    const stored = readStored();
    if (!stored) {
      setReady(true);
      return;
    }

    getPatient(stored.id)
      .then((record) => {
        const next = patientFromRecord(record, { token: stored.token });
        writeStored(next);
        setPatientState(next);
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setPatientState(null);
      })
      .finally(() => setReady(true));
  }, []);

  const setPatient = useCallback((p: StoredPatient | null) => {
    if (p) writeStored(p);
    else localStorage.removeItem(STORAGE_KEY);
    setPatientState(p);
  }, []);

  const ensurePatient = useCallback(async () => {
    if (patient) return patient;

    if (SUPABASE_ENABLED) {
      const record = await getPatientMe();
      const next = patientFromRecord(record);
      writeStored(next);
      setPatientState(next);
      return next;
    }

    const created = await createPatient(undefined, "mr");
    const next = patientFromRecord(created, { token: created.patient_token ?? undefined });
    writeStored(next);
    setPatientState(next);
    return next;
  }, [patient]);

  const refreshPatient = useCallback(async () => {
    if (SUPABASE_ENABLED) {
      const record = await getPatientMe();
      const next = patientFromRecord(record);
      writeStored(next);
      setPatientState(next);
      return;
    }
    if (!patient?.id) return;
    const record = await getPatient(patient.id);
    const next = patientFromRecord(record, { token: patient.token });
    writeStored(next);
    setPatientState(next);
  }, [patient]);

  const clearPatient = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setPatientState(null);
  }, []);

  const value = useMemo(
    () => ({
      patient,
      ready,
      ensurePatient,
      clearPatient,
      setPatient,
      refreshPatient,
    }),
    [patient, ready, ensurePatient, clearPatient, setPatient, refreshPatient],
  );

  return <PatientContext.Provider value={value}>{children}</PatientContext.Provider>;
}

export function usePatient() {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error("usePatient must be used within PatientProvider");
  return ctx;
}
