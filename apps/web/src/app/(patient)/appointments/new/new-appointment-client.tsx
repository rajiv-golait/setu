"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { BackLink } from "@/components/ui/back-link";
import { PageHeader } from "@/components/ui/page-header";
import { createAppointment } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import { useLocale } from "@/lib/hooks/use-locale";

const SPECIALTIES = [
  "Endocrinologist",
  "Cardiologist",
  "Dermatologist",
  "General physician",
  "Gynecologist",
  "Pediatrician",
];

export default function NewAppointmentClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const triageId = searchParams.get("triage_id") ?? undefined;
  const patientIdParam = searchParams.get("patient_id") ?? undefined;
  const providerId = searchParams.get("provider_id") ?? undefined;
  const slotId = searchParams.get("slot_id") ?? undefined;
  const { patient, ensurePatient } = usePatient();
  const { t } = useLocale();
  const [specialty, setSpecialty] = useState(SPECIALTIES[0]);
  const [scheduledFor, setScheduledFor] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const p = patient ?? (await ensurePatient());
      await createAppointment({
        patient_id: patientIdParam ?? p.id,
        specialty,
        scheduled_for: scheduledFor ? new Date(scheduledFor).toISOString() : undefined,
        triage_id: triageId,
        notes: notes || undefined,
        provider_id: providerId,
        slot_id: slotId,
      });
      router.push("/appointments");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Booking failed");
      setLoading(false);
    }
  };

  return (
    <div className="px-5 pb-8 pt-4">
      <BackLink />
      <PageHeader
        title={t("appointments.book")}
        subtitle="Your doctor brief is attached to the request automatically."
      />

      <label className="mt-6 block text-sm font-semibold">Specialist type</label>
      <select
        value={specialty}
        onChange={(e) => setSpecialty(e.target.value)}
        className="mt-2 w-full rounded-card border border-border bg-surface-raised px-4 py-3"
      >
        {SPECIALTIES.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      <label className="mt-5 block text-sm font-semibold">Preferred date & time (optional)</label>
      <input
        type="datetime-local"
        value={scheduledFor}
        onChange={(e) => setScheduledFor(e.target.value)}
        className="mt-2 w-full rounded-card border border-border px-4 py-3"
      />

      <label className="mt-5 block text-sm font-semibold">Notes for the doctor</label>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        rows={3}
        className="mt-2 w-full rounded-card border border-border px-4 py-3 text-sm"
        placeholder="Brief reason for visit…"
      />

      <PrimaryButton className="mt-6" disabled={loading} onClick={submit}>
        {loading ? "Booking…" : "Request consultation"}
      </PrimaryButton>
    </div>
  );
}
