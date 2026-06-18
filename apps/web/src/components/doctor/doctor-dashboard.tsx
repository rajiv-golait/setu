"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Video } from "lucide-react";
import { RequestQueueCard } from "@/components/doctor/request-queue-card";
import { DoctorStatPills } from "@/components/doctor/doctor-stat-pills";
import { SectionHeading } from "@/components/ui/section-heading";
import { ScreenHeader } from "@/components/ui/screen-header";
import { FlushList, FlushListItem } from "@/components/ui/data-table";
import { formatDoctorName, formatWhen, isToday, patientLabel } from "@/lib/doctor-utils";
import {
  getProviderDashboard,
  getProviderMe,
  listAppointments,
  listEncountersForPatient,
  listProviderPatients,
  doctorAppointmentAction,
} from "@/lib/api";
import type { Appointment, Encounter, ProviderDashboard, ProviderRecord } from "@/lib/types";

type FollowUpRow = Encounter & { patient_label: string };

export default function DoctorDashboardView() {
  const [provider, setProvider] = useState<ProviderRecord | null>(null);
  const [dash, setDash] = useState<ProviderDashboard | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [followUps, setFollowUps] = useState<FollowUpRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    getProviderDashboard().then(setDash).catch(() => setDash(null));
    listAppointments()
      .then(setAppointments)
      .catch(() => setAppointments([]));
  }, []);

  useEffect(() => {
    getProviderMe()
      .then((p) => {
        setProvider(p);
        if (p.verification_status && p.verification_status !== "approved") {
          window.location.href = "/doctor/pending";
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Not a provider"));
    refresh();
  }, [refresh]);

  useEffect(() => {
    (async () => {
      try {
        const patients = await listProviderPatients();
        const nested = await Promise.all(
          patients.map(async (p) => {
            const encs = await listEncountersForPatient(p.id).catch(() => []);
            return encs
              .filter((e) => e.status === "open")
              .map((e) => ({
                ...e,
                patient_label: p.display_name || p.id.slice(0, 8),
              }));
          }),
        );
        setFollowUps(nested.flat().slice(0, 5));
      } catch {
        setFollowUps([]);
      }
    })();
  }, [appointments]);

  const requested = useMemo(
    () => appointments.filter((a) => a.status === "requested"),
    [appointments],
  );

  const todaySchedule = useMemo(
    () =>
      appointments.filter(
        (a) =>
          ["accepted", "confirmed"].includes(a.status) &&
          isToday(a.scheduled_for ?? a.requested_at),
      ),
    [appointments],
  );

  const handleAccept = async (id: string) => {
    setBusyId(id);
    setError(null);
    try {
      const updated = await doctorAppointmentAction(id, "accept");
      setAppointments((prev) => prev.map((a) => (a.id === id ? updated : a)));
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not accept request");
      refresh();
    } finally {
      setBusyId(null);
    }
  };

  const handleDecline = async (id: string, reason: string) => {
    setBusyId(id);
    setError(null);
    try {
      const updated = await doctorAppointmentAction(id, "decline", { reason });
      setAppointments((prev) => prev.map((a) => (a.id === id ? updated : a)));
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not decline request");
      refresh();
    } finally {
      setBusyId(null);
    }
  };

  const todayLabel = new Date().toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <ScreenHeader
          title={formatDoctorName(provider?.display_name)}
          subtitle={provider?.specialty ?? undefined}
        />
        <p className="text-sm font-medium text-text-muted">{todayLabel}</p>
      </div>

      {error && <p className="mt-2 text-sm text-danger">{error}</p>}

      {provider?.verification_status && provider.verification_status !== "approved" && (
        <div className="mt-4 rounded-card border border-warning-border bg-warning-bg p-4 text-sm">
          Account status:{" "}
          <span className="font-semibold capitalize">{provider.verification_status}</span>.
          Complete onboarding or wait for admin approval.{" "}
          <Link href="/doctor/onboarding" className="font-semibold text-primary">
            Onboarding →
          </Link>
        </div>
      )}

      <div className="mt-6">
        <DoctorStatPills dash={dash} pendingFallback={requested.length} />
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-5">
        <section className="lg:col-span-3">
          <SectionHeading title="Incoming requests" />
          {requested.length === 0 ? (
            <p className="rounded-card border border-dashed border-border bg-surface p-6 text-center text-sm text-text-muted">
              No pending consultation requests. New patient bookings will appear here.
            </p>
          ) : (
            <div className="space-y-3">
              {requested.map((a) => (
                <RequestQueueCard
                  key={a.id}
                  appt={a}
                  busy={busyId === a.id}
                  onAccept={() => handleAccept(a.id)}
                  onDecline={(reason) => handleDecline(a.id, reason)}
                />
              ))}
            </div>
          )}
        </section>

        <aside className="space-y-8 lg:col-span-2">
          <section>
            <SectionHeading title="Today's schedule" />
            {todaySchedule.length === 0 ? (
              <p className="text-sm text-text-muted">No consultations scheduled for today.</p>
            ) : (
              <FlushList className="mt-2 rounded-card border border-border bg-surface-raised px-4">
                {todaySchedule.map((a) => (
                  <FlushListItem key={a.id}>
                    <p className="font-semibold">{patientLabel(a)}</p>
                    <p className="text-sm text-text-muted">
                      {a.specialty} · {formatWhen(a.scheduled_for ?? a.requested_at)}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {a.consult_room && (
                        <Link
                          href={`/doctor/appointments/${a.id}`}
                          className="inline-flex items-center gap-1 text-sm font-semibold text-primary"
                        >
                          <Video className="h-4 w-4" /> Join
                        </Link>
                      )}
                      <Link
                        href={`/doctor/appointments/${a.id}`}
                        className="text-sm font-semibold text-primary"
                      >
                        Open case
                      </Link>
                    </div>
                  </FlushListItem>
                ))}
              </FlushList>
            )}
          </section>

          <section>
            <SectionHeading title="Follow-ups due" />
            {followUps.length === 0 ? (
              <p className="text-sm text-text-muted">No open follow-ups.</p>
            ) : (
              <FlushList className="mt-2">
                {followUps.map((e) => (
                  <FlushListItem key={e.id}>
                    <Link
                      href={`/doctor/consultations/${e.id}`}
                      className="block text-sm"
                    >
                      <p className="font-semibold">{e.patient_label}</p>
                      <p className="capitalize text-text-muted">{e.encounter_type}</p>
                    </Link>
                  </FlushListItem>
                ))}
              </FlushList>
            )}
            {(dash?.follow_ups_due ?? 0) > followUps.length && (
              <Link href="/doctor/consultations" className="mt-2 inline-block text-sm font-semibold text-primary">
                View all →
              </Link>
            )}
          </section>
        </aside>
      </div>

      <p className="mt-8 rounded-lg bg-[#F8F7F2] px-3 py-2 text-xs text-text-muted">
        Prepared summaries for practitioner review — not a diagnosis. Clinical decisions remain
        with the treating doctor.
      </p>
    </div>
  );
}
