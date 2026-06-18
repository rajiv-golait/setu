"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Camera, Check, Lock, Sparkles, Sun, Sunrise, Sunset, X } from "lucide-react";
import { SecondaryButton } from "@/components/ui/buttons";
import { ConsentPanel } from "@/components/consent/consent-panel";
import { OfflineQueueBanner } from "@/components/ui/offline-queue-banner";
import { ConnectionBadge } from "@/components/ui/connection-badge";
import { SetuAvatar } from "@/components/characters/setu-avatar";
import { LabSparkline } from "@/components/ui/sparkline";
import { ReminderOptIn } from "@/components/reminders/reminder-opt-in";
import { hasLocalConsent } from "@/lib/consent";
import { getReminders, getVitalsSummary, listVitals } from "@/lib/api";
import { useLiveMemory } from "@/lib/hooks/use-live-memory";
import { isTakenToday, markTakenToday } from "@/lib/med-acks";
import { usePatient } from "@/lib/hooks/use-patient";
import type {
  CurrentTruthEntry,
  ReminderItem,
  ReminderSchedule,
  VitalReading,
  VitalsSummary,
  VitalType,
} from "@/lib/types";

function medField(entry: CurrentTruthEntry, key: string): string {
  const v = entry.value;
  const val = v[key] ?? (Array.isArray(v.values) ? (v.values[0] as Record<string, unknown>)?.[key] : undefined);
  return val == null ? "" : String(val);
}

/** Plain-language "why" for a medicine — from its own instructions/frequency, never invented. */
function medWhy(entry: CurrentTruthEntry): string {
  const instr = medField(entry, "instructions");
  if (instr) return instr;
  const freq = medField(entry, "frequency");
  const food = medField(entry, "relative_to_food");
  const parts = [freq, food].filter(Boolean);
  return parts.length ? parts.join(" · ") : "As prescribed by your doctor";
}

