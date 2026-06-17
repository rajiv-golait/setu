"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DoctorShell } from "@/components/layout/role-shells";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { VideoConsult } from "@/components/doctor/video-consult";
import { ConsultSidebar } from "@/components/doctor/consult-sidebar";
import {
  addEncounterNote,
  addEncounterPrescription,
  completeEncounter,
  draftEncounterSummary,
  getEncounter,
} from "@/lib/api";
import { PrescriptionBuilder } from "@/components/doctor/prescription-builder";

export default function DoctorConsultationPage() {
  const { id } = useParams<{ id: string }>();
  const [note, setNote] = useState("");
  const [room, setRoom] = useState<string | null>(null);
  const [patientId, setPatientId] = useState<string | null>(null);
  const [appointmentId, setAppointmentId] = useState<string | null>(null);
  const [drafting, setDrafting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getEncounter(id)
      .then((enc) => {
        setPatientId(enc.patient_id);
        setRoom(enc.consult_room ?? null);
        setAppointmentId(enc.appointment_id ?? null);
        setStatus(enc.status);
      })
      .catch(() => null);
  }, [id]);

  const saveNote = async () => {
    if (!id || !note.trim()) return;
    await addEncounterNote(id, { note_type: "plan", body: note });
    setNote("");
  };

  const generateDraft = async () => {
    if (!id) return;
    setDrafting(true);
    try {
      const res = await draftEncounterSummary(id);
      setNote(res.body);
    } finally {
      setDrafting(false);
    }
  };

  const finish = async () => {
    if (!id) return;
    await completeEncounter(id);
    setStatus("completed");
  };

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Consultation</h1>
      {status && <p className="mt-1 text-sm capitalize text-text-muted">Status: {status}</p>}
      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        <div>
          {room && (
            <VideoConsult
              roomName={room}
              joinLabel="Join video"
              appointmentId={appointmentId ?? undefined}
            />
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <SecondaryButton onClick={generateDraft} disabled={drafting}>
              {drafting ? "Drafting…" : "AI draft summary"}
            </SecondaryButton>
            {status !== "completed" && (
              <PrimaryButton onClick={finish}>Complete consult</PrimaryButton>
            )}
          </div>
          <label className="mt-4 block text-sm font-semibold">Clinical notes</label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={5}
            className="mt-2 w-full rounded-card border border-border px-4 py-3"
            placeholder="Assessment and plan — review AI drafts before saving."
          />
          <PrimaryButton className="mt-3" onClick={saveNote}>
            Save note
          </PrimaryButton>
          <PrescriptionBuilder
            onSave={async (items) => {
              if (!id) return;
              await addEncounterPrescription(id, items);
            }}
          />
        </div>
        {patientId && <ConsultSidebar patientId={patientId} />}
      </div>
      <Link href="/doctor" className="mt-6 inline-block text-sm font-semibold text-primary">
        Back to dashboard
      </Link>
    </DoctorShell>
  );
}
