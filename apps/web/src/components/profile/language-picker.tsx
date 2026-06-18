"use client";

import { PATIENT_LANGS, type PatientLang } from "@/lib/constants/langs";
import { cn } from "@/lib/cn";

type LanguagePickerProps = {
  value: PatientLang;
  onChange: (lang: PatientLang) => void;
  disabled?: boolean;
};

export function LanguagePicker({ value, onChange, disabled }: LanguagePickerProps) {
  return (
    <div className="space-y-2">
      {PATIENT_LANGS.map((l) => (
        <button
          key={l.id}
          type="button"
          disabled={disabled}
          onClick={() => onChange(l.id)}
          className={cn(
            "flex w-full items-center justify-between rounded-card border px-4 py-3.5 text-left transition-colors disabled:opacity-50",
            value === l.id
              ? "border-primary bg-[#EEF4F0] shadow-card"
              : "border-border bg-surface-raised hover:border-primary/40",
          )}
        >
          <span className="text-base font-semibold">{l.label}</span>
          <span className="text-sm text-text-muted">{l.sub}</span>
        </button>
      ))}
    </div>
  );
}
