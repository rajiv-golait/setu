"use client";

import type { TimelineEvent } from "@/lib/types";

export function DoctorTimelineSidebar({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-card border border-border bg-surface-raised p-4 text-sm text-text-muted">
        No timeline events yet.
      </div>
    );
  }

  const byYear = events.reduce<Record<string, TimelineEvent[]>>((acc, ev) => {
    const year = new Date(ev.at).getFullYear().toString();
    if (!acc[year]) acc[year] = [];
    acc[year].push(ev);
    return acc;
  }, {});

  const years = Object.keys(byYear).sort((a, b) => Number(b) - Number(a));

  return (
    <div className="rounded-card border border-border bg-surface-raised p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Timeline</h2>
      <div className="mt-4 space-y-5">
        {years.map((year) => (
          <div key={year}>
            <p className="text-xs font-bold text-primary">{year}</p>
            <ul className="mt-2 space-y-3 border-l-2 border-primary/20 pl-3">
              {byYear[year].slice(0, 8).map((ev, i) => (
                <li key={`${ev.at}-${i}`} className="relative">
                  <span className="absolute -left-[1.15rem] top-1.5 h-2 w-2 rounded-full bg-primary" />
                  <p className="text-xs text-text-faint">
                    {new Date(ev.at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                    })}
                  </p>
                  <p className="text-sm font-semibold text-text">{ev.title}</p>
                  {ev.event_type && (
                    <p className="text-xs capitalize text-text-muted">{ev.event_type.replace(/_/g, " ")}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
