"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { updatePatientMe } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";
import { cn } from "@/lib/cn";

const LANGS = [
  { id: "mr" as const, label: "मराठी", sub: "Marathi" },
  { id: "hi" as const, label: "हिंदी", sub: "Hindi" },
  { id: "en" as const, label: "English", sub: "English" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { patient, ready, ensurePatient, refreshPatient } = usePatient();
  const [lang, setLang] = useState<(typeof LANGS)[number]["id"]>("mr");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (SUPABASE_ENABLED && ready && !patient) {
      ensurePatient().catch(() => undefined);
    }
  }, [ready, patient, ensurePatient]);

  useEffect(() => {
    if (patient?.onboardingCompleted) {
      router.replace("/");
    } else if (patient?.langPref) {
      const pref = patient.langPref as (typeof LANGS)[number]["id"];
      if (LANGS.some((l) => l.id === pref)) setLang(pref);
    }
  }, [patient, router]);

  const save = async () => {
    setLoading(true);
    try {
      await ensurePatient();
      await updatePatientMe({ lang_pref: lang, onboarding_completed: true });
      await refreshPatient();
      router.replace("/");
    } finally {
      setLoading(false);
    }
  };

  if (!ready) {
    return <div className="p-8 text-center text-text-faint">Loading…</div>;
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-10 animate-setu-fade">
      <h1 className="text-[26px] font-semibold">Choose your language</h1>
      <p className="mt-2 text-sm text-text-muted">भाषा निवडा · भाषा चुनें</p>

      <div className="mt-8 space-y-3">
        {LANGS.map((l) => (
          <button
            key={l.id}
            type="button"
            onClick={() => setLang(l.id)}
            className={cn(
              "flex w-full items-center justify-between rounded-card border px-4 py-4 text-left",
              lang === l.id
                ? "border-primary bg-[#EEF4F0] shadow-card"
                : "border-border bg-surface-raised",
            )}
          >
            <span className="text-lg font-semibold">{l.label}</span>
            <span className="text-sm text-text-muted">{l.sub}</span>
          </button>
        ))}
      </div>

      <PrimaryButton className="mt-8" disabled={loading} onClick={save}>
        {loading ? "Saving…" : "Continue"}
      </PrimaryButton>
    </div>
  );
}
