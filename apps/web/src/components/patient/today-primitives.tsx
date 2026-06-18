"use client";

import { Camera, Check, Sun, Sunrise, Sunset } from "lucide-react";
import { SecondaryButton } from "@/components/ui/buttons";
import { SectionHeading } from "@/components/ui/section-heading";
import { medField, medWhy } from "@/lib/med-utils";
import { isTakenToday } from "@/lib/med-acks";
import type { CurrentTruthEntry, ReminderItem } from "@/lib/types";

export function TodaySection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-7">
      <SectionHeading title={title} />
      {children}
    </section>
  );
}

export function MedRow({
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
      className={`flex items-center gap-3 rounded-card border p-3.5 ${
        isNew
          ? "border-marigold-border bg-marigold-bg"
          : "border-border bg-surface-raised shadow-card"
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

type Slot = "morning" | "afternoon" | "night";
const SLOT_META: Record<Slot, { label: string; icon: typeof Sunrise }> = {
  morning: { label: "Morning", icon: Sunrise },
  afternoon: { label: "Afternoon", icon: Sun },
  night: { label: "Night", icon: Sunset },
};

export function SlotRow({ slot, items }: { slot: Slot; items: ReminderItem[] }) {
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
            className="rounded-card border border-border bg-surface-raised px-3.5 py-2.5"
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

export function EmptyInvite({
  text,
  cta,
  onClick,
}: {
  text: string;
  cta: string;
  onClick: () => void;
}) {
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
