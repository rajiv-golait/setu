"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { AuthBrand } from "@/components/auth/auth-brand";
import { LanguagePicker } from "@/components/profile/language-picker";
import { updatePatientMe } from "@/lib/api";
import { isPatientLang, type PatientLang } from "@/lib/constants/langs";
import { usePatient } from "@/lib/hooks/use-patient";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";

export default function OnboardingPage() {
  const router = useRouter();
  const { patient, ready, ensurePatient, refreshPatient } = usePatient();
  const [lang, setLang] = useState<PatientLang>("mr");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (SUPABASE_ENABLED && ready && !patient) {
      ensurePatient().catch(() => undefined);
    }
  }, [ready, patient, ensurePatient]);

  useEffect(() => {
    if (patient?.onboardingCompleted) {
      router.replace("/");
    } else if (patient?.langPref && isPatientLang(patient.langPref)) {
      setLang(patient.langPref);
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
      <AuthBrand
        badge="Setu · Patient"
        title="Choose your language"
        subtitle="Menus, Saathi, and summaries will use this language. You can change it anytime in your profile."
      />

      <div className="mt-2">
        <LanguagePicker value={lang} onChange={setLang} disabled={loading} />
      </div>

      <PrimaryButton className="mt-8" disabled={loading} onClick={save}>
        {loading ? "Saving…" : "Continue"}
      </PrimaryButton>
    </div>
  );
}
