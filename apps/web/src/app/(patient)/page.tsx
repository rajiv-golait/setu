"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Camera, Lock, Calendar } from "lucide-react";
import { SecondaryButton } from "@/components/ui/buttons";
import { ConsentPanel } from "@/components/consent/consent-panel";
import { EmptyDocuments } from "@/components/ui/state-panel";
import { OfflineQueueBanner } from "@/components/ui/offline-queue-banner";
import { ConnectionBadge } from "@/components/ui/connection-badge";
import { hasLocalConsent } from "@/lib/consent";
import { listDocuments, getReminders, getPatientProfile, getPatientTimeline } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { DocumentListItem, ReminderSchedule, TimelineEvent } from "@/lib/types";
import type { PatientProfile } from "@/lib/types";

function profileCompletion(p: PatientProfile | null): number {
  if (!p) return 0;
  const fields = [p.date_of_birth, p.gender, p.blood_group, p.district, p.state];
  const filled = fields.filter(Boolean).length;
  return Math.round((filled / fields.length) * 100);
}

function docTitle(doc: DocumentListItem): string {
  const raw = doc.doc_type?.replace(/_/g, " ") ?? "Document";
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

function docMeta(doc: DocumentListItem): string {
  const date = new Date(doc.uploaded_at).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const source = doc.source === "upload" ? "Your upload" : doc.source ?? "Document";
  return `${source} · ${date}`;
}

function statusLabel(status: string): { text: string; className: string } {
  if (status === "extracted") {
    return { text: "Read", className: "bg-success-bg text-success" };
  }
  if (status === "failed") {
    return { text: "Failed", className: "bg-danger-bg text-danger" };
  }
  return { text: "Processing", className: "bg-warning-bg text-warning" };
}

const DOC_TINTS = [
  { tint: "bg-info-bg", ink: "text-info" },
  { tint: "bg-success-bg", ink: "text-primary" },
  { tint: "bg-warning-bg", ink: "text-warning" },
];

export default function HomePage() {
  const router = useRouter();
  const { patient, ready, ensurePatient } = usePatient();
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [consentOk, setConsentOk] = useState(false);
  const [reminders, setReminders] = useState<ReminderSchedule | null>(null);
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    if (patient?.id && hasLocalConsent(patient.id)) setConsentOk(true);
  }, [patient?.id]);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    setDocsLoading(true);
    listDocuments(patient.id)
      .then(setDocuments)
      .catch(() => setDocuments([]))
      .finally(() => setDocsLoading(false));
    getReminders(patient.id)
      .then(setReminders)
      .catch(() => setReminders(null));
    getPatientProfile()
      .then(setProfile)
      .catch(() => setProfile(null));
    getPatientTimeline(patient.id)
      .then((events) => setTimeline(events.slice(0, 3)))
      .catch(() => setTimeline([]));
  }, [patient?.id, ready]);

  const greetingName = patient?.displayName?.split(" ")[0] ?? "there";
  const profilePct = profileCompletion(profile);
  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  if (!ready) {
    return <div className="px-5 py-10 text-center text-sm text-text-faint">Loading…</div>;
  }

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <ConnectionBadge />
      <OfflineQueueBanner />
      <div className="mb-6 flex items-start justify-between gap-3">
        <div>
          <p className="text-[13px] text-text-muted">{today}</p>
          <h1 className="whitespace-nowrap text-2xl font-semibold tracking-tight">
            Namaste, {greetingName}
          </h1>
        </div>
        <div className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-full bg-primary text-base font-semibold text-white">
          {greetingName.slice(0, 2).toUpperCase()}
        </div>
      </div>

      {profilePct < 100 && (
        <Link
          href="/profile"
          className="mb-6 block rounded-card border border-border bg-surface-raised p-4 shadow-card"
        >
          <p className="text-sm font-semibold">Complete your health profile</p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-border">
            <div className="h-full bg-primary" style={{ width: `${profilePct}%` }} />
          </div>
          <p className="mt-1 text-xs text-text-muted">{profilePct}% complete — tap to update</p>
        </Link>
      )}

      {timeline.length > 0 && (
        <div className="mb-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
          <h2 className="text-sm font-semibold">Recent activity</h2>
          <ul className="mt-2 space-y-1.5 text-sm text-text-muted">
            {timeline.map((e, i) => (
              <li key={`${e.at}-${i}`}>· {e.title}</li>
            ))}
          </ul>
          <Link href="/timeline" className="mt-2 inline-block text-xs font-semibold text-primary">
            Full timeline →
          </Link>
        </div>
      )}

      <div className="rounded-hero border border-border bg-surface-raised p-5 shadow-raised">
        {patient?.id && !consentOk ? (
          <ConsentPanel
            patientId={patient.id}
            lang={patient.langPref ?? "mr"}
            onGranted={() => setConsentOk(true)}
          />
        ) : (
          <>
        <h2 className="text-[17px] font-semibold">Add a prescription or report</h2>
        <p className="mt-1 text-sm text-text-muted">
          Photograph it. We&apos;ll read it and keep a clear record.
        </p>
        <div className="mt-4 rounded-[14px] border-[1.5px] border-dashed border-[#C9D6CD] bg-[#F4F8F5] px-4 py-6 text-center">
          <div className="mx-auto flex h-[54px] w-[54px] items-center justify-center rounded-full bg-[#E4EFE8]">
            <Camera className="h-[26px] w-[26px] text-primary" strokeWidth={1.7} aria-hidden />
          </div>
          <p className="mt-3 text-sm text-[#3D4A42]">Place the page flat in good light</p>
        </div>
        <button
          type="button"
          aria-label="Take a photo of a document"
          onClick={async () => {
            await ensurePatient();
            router.push("/upload");
          }}
          className="mt-4 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-[13px] bg-primary py-[15px] text-base font-semibold text-white"
        >
          <Camera className="h-5 w-5" aria-hidden />
          Take a photo
        </button>
        <SecondaryButton
          className="mt-2.5"
          aria-label="Choose a document from your gallery"
          onClick={async () => {
            await ensurePatient();
            router.push("/upload");
          }}
        >
          Choose from gallery
        </SecondaryButton>
          </>
        )}
      </div>

      {reminders && reminders.reminders.length > 0 && (
        <div className="mb-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">Today</h2>
          </div>
          <ul className="mt-2 space-y-1.5 text-sm text-text-muted">
            {reminders.reminders.slice(0, 3).map((r, i) => (
              <li key={`${r.label}-${i}`}>· {r.label}</li>
            ))}
          </ul>
          <Link href="/memory" className="mt-2 inline-block text-xs font-semibold text-primary">
            View full schedule →
          </Link>
        </div>
      )}

      <div className="mb-6 flex gap-2 overflow-x-auto">
        <Link
          href="/triage"
          className="shrink-0 rounded-full border border-border bg-surface-raised px-4 py-2 text-sm font-semibold text-primary"
        >
          Check symptoms
        </Link>
        <Link
          href="/appointments"
          className="shrink-0 rounded-full border border-border bg-surface-raised px-4 py-2 text-sm font-semibold text-primary"
        >
          Book specialist
        </Link>
        <Link
          href="/vitals"
          className="shrink-0 rounded-full border border-border bg-surface-raised px-4 py-2 text-sm font-semibold text-primary"
        >
          Log vitals
        </Link>
      </div>

      <div className="mb-3 mt-2 flex items-center gap-2 px-1">
        <span className="text-[13px] font-semibold uppercase tracking-[0.06em] text-[#3D4A42]">
          Your documents
        </span>
        <div className="h-px flex-1 bg-border" />
      </div>

      {docsLoading && <p className="text-sm text-text-faint">Loading documents…</p>}

      {!docsLoading && documents.length === 0 && (
        <EmptyDocuments onUpload={async () => {
          await ensurePatient();
          router.push("/upload");
        }} />
      )}

      <div className="flex flex-col gap-2.5">
        {documents.map((doc, i) => {
          const colors = DOC_TINTS[i % DOC_TINTS.length];
          const status = statusLabel(doc.status);
          return (
            <div
              key={doc.id}
              className="flex items-center gap-3 rounded-[14px] border border-border bg-surface-raised p-3.5 shadow-card"
            >
              <div
                className={`flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-[11px] ${colors.tint}`}
              >
                <Camera className={`h-5 w-5 ${colors.ink}`} strokeWidth={1.7} aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[15px] font-semibold">{docTitle(doc)}</p>
                <p className="truncate text-[13px] text-text-muted">{docMeta(doc)}</p>
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-1 text-xs font-semibold ${status.className}`}
              >
                {status.text}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-5 flex flex-col gap-2 px-0.5">
        <div className="flex items-start gap-2 text-[13px] text-text-muted">
          <Lock className="mt-0.5 h-[15px] w-[15px] shrink-0 text-primary-light" strokeWidth={1.8} />
          <span>Your reports stay private. They&apos;re shared only when you choose to.</span>
        </div>
        <Link href="/settings" className="text-[13px] font-semibold text-primary">
          Privacy & delete my data
        </Link>
      </div>
    </div>
  );
}
