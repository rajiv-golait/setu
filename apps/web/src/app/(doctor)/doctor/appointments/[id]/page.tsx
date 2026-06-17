"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DoctorShell } from "@/components/layout/role-shells";
import { VideoConsult } from "@/components/doctor/video-consult";
import { listAppointments, patchAppointment } from "@/lib/api";
import { SecondaryButton } from "@/components/ui/buttons";
import type { Appointment } from "@/lib/types";

export default function DoctorAppointmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [appt, setAppt] = useState<Appointment | null>(null);

  useEffect(() => {
    listAppointments().then((list) => setAppt(list.find((a) => a.id === id) ?? null));
  }, [id]);

  const act = async (action: string) => {
    if (!appt) return;
    const updated = await patchAppointment(appt.id, action);
    setAppt(updated);
  };

  return (
    <DoctorShell>
      {!appt ? (
        <p className="text-sm text-text-muted">Loading…</p>
      ) : (
        <>
          <Link href="/doctor/appointments" className="text-sm font-semibold text-primary">
            ← Back
          </Link>
          <h1 className="mt-4 text-xl font-semibold">{appt.specialty}</h1>
          <p className="text-sm text-text-muted">Patient {appt.patient_id}</p>
          <p className="mt-1 capitalize text-sm">Status: {appt.status}</p>

          {appt.status === "requested" && (
            <div className="mt-4 flex gap-2">
              <SecondaryButton onClick={() => act("accept")}>Accept</SecondaryButton>
              <SecondaryButton onClick={() => act("decline")}>Decline</SecondaryButton>
            </div>
          )}

          {appt.consult_room && (
            <VideoConsult
              roomName={appt.consult_room}
              joinLabel="Start video consultation"
              onJoin={() => act("confirm").catch(() => undefined)}
            />
          )}

          {appt.status === "accepted" || appt.status === "confirmed" ? (
            <SecondaryButton className="mt-4" onClick={() => act("complete")}>
              Mark completed
            </SecondaryButton>
          ) : null}
        </>
      )}
    </DoctorShell>
  );
}
