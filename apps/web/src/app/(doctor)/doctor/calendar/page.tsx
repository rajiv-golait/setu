"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DoctorShell } from "@/components/layout/role-shells";
import { PrimaryButton } from "@/components/ui/buttons";
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

  const addRule = () => {
    setRules((r) => [...r, { day_of_week: 1, start_time: "09:00", end_time: "17:00", slot_minutes: 30 }]);
  };

  const save = async () => {
    await setProviderAvailability(rules);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Availability</h1>
      <p className="mt-1 text-sm text-text-muted">Patients book from generated slots.</p>
      <div className="mt-6 space-y-4">
        {rules.map((r, i) => (
          <div key={i} className="rounded-card border border-border p-4 space-y-2">
            <select
              value={r.day_of_week}
              onChange={(e) => {
                const next = [...rules];
                next[i] = { ...r, day_of_week: Number(e.target.value) };
                setRules(next);
              }}
              className="w-full rounded border border-border px-3 py-2"
            >
              {DAYS.map((d, idx) => (
                <option key={d} value={idx}>
                  {d}
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <input
                value={r.start_time}
                onChange={(e) => {
                  const next = [...rules];
                  next[i] = { ...r, start_time: e.target.value };
                  setRules(next);
                }}
                className="flex-1 rounded border border-border px-3 py-2"
              />
              <input
                value={r.end_time}
                onChange={(e) => {
                  const next = [...rules];
                  next[i] = { ...r, end_time: e.target.value };
                  setRules(next);
                }}
                className="flex-1 rounded border border-border px-3 py-2"
              />
            </div>
          </div>
        ))}
        <button type="button" onClick={addRule} className="text-sm font-semibold text-primary">
          + Add hours
        </button>
        <PrimaryButton onClick={save}>Save availability</PrimaryButton>
        {saved && <p className="text-sm text-success">Saved.</p>}
      </div>
      <Link href="/doctor" className="mt-6 inline-block text-sm font-semibold text-primary">
        Back to dashboard
      </Link>
    </DoctorShell>
  );
}
