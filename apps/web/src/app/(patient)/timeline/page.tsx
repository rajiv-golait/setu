"use client";

import { useEffect, useState } from "react";
import { getPatientTimeline } from "@/lib/api";
import { BackLink } from "@/components/ui/back-link";
import { EmptyState } from "@/components/ui/empty-state";
import { ScreenHeader } from "@/components/ui/screen-header";
import { usePatient } from "@/lib/hooks/use-patient";
import { useLocale } from "@/lib/hooks/use-locale";
import type { TimelineEvent } from "@/lib/types";

export default function TimelinePage() {
  const { patient, ready } = usePatient();
  const { t } = useLocale();
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!patient?.id) return;
    getPatientTimeline(patient.id)
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [patient?.id]);

  if (!ready) return null;

  return (
    <div className="px-5 pb-24 pt-5">
      <BackLink href="/memory" />
      <ScreenHeader title={t("timeline.title")} subtitle={t("timeline.subtitle")} />

      {loading ? (
        <p className="mt-6 text-sm text-text-faint">Loading…</p>
      ) : events.length === 0 ? (
        <EmptyState
          variant="withSaathi"
          title={t("timeline.empty")}
          message="Upload a report or book a visit — your timeline builds automatically."
          actionLabel="Upload a document"
          onAction={() => {
            window.location.href = "/upload";
          }}
        />
      ) : (
        <ol className="relative mt-6 space-y-6 border-l-2 border-primary/25 pl-5">
          {events.map((e, i) => (
            <li key={`${e.event_type}-${e.at}-${i}`} className="relative">
              <span className="absolute -left-[23px] top-1.5 h-3 w-3 rounded-full border-2 border-surface bg-primary" />
              <p className="text-xs text-text-faint">
                {new Date(e.at).toLocaleString("en-IN")}
              </p>
              <p className="mt-0.5 font-semibold">{e.title}</p>
              <p className="text-xs capitalize text-text-muted">{e.event_type.replace("_", " ")}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
