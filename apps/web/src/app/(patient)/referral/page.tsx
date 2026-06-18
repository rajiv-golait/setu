"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, FileText, UserCheck } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { ScreenHeader } from "@/components/ui/screen-header";
import { WarmCard } from "@/components/ui/warm-card";
import { createReferral, getBrief } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { DoctorBrief } from "@/lib/types";

const SPECIALTIES = [
  "General Physician",
  "Cardiologist",
  "Endocrinologist",
  "Ophthalmologist",
  "Nephrologist",
  "Orthopaedic",
  "Neurologist",
  "Psychiatrist",
];

export default function ReferralPage() {
  const router = useRouter();
  const { patient, ready } = usePatient();
  const [brief, setBrief] = useState<DoctorBrief | null>(null);
  const [specialty, setSpecialty] = useState("Endocrinologist");
  const [reason, setReason] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getBrief(patient.id).then((b) => {
      setBrief(b);
      setReason(b.referral_reason ?? b.chief_concern ?? "");
      if (b.specialist_type) setSpecialty(b.specialist_type);
    });
  }, [patient?.id, ready]);

  const submit = async () => {
    if (!patient?.id) return;
    setLoading(true);
    setError(null);
    try {
      await createReferral({ patient_id: patient.id, specialty, reason });
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't create referral");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="px-5 py-12 text-center">
        <div className="mx-auto flex h-16 w-16 animate-setu-pop items-center justify-center rounded-full bg-success-bg">
          <Check className="h-8 w-8 text-success" strokeWidth={2} />
        </div>
        <h1 className="mt-4 text-xl font-semibold">Referral created</h1>
        <p className="mt-1 text-text-muted">Sent for {specialty}</p>
        <p className="mt-3 text-sm text-text-muted">{reason}</p>
        <PrimaryButton className="mt-8" onClick={() => router.push("/share")}>
          Share referral link
        </PrimaryButton>
        <SecondaryButton className="mt-2.5" onClick={() => router.push("/brief")}>
          Done
        </SecondaryButton>
      </div>
    );
  }

  return (
    <div className="px-5 pb-8 pt-5">
      <ScreenHeader
        title="Specialist referral"
        subtitle="Share your brief with a specialist — your doctor-ready summary goes with it."
      />

      <p className="mb-5 flex items-center gap-2 text-sm text-text-muted">
        <UserCheck className="h-[18px] w-[18px] shrink-0 text-primary-light" strokeWidth={1.8} />
        Suggested <strong className="font-semibold text-text">{specialty}</strong> based on your latest labs
      </p>

      {brief && (
        <WarmCard variant="inset" className="mb-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-[#EEF4F0]">
              <FileText className="h-5 w-5 text-primary" strokeWidth={1.7} aria-hidden />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-label text-primary-light">
                Attached brief
              </p>
              <p className="mt-1 text-[15px] font-semibold leading-snug">{brief.one_line}</p>
              <p className="mt-1 text-sm text-text-muted line-clamp-2">{brief.chief_concern}</p>
              {brief.source_documents.length > 0 && (
                <p className="mt-2 text-xs text-text-faint">
                  {brief.source_documents.length} source document
                  {brief.source_documents.length === 1 ? "" : "s"}
                </p>
              )}
            </div>
          </div>
        </WarmCard>
      )}

      <label className="font-display text-sm font-semibold text-text">
        Which specialist?
      </label>
      <div className="mt-2 flex flex-col gap-1.5">
        {SPECIALTIES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSpecialty(s)}
            className={`flex items-center justify-between rounded-[11px] border px-3.5 py-3 text-left text-[15px] ${
              specialty === s
                ? "border-primary bg-[#EEF4F0] font-semibold text-primary"
                : "border-border bg-surface-raised"
            }`}
          >
            {s}
            {specialty === s && <Check className="h-4 w-4" />}
          </button>
        ))}
      </div>

      <label className="mt-6 block font-display text-sm font-semibold text-text">
        Reason for referral
      </label>
      <textarea
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        rows={4}
        className="mt-2 w-full resize-none rounded-card border border-border bg-surface-raised p-3.5 text-base outline-none focus:border-primary-light"
      />

      {error && (
        <div className="mt-3 rounded-card border border-danger-border bg-danger-bg p-3 text-sm text-danger">
          {error}
          <button type="button" onClick={submit} className="ml-2 font-semibold underline">
            Try again
          </button>
        </div>
      )}

      <PrimaryButton className="mt-6" disabled={loading || !reason.trim()} onClick={submit}>
        Create referral
      </PrimaryButton>
    </div>
  );
}
