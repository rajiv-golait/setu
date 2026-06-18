"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Lock, Sparkles, X } from "lucide-react";
import { ConsentPanel } from "@/components/consent/consent-panel";
import { OfflineQueueBanner } from "@/components/ui/offline-queue-banner";
import { ConnectionBadge } from "@/components/ui/connection-badge";
import { LabSparkline } from "@/components/ui/sparkline";
import { ScreenHeader } from "@/components/ui/screen-header";
import {
  EmptyInvite,
  MedRow,
  SlotRow,
  TodaySection,
} from "@/components/patient/today-primitives";
import { ReminderOptIn } from "@/components/reminders/reminder-opt-in";
import { hasLocalConsent, markLocalConsent } from "@/lib/consent";
import { getConsentStatus, getReminders, getVitalsSummary, listVitals } from "@/lib/api";
import { useLiveMemory } from "@/lib/hooks/use-live-memory";
import { markTakenToday } from "@/lib/med-acks";
import { pushSaathiMessage } from "@/lib/saathi-history";
import { computeDriftNudge } from "@/lib/drift";
import { usePatient } from "@/lib/hooks/use-patient";
import type {
  ReminderItem,
  ReminderSchedule,
  VitalReading,
  VitalsSummary,
  VitalType,
} from "@/lib/types";

type Slot = "morning" | "afternoon" | "night";

function slotForTime(t: string): Slot {
  const s = t.toLowerCase();
  if (s.includes("morning") || s.includes("सकाळ") || s.includes("सुबह")) return "morning";
  if (s.includes("after") || s.includes("noon") || s.includes("दुपार") || s.includes("दोपहर")) return "afternoon";
  return "night";
}

function vitalSeries(readings: VitalReading[], type: VitalType): number[] {
  return readings
    .filter((r) => r.vital_type === type)
    .sort((a, b) => a.measured_at.localeCompare(b.measured_at))
    .map((r) => {
      const v = r.value;
      if (type === "blood_pressure" && typeof v.systolic === "number") return v.systolic;
      if (type === "blood_sugar" && typeof v.fasting === "number") return v.fasting;
      return 0;
    })
    .filter((n) => n > 0);
}

