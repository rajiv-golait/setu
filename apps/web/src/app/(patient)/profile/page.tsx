"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { getPatientProfile, updatePatientProfile } from "@/lib/api";
import { useLocale } from "@/lib/hooks/use-locale";
import type { PatientProfile } from "@/lib/types";

export default function PatientProfilePage() {
  const { t } = useLocale();
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [gender, setGender] = useState("");
  const [bloodGroup, setBloodGroup] = useState("");
  const [district, setDistrict] = useState("");
  const [state, setState] = useState("");
  const [allergies, setAllergies] = useState("");
  const [conditions, setConditions] = useState("");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPatientProfile()
      .then((p) => {
        setProfile(p);
        setGender(p.gender ?? "");
        setBloodGroup(p.blood_group ?? "");
        setDistrict(p.district ?? "");
        setState(p.state ?? "");
        setAllergies((p.allergies_known ?? []).join(", "));
        setConditions((p.chronic_conditions ?? []).join(", "));
      })
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    const updated = await updatePatientProfile({
      gender: gender || undefined,
      blood_group: bloodGroup || undefined,
      district: district || undefined,
      state: state || undefined,
      allergies_known: allergies
        ? allergies.split(",").map((s) => s.trim()).filter(Boolean)
        : [],
      chronic_conditions: conditions
        ? conditions.split(",").map((s) => s.trim()).filter(Boolean)
        : [],
    });
    setProfile(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading) {
    return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  }

  return (
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
        <ChevronLeft className="h-4 w-4" aria-hidden />
        Back
      </Link>
      <h1 className="text-[23px] font-semibold">{t("profile.title")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("profile.subtitle")}</p>

      <div className="mt-6 space-y-4">
        <label className="block text-sm font-semibold">
          Gender
          <select
            value={gender}
            onChange={(e) => setGender(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          >
            <option value="">Prefer not to say</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="block text-sm font-semibold">
          Blood group
          <input
            value={bloodGroup}
            onChange={(e) => setBloodGroup(e.target.value)}
            placeholder="e.g. B+"
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          District
          <input
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          State
          <input
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Known allergies (comma-separated)
          <input
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Chronic conditions (comma-separated)
          <input
            value={conditions}
            onChange={(e) => setConditions(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <PrimaryButton onClick={save}>{t("profile.save")}</PrimaryButton>
        {saved && <p className="text-sm text-success">Saved.</p>}
        {profile && (
          <p className="text-xs text-text-faint">Patient ID: {profile.patient_id}</p>
        )}
      </div>
    </div>
  );
}
