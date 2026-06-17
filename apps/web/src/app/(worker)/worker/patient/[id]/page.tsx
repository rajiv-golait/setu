"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { WorkerShell } from "@/components/layout/role-shells";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
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
      <Link href="/worker" className="text-sm font-semibold text-primary">
        ← Patients
      </Link>
      <h1 className="mt-4 text-xl font-semibold">
        {patient?.display_name ?? "Patient"}
      </h1>
      <p className="text-sm text-text-muted">{id}</p>

      <div className="mt-6 flex flex-col gap-2">
        <Link href={`/upload?patient_id=${id}`}>
          <PrimaryButton>Upload report for patient</PrimaryButton>
        </Link>
        <Link href={`/triage?patient_id=${id}`}>
          <SecondaryButton>Run symptom check</SecondaryButton>
        </Link>
        <Link href={`/appointments/new?patient_id=${id}`}>
          <SecondaryButton>Schedule consultation</SecondaryButton>
        </Link>
        <SecondaryButton onClick={genQr}>Generate share QR</SecondaryButton>
      </div>

      {shareUrl && (
        <p className="mt-4 break-all rounded-lg bg-[#EEF4F0] p-3 text-xs">{shareUrl}</p>
      )}
    </WorkerShell>
  );
}
