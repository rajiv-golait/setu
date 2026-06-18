"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { ScreenHeader } from "@/components/ui/screen-header";
import { getProviderAvailability, setProviderAvailability } from "@/lib/api";

type Rule = { day_of_week: number; start_time: string; end_time: string; slot_minutes: number };

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function DoctorCalendarPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getProviderAvailability()
      .then(setRules)
      .catch(() => setRules([]));
  }, []);

  const addForDay = (day: number) =>
    setRules((r) => [...r, { day_of_week: day, start_time: "09:00", end_time: "17:00", slot_minutes: 30 }]);

  const patch = (i: number, next: Partial<Rule>) =>
    setRules((r) => r.map((rule, idx) => (idx === i ? { ...rule, ...next } : rule)));

  const remove = (i: number) => setRules((r) => r.filter((_, idx) => idx !== i));

  const save = async () => {
    await setProviderAvailability(rules);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // Group rules by day so the editor reads like a week, not a stack of identical cards.
  const byDay = DAYS.map((label, day) => ({
    label,
    day,
    rows: rules.map((r, i) => ({ r, i })).filter(({ r }) => r.day_of_week === day),
  }));

  return (
    <>
      <ScreenHeader title="Availability" subtitle="Patients book from your published slots." />

      <div className="mt-6 overflow-hidden rounded-card border border-border bg-surface-raised">
        {byDay.map(({ label, day, rows }) => (
          <div
            key={day}
            className="grid grid-cols-[3.5rem_1fr] items-start gap-3 border-b border-border px-4 py-3.5 last:border-b-0 sm:grid-cols-[5rem_1fr]"
          >
            <span className="pt-1.5 font-display text-sm font-semibold text-text">{label}</span>
            <div className="space-y-2">
              {rows.length === 0 ? (
                <button
                  type="button"
                  onClick={() => addForDay(day)}
                  className="text-sm text-text-faint hover:text-primary"
                >
                  Closed · add hours
                </button>
              ) : (
                <>
                  {rows.map(({ r, i }) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        type="time"
                        value={r.start_time}
                        onChange={(e) => patch(i, { start_time: e.target.value })}
                        className="rounded border border-border bg-surface px-2.5 py-1.5 text-sm tabular-nums"
                      />
                      <span className="text-text-faint">–</span>
                      <input
                        type="time"
                        value={r.end_time}
                        onChange={(e) => patch(i, { end_time: e.target.value })}
                        className="rounded border border-border bg-surface px-2.5 py-1.5 text-sm tabular-nums"
                      />
                      <button
                        type="button"
                        onClick={() => remove(i)}
                        aria-label="Remove hours"
                        className="ml-auto text-text-faint hover:text-danger"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addForDay(day)}
                    className="text-xs font-semibold text-primary"
                  >
                    + Another window
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 flex max-w-xs items-center gap-4">
        <PrimaryButton onClick={save}>Save availability</PrimaryButton>
        {saved && <span className="shrink-0 text-sm text-success">Saved.</span>}
      </div>

      <Link href="/doctor" className="mt-6 inline-block text-sm font-semibold text-primary">
        Back to dashboard
      </Link>
    </>
  );
}
