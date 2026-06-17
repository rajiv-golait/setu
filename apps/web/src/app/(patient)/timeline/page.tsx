"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { getPatientTimeline } from "@/lib/api";
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
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <Link href="/memory" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
        <ChevronLeft className="h-4 w-4" aria-hidden />
        Back
      </Link>
      <h1 className="text-[23px] font-semibold">{t("timeline.title")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("timeline.subtitle")}</p>

      {loading ? (
        <p className="mt-6 text-sm text-text-faint">Loading…</p>
      ) : events.length === 0 ? (
        <p className="mt-6 text-sm text-text-muted">{t("timeline.empty")}</p>
      ) : (
        <ol className="relative mt-6 space-y-4 border-l-2 border-primary/20 pl-4">
          {events.map((e, i) => (
            <li key={`${e.event_type}-${e.at}-${i}`} className="relative">
              <span className="absolute -left-[21px] top-1 h-3 w-3 rounded-full bg-primary" />
              <p className="text-xs text-text-faint">
                {new Date(e.at).toLocaleString("en-IN")}
              </p>
              <p className="font-semibold">{e.title}</p>
              <p className="text-xs capitalize text-text-muted">{e.event_type.replace("_", " ")}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
