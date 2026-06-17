"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { VideoConsult } from "@/components/doctor/video-consult";
import { listAppointments, patchAppointment } from "@/lib/api";
import { SecondaryButton } from "@/components/ui/buttons";
import type { Appointment } from "@/lib/types";

export default function PatientAppointmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAppointments()
      .then((list) => setAppt(list.find((a) => a.id === id) ?? null))
      .finally(() => setLoading(false));
  }, [id]);

  const act = async (action: string) => {
    if (!appt) return;
    const updated = await patchAppointment(appt.id, action);
    setAppt(updated);
  };

  if (loading) return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  if (!appt) return <p className="p-8 text-center text-sm text-danger">Appointment not found</p>;

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-4">
      <button
        type="button"
        onClick={() => router.back()}
        className="mb-4 flex items-center gap-2 text-sm font-semibold text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <h1 className="text-xl font-semibold">{appt.specialty}</h1>
      <p className="mt-1 capitalize text-sm text-text-muted">Status: {appt.status}</p>

      {appt.consult_room && (
        <VideoConsult roomName={appt.consult_room} joinLabel="Join video consultation" />
      )}

      {appt.status === "accepted" && (
        <SecondaryButton className="mt-4" onClick={() => act("confirm")}>
          Confirm attendance
        </SecondaryButton>
      )}
      {["requested", "accepted", "confirmed"].includes(appt.status) && (
        <SecondaryButton className="mt-2" onClick={() => act("cancel")}>
          Cancel
        </SecondaryButton>
      )}
    </div>
  );
}