export default function TodayPage() {
  const router = useRouter();
  const { patient, ready, ensurePatient } = usePatient();
  const [consentOk, setConsentOk] = useState(false);
  const [consentReady, setConsentReady] = useState(false);
  const [reminders, setReminders] = useState<ReminderSchedule | null>(null);
  const [vitalsSummary, setVitalsSummary] = useState<VitalsSummary | null>(null);
  const [vitals, setVitals] = useState<VitalReading[]>([]);
  const [acks, setAcks] = useState(0); // bump to re-render after marking taken
  const [driftDismissed, setDriftDismissed] = useState(false);
  const driftPushedRef = useRef(false);

  const { truth, newMed, dismissNewMed } = useLiveMemory(consentOk && patient?.id ? patient.id : null);

  useEffect(() => {
    if (!patient?.id) {
      setConsentReady(true);
      return;
    }
    if (hasLocalConsent(patient.id)) {
      setConsentOk(true);
      setConsentReady(true);
      return;
    }
    setConsentReady(false);
    getConsentStatus(patient.id)
      .then((status) => {
        if (status.granted) {
          markLocalConsent(patient.id);
          setConsentOk(true);
        }
      })
      .catch(() => {})
      .finally(() => setConsentReady(true));
  }, [patient?.id]);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getReminders(patient.id).then(setReminders).catch(() => setReminders(null));
    getVitalsSummary(patient.id).then(setVitalsSummary).catch(() => setVitalsSummary(null));
    listVitals(patient.id).then(setVitals).catch(() => setVitals([]));
  }, [patient?.id, ready]);

  const greetingName = patient?.displayName?.split(" ")[0] ?? "there";
  const today = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });

  const meds = useMemo(
    () => (truth?.entries ?? []).filter((e) => e.entry_type === "medication"),
    [truth],
  );

  // Group reminders into morning / afternoon / night.
  const slots = useMemo(() => {
    const out: Record<Slot, ReminderItem[]> = { morning: [], afternoon: [], night: [] };
    for (const r of reminders?.reminders ?? []) {
      const times = r.times_of_day?.length ? r.times_of_day : ["night"];
      const seen = new Set<Slot>();
      for (const t of times) {
        const slot = slotForTime(t);
        if (!seen.has(slot)) {
          out[slot].push(r);
          seen.add(slot);
        }
      }
    }
    return out;
  }, [reminders]);

  // Pick one real trend: prefer sugar, else BP — only if ≥2 real readings exist.
  const sugar = vitalSeries(vitals, "blood_sugar");
  const bp = vitalSeries(vitals, "blood_pressure");
  const trend =
    sugar.length >= 2
      ? { type: "blood_sugar" as VitalType, label: "Blood sugar", points: sugar, summary: vitalsSummary?.latest.blood_sugar }
      : bp.length >= 2
        ? { type: "blood_pressure" as VitalType, label: "Blood pressure", points: bp, summary: vitalsSummary?.latest.blood_pressure }
        : null;

  // Drift nudge — pure read of already-fetched data, no new fetch.
  const driftNudge = useMemo(
    () => computeDriftNudge(truth, vitalsSummary),
    [truth, vitalsSummary],
  );

  // Push to Saathi once when a non-stable nudge first appears.
  useEffect(() => {
    if (driftNudge && !driftPushedRef.current) {
      driftPushedRef.current = true;
      pushSaathiMessage({ role: "assistant", content: driftNudge.saathiHint, action: "monitor" });
    }
  }, [driftNudge]);

  if (!ready || (patient?.id && !consentReady)) {
    return <div className="px-5 py-10 text-center text-sm text-text-faint">Loading…</div>;
  }

  // Consent gate — keep the working flow intact.
  if (patient?.id && !consentOk) {
    return (
      <div className="animate-setu-fade px-5 pb-8 pt-5">
        <ScreenHeader
          mode="greeting"
          dateLine={today}
          name={greetingName}
          tagline="Here's your day. I'm keeping watch."
        />
        <div className="mt-6 rounded-hero border border-border bg-surface-raised p-5 shadow-raised">
          <ConsentPanel
            patientId={patient.id}
            lang={patient.langPref ?? "mr"}
            onGranted={() => setConsentOk(true)}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <ConnectionBadge />
      <OfflineQueueBanner />
      <ScreenHeader
        mode="greeting"
        dateLine={today}
        name={greetingName}
        tagline="Here's your day. I'm keeping watch."
      />

      {/* Living-memory moment: a doctor just added a medicine. */}
      {newMed && (
        <div className="animate-new-med mt-5 flex items-start gap-3 rounded-hero border border-marigold-border bg-marigold-bg p-4">
          <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-marigold" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="font-display text-[15px] font-semibold text-text">
              {newMed.doctor ?? "Your doctor"} just added a new medicine
            </p>
            <p className="mt-0.5 text-sm text-text-muted">
              <span className="font-semibold text-text">{newMed.name}</span> is now in your Today. Saathi
              can remind you when it&apos;s time.
            </p>
            <Link href="/chat" className="mt-2 inline-block text-sm font-semibold text-saathi">
              Ask Saathi about it →
            </Link>
          </div>
          <button type="button" onClick={dismissNewMed} aria-label="Dismiss" className="text-text-faint">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Today's medicines */}
      <TodaySection title="Today's medicines">
        {meds.length === 0 ? (
          <EmptyInvite
            text="No medicines on file yet. Show me a prescription and I'll keep track."
            cta="Add a prescription"
            onClick={async () => {
              await ensurePatient();
              router.push("/upload");
            }}
          />
        ) : (
          <div className="flex flex-col gap-2.5">
            {meds.map((m) => (
              <MedRow
                key={m.normalized_key}
                entry={m}
                isNew={newMed?.key === m.normalized_key}
                onTaken={() => {
                  markTakenToday(m.normalized_key);
                  setAcks((n) => n + 1);
                }}
              />
            ))}
          </div>
        )}
        <span className="sr-only">{acks}</span>
      </TodaySection>

      {/* Upcoming reminders as a time-of-day timeline */}
      {(slots.morning.length > 0 || slots.afternoon.length > 0 || slots.night.length > 0) && (
        <TodaySection title="Your day">
          <div className="flex flex-col gap-3">
            {(["morning", "afternoon", "night"] as Slot[]).map((slot) =>
              slots[slot].length === 0 ? null : (
                <SlotRow key={slot} slot={slot} items={slots[slot]} />
              ),
            )}
          </div>
          {reminders?.disclaimer && (
            <p className="mt-2 text-[11px] italic text-text-faint">{reminders.disclaimer}</p>
          )}
        </TodaySection>
      )}

      {/* One real trend — real data only */}
      <TodaySection title="Your trend">
        {trend ? (
          <Link
            href="/vitals"
            className="block rounded-card border border-border bg-surface-raised p-4 shadow-card"
          >
            <div className="flex items-center justify-between">
              <p className="font-semibold">{trend.label}</p>
              {trend.summary && (
                <span className="font-display text-lg font-semibold tabular-nums text-primary">
                  {trend.points[trend.points.length - 1]}
                </span>
              )}
            </div>
            <div className="mt-3">
              <LabSparkline points={trend.points} />
            </div>
            <p className="mt-2 text-xs text-text-muted">Tap to see your full readings →</p>
          </Link>
        ) : (
          <EmptyInvite
            text="Log your sugar or BP a couple of times and I'll show you the trend here."
            cta="Log a reading"
            onClick={() => router.push("/vitals")}
          />
        )}
      </TodaySection>

      {/* Medicine-reminder opt-in (friendly pre-prompt) */}
      {/* Drift nudge — calm amber, non-diagnostic, dismissible */}
      {driftNudge && !driftDismissed && (
        <div className="mt-6 flex items-start gap-3 rounded-card border border-amber-200 bg-amber-50 p-4">
          <span className="mt-0.5 text-base" aria-hidden>📊</span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-amber-900">{driftNudge.label}</p>
            <p className="mt-0.5 text-sm text-amber-800">{driftNudge.message}</p>
          </div>
          <button
            type="button"
            onClick={() => setDriftDismissed(true)}
            aria-label="Dismiss"
            className="text-amber-400 hover:text-amber-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="mt-6">
        <ReminderOptIn />
      </div>

      <div className="mt-6 flex flex-col gap-2 px-0.5">
        <div className="flex items-start gap-2 text-[13px] text-text-muted">
          <Lock className="mt-0.5 h-[15px] w-[15px] shrink-0 text-primary-light" strokeWidth={1.8} />
          <span>Your records stay private. They&apos;re shared only when you choose to.</span>
        </div>
        <Link href="/profile" className="text-[13px] font-semibold text-primary">
          Profile &amp; privacy
        </Link>
      </div>
    </div>
  );
}
