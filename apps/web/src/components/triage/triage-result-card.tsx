"use client";

import Link from "next/link";
import type { TriageResult, TriageRecommendation } from "@/lib/types";
import { PrimaryButton } from "@/components/ui/buttons";
import { useLocale } from "@/lib/hooks/use-locale";

const PRIORITY_STYLES = {
  low: "bg-success-bg text-success",
  medium: "bg-warning-bg text-warning",
  high: "bg-danger-bg text-danger",
} as const;

const REC_LABELS: Record<TriageRecommendation, string> = {
  visit_phc: "Visit nearest PHC",
  schedule_specialist: "Schedule specialist consultation",
  emergency: "Emergency care recommended",
};

export function TriageResultCard({ result }: { result: TriageResult }) {
  const { t } = useLocale();

  return (
    <div className="rounded-card border border-border bg-surface-raised p-4 shadow-card">
      <div className="flex items-center justify-between gap-2">
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase ${PRIORITY_STYLES[result.priority]}`}
        >
          {result.priority} priority
        </span>
        <span className="text-xs text-text-faint">
          {new Date(result.created_at).toLocaleDateString("en-IN")}
        </span>
      </div>
      <p className="mt-3 text-base font-semibold">{REC_LABELS[result.recommendation]}</p>
      {result.message && (
        <p className="mt-2 text-sm leading-relaxed text-text-muted">{result.message}</p>
      )}
      <p className="mt-3 rounded-lg bg-[#F8F7F2] px-3 py-2 text-xs text-text-muted">
        {result.disclaimer ??
          "This is guidance on where to seek care, not a diagnosis. It does not identify any disease or recommend medicine."}
      </p>
      {result.recommendation === "schedule_specialist" && (
        <Link href={`/appointments/new?triage_id=${result.id}`} className="mt-4 block">
          <PrimaryButton>{t("triage.book")}</PrimaryButton>
        </Link>
      )}
    </div>
  );
}
