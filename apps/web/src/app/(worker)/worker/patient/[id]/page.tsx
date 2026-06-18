"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { WorkerShell } from "@/components/layout/role-shells";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { BackLink } from "@/components/ui/back-link";
import { PageHeader } from "@/components/ui/page-header";
import { WarmCard } from "@/components/ui/warm-card";
import { createWorkerShare, getPatient } from "@/lib/api";
import type { PatientRecord } from "@/lib/types";

export default function WorkerPatientPage() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<PatientRecord | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  useEffect(() => {
    getPatient(id).then(setPatient).catch(() => setPatient(null));
  }, [id]);

  const genQr = async () => {
    const res = await createWorkerShare(id);
    setShareUrl(res.url);
  };

  return (
    <WorkerShell>
      <BackLink href="/worker" label="Patients" />
      <PageHeader title={patient?.display_name ?? "Patient"} subtitle={id} />

      <WarmCard className="flex flex-col gap-2">
        <Link href={`/upload?patient_id=${id}`}>
          <PrimaryButton>Upload report for patient</PrimaryButton>
        </Link>
        <Link href={`/triage?patient_id=${id}`}>
          <SecondaryButton>Run symptom check</SecondaryButton>
        </Link>
        <Link href={`/doctors`}>
          <SecondaryButton>Find a doctor</SecondaryButton>
        </Link>
        <Link href={`/appointments/new?patient_id=${id}`}>
          <SecondaryButton>Schedule consultation</SecondaryButton>
        </Link>
        <SecondaryButton onClick={genQr}>Generate share QR</SecondaryButton>
      </WarmCard>

      {shareUrl && (
        <p className="mt-4 break-all rounded-lg bg-[#EEF4F0] p-3 text-xs">{shareUrl}</p>
      )}
    </WorkerShell>
  );
}
