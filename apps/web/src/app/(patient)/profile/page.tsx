"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Share2, Shield } from "lucide-react";
import { LanguagePicker } from "@/components/profile/language-picker";
import { PrimaryButton } from "@/components/ui/buttons";
import { ErrorPanel } from "@/components/ui/state-panel";
import { getPatientProfile, updatePatientMe, updatePatientProfile } from "@/lib/api";
import { isPatientLang, type PatientLang } from "@/lib/constants/langs";
import { useLocale } from "@/lib/hooks/use-locale";
import { usePatient } from "@/lib/hooks/use-patient";
import type { PatientProfile } from "@/lib/types";

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function PatientProfilePage() {
  const { t } = useLocale();
  const { patient, ready, refreshPatient } = usePatient();

  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [displayName, setDisplayName] = useState("");
  const [lang, setLang] = useState<PatientLang>("mr");
  const [langSaving, setLangSaving] = useState(false);
  const [langSaved, setLangSaved] = useState(false);

  const [gender, setGender] = useState("");
  const [bloodGroup, setBloodGroup] = useState("");
  const [district, setDistrict] = useState("");
  const [stateVal, setStateVal] = useState("");
  const [allergies, setAllergies] = useState("");
  const [conditions, setConditions] = useState("");
  const [healthSaving, setHealthSaving] = useState(false);
  const [healthSaved, setHealthSaved] = useState(false);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const p = await getPatientProfile();
      setProfile(p);
      setGender(p.gender ?? "");
      setBloodGroup(p.blood_group ?? "");
      setDistrict(p.district ?? "");
      setStateVal(p.state ?? "");
      setAllergies((p.allergies_known ?? []).join(", "));
      setConditions((p.chronic_conditions ?? []).join(", "));
    } catch (e) {
      setProfile(null);
      setLoadError(e instanceof Error ? e.message : "Could not load profile");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (patient?.displayName) setDisplayName(patient.displayName);
    if (patient?.langPref && isPatientLang(patient.langPref)) {
      setLang(patient.langPref);
    }
  }, [ready, patient?.displayName, patient?.langPref]);

  useEffect(() => {
    if (!ready) return;
    void loadProfile();
  }, [ready, loadProfile]);

  const saveLanguage = async (next: PatientLang) => {
    if (next === lang || langSaving) return;
    setLang(next);
    setLangSaving(true);
    setLangSaved(false);
    try {
      await updatePatientMe({ lang_pref: next, onboarding_completed: true });
      await refreshPatient();
      setLangSaved(true);
      setTimeout(() => setLangSaved(false), 2500);
    } catch {
      if (patient?.langPref && isPatientLang(patient.langPref)) setLang(patient.langPref);
    } finally {
      setLangSaving(false);
    }
  };

  const saveHealth = async () => {
    setHealthSaving(true);
    setHealthSaved(false);
    try {
      if (displayName.trim()) {
        await updatePatientMe({ display_name: displayName.trim() });
        await refreshPatient();
      }
      const updated = await updatePatientProfile({
        gender: gender || undefined,
        blood_group: bloodGroup || undefined,
        district: district || undefined,
        state: stateVal || undefined,
        allergies_known: splitList(allergies),
        chronic_conditions: splitList(conditions),
      });
      setProfile(updated);
      setHealthSaved(true);
      setTimeout(() => setHealthSaved(false), 2500);
    } finally {
      setHealthSaving(false);
    }
  };

  if (!ready || loading) {
    return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  }

  if (loadError) {
    return (
      <div className="animate-setu-fade px-5 pb-24 pt-5">
        <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
          <ChevronLeft className="h-4 w-4" aria-hidden />
          {t("profile.back")}
        </Link>
        <ErrorPanel title={t("profile.loadError")} message={loadError} />
        <PrimaryButton className="mt-4" onClick={() => void loadProfile()}>
          {t("profile.retry")}
        </PrimaryButton>
      </div>
    );
  }

  return (
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <h1 className="text-[23px] font-semibold tracking-tight">{t("profile.pageTitle")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("profile.pageSubtitle")}</p>

      <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
        <h2 className="text-sm font-semibold">{t("profile.language.title")}</h2>
        <p className="mt-1 text-sm text-text-muted">{t("profile.language.subtitle")}</p>
        <div className="mt-4">
          <LanguagePicker value={lang} onChange={(l) => void saveLanguage(l)} disabled={langSaving} />
        </div>
        {langSaved && (
          <p className="mt-3 text-sm text-success">{t("profile.language.saved")}</p>
        )}
      </section>

      <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
        <h2 className="text-sm font-semibold">{t("profile.health.title")}</h2>
        <p className="mt-1 text-sm text-text-muted">{t("profile.subtitle")}</p>

        <div className="mt-4 space-y-4">
          <label className="block text-sm font-semibold">
            {t("profile.displayName")}
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder={t("profile.displayName.placeholder")}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 text-base font-normal"
            />
          </label>

          <label className="block text-sm font-semibold">
            {t("profile.gender")}
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 font-normal"
            >
              <option value="">{t("profile.gender.preferNot")}</option>
              <option value="female">{t("profile.gender.female")}</option>
              <option value="male">{t("profile.gender.male")}</option>
              <option value="other">{t("profile.gender.other")}</option>
            </select>
          </label>

          <label className="block text-sm font-semibold">
            {t("profile.bloodGroup")}
            <input
              value={bloodGroup}
              onChange={(e) => setBloodGroup(e.target.value)}
              placeholder={t("profile.bloodGroup.placeholder")}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 font-normal"
            />
          </label>

          <label className="block text-sm font-semibold">
            {t("profile.district")}
            <input
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 font-normal"
            />
          </label>

          <label className="block text-sm font-semibold">
            {t("profile.state")}
            <input
              value={stateVal}
              onChange={(e) => setStateVal(e.target.value)}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 font-normal"
            />
          </label>

          <label className="block text-sm font-semibold">
            {t("profile.allergies")}
            <input
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 font-normal"
            />
          </label>

          <label className="block text-sm font-semibold">
            {t("profile.conditions")}
            <input
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              className="mt-1 w-full rounded-card border border-border bg-surface px-4 py-3 font-normal"
            />
          </label>

          <PrimaryButton disabled={healthSaving} onClick={() => void saveHealth()}>
            {healthSaving ? "…" : t("profile.save")}
          </PrimaryButton>
          {healthSaved && <p className="text-sm text-success">{t("profile.saved")}</p>}
        </div>
      </section>

      <section className="mt-6 space-y-2">
        <Link
          href="/share"
          className="flex items-center justify-between rounded-card border border-border bg-surface-raised px-4 py-3.5 shadow-card"
        >
          <span className="flex items-center gap-3 text-sm font-semibold">
            <Share2 className="h-4 w-4 text-primary" aria-hidden />
            {t("profile.share")}
          </span>
          <ChevronRight className="h-4 w-4 text-text-faint" aria-hidden />
        </Link>
        <Link
          href="/settings"
          className="flex items-center justify-between rounded-card border border-border bg-surface-raised px-4 py-3.5 shadow-card"
        >
          <span className="flex items-center gap-3 text-sm font-semibold">
            <Shield className="h-4 w-4 text-primary" aria-hidden />
            {t("profile.privacy")}
          </span>
          <ChevronRight className="h-4 w-4 text-text-faint" aria-hidden />
        </Link>
      </section>

      {profile && (
        <p className="mt-6 text-center text-xs text-text-faint">ID · {profile.patient_id}</p>
      )}
    </div>
  );
}