type Slot = "morning" | "afternoon" | "night";
const SLOT_META: Record<Slot, { label: string; icon: typeof Sunrise }> = {
  morning: { label: "Morning", icon: Sunrise },
  afternoon: { label: "Afternoon", icon: Sun },
  night: { label: "Night", icon: Sunset },
};

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
  const [reminders, setReminders] = useState<ReminderSchedule | null>(null);
  const [vitalsSummary, setVitalsSummary] = useState<VitalsSummary | null>(null);
  const [vitals, setVitals] = useState<VitalReading[]>([]);
  const [acks, setAcks] = useState(0); // bump to re-render after marking taken

  const { truth, newMed, dismissNewMed } = useLiveMemory(consentOk && patient?.id ? patient.id : null);

  useEffect(() => {
    if (patient?.id && hasLocalConsent(patient.id)) setConsentOk(true);
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

  if (!ready) {
    return <div className="px-5 py-10 text-center text-sm text-text-faint">Loading…</div>;
  }

  // Consent gate — keep the working flow intact.
  if (patient?.id && !consentOk) {
    return (
      <div className="animate-setu-fade px-5 pb-8 pt-5">
        <Greeting name={greetingName} today={today} />
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
      <Greeting name={greetingName} today={today} />

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
      <Section title="Today's medicines">
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
      </Section>

      {/* Upcoming reminders as a time-of-day timeline */}
      {(slots.morning.length > 0 || slots.afternoon.length > 0 || slots.night.length > 0) && (
        <Section title="Your day">
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
        </Section>
      )}

      {/* One real trend — real data only */}
      <Section title="Your trend">
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
      </Section>

      {/* Medicine-reminder opt-in (friendly pre-prompt) */}
      <div className="mt-6">
        <ReminderOptIn />
      </div>

      <div className="mt-6 flex flex-col gap-2 px-0.5">
        <div className="flex items-start gap-2 text-[13px] text-text-muted">
          <Lock className="mt-0.5 h-[15px] w-[15px] shrink-0 text-primary-light" strokeWidth={1.8} />
          <span>Your records stay private. They&apos;re shared only when you choose to.</span>
        </div>
        <Link href="/settings" className="text-[13px] font-semibold text-primary">
          Privacy &amp; my data
        </Link>
      </div>
    </div>
  );
}

function Greeting({ name, today }: { name: string; today: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div>
        <p className="text-[13px] text-text-muted">{today}</p>
        <h1 className="font-display text-2xl font-semibold tracking-tight">Namaste, {name}</h1>
        <p className="mt-0.5 text-sm text-text-muted">Here&apos;s your day. I&apos;m keeping watch.</p>
      </div>
      <SetuAvatar size={56} label="SETU, your health keeper" />
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-7">
      <div className="mb-2.5 flex items-center gap-2 px-0.5">
        <h2 className="font-display text-[13px] font-semibold uppercase tracking-[0.06em] text-primary-light">
          {title}
        </h2>
        <div className="h-px flex-1 bg-border" />
      </div>
      {children}
    </section>
  );
}

function MedRow({
  entry,
  isNew,
  onTaken,
}: {
  entry: CurrentTruthEntry;
  isNew: boolean;
  onTaken: () => void;
}) {
  const name = medField(entry, "name") || entry.normalized_key;
  const dose = medField(entry, "dose");
  const unit = medField(entry, "dose_unit");
  const taken = isTakenToday(entry.normalized_key);

  return (
    <div
      className={`flex items-center gap-3 rounded-card border p-3.5 shadow-card ${
        isNew ? "border-marigold-border bg-marigold-bg" : "border-border bg-surface-raised"
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-display text-[15px] font-semibold">{name}</p>
          {dose && (
            <span className="rounded-full bg-[#E4F3F0] px-2 py-0.5 text-xs font-semibold text-primary">
              {dose}
              {unit}
            </span>
          )}
          {isNew && (
            <span className="rounded-full bg-marigold px-2 py-0.5 text-[11px] font-semibold text-white">
              New
            </span>
          )}
        </div>
        <p className="mt-0.5 text-sm text-text-muted">{medWhy(entry)}</p>
      </div>
      <button
        type="button"
        onClick={onTaken}
        disabled={taken}
        aria-label={taken ? `${name} taken` : `Mark ${name} as taken`}
        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
          taken
            ? "animate-med-check border-success bg-success text-white"
            : "border-primary-light bg-white text-primary-light active:bg-[#E4F3F0]"
        }`}
      >
        <Check className="h-6 w-6" strokeWidth={2.4} />
      </button>
    </div>
  );
}

function SlotRow({ slot, items }: { slot: Slot; items: ReminderItem[] }) {
  const { label, icon: Icon } = SLOT_META[slot];
  return (
    <div className="flex gap-3">
      <div className="flex w-16 shrink-0 flex-col items-center gap-1 pt-1">
        <Icon className="h-5 w-5 text-marigold" strokeWidth={1.8} aria-hidden />
        <span className="text-[11px] font-semibold text-text-muted">{label}</span>
      </div>
      <div className="flex-1 space-y-1.5">
        {items.map((r, i) => (
          <div
            key={`${r.label}-${i}`}
            className="rounded-card border border-border bg-surface-raised px-3.5 py-2.5 shadow-card"
          >
            <p className="text-sm font-semibold">{r.label}</p>
            {r.frequency_text && <p className="text-xs text-text-muted">{r.frequency_text}</p>}
            {r.needs_confirmation && (
              <span className="mt-1 inline-block rounded-full bg-warning-bg px-2 py-0.5 text-[11px] font-semibold text-warning">
                Confirm with your doctor
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyInvite({ text, cta, onClick }: { text: string; cta: string; onClick: () => void }) {
  return (
    <div className="rounded-card border border-dashed border-primary-light/40 bg-[#EAF5F2] p-4 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#D6EDE8]">
        <Camera className="h-6 w-6 text-primary" strokeWidth={1.7} aria-hidden />
      </div>
      <p className="mt-2 text-sm text-text-muted">{text}</p>
      <SecondaryButton className="mt-3" onClick={onClick}>
        {cta}
      </SecondaryButton>
    </div>
  );
}
