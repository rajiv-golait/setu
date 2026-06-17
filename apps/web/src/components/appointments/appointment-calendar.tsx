"use client";

import type { Appointment } from "@/lib/types";
import { cn } from "@/lib/cn";

export function AppointmentCalendar({ appointments }: { appointments: Appointment[] }) {
  const now = new Date();
  const days: Date[] = [];
  for (let i = -1; i < 6; i++) {
    const d = new Date(now);
    d.setDate(now.getDate() + i);
    days.push(d);
  }

  const hasAppt = (day: Date) =>
    appointments.some((a) => {
      if (!a.scheduled_for) return false;
      const d = new Date(a.scheduled_for);
      return (
        d.getFullYear() === day.getFullYear() &&
        d.getMonth() === day.getMonth() &&
        d.getDate() === day.getDate()
      );
    });

  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {days.map((day) => {
        const isToday =
          day.getDate() === now.getDate() &&
          day.getMonth() === now.getMonth() &&
          day.getFullYear() === now.getFullYear();
        const dot = hasAppt(day);
        return (
          <div
            key={day.toISOString()}
            className={cn(
              "flex min-w-[52px] flex-col items-center rounded-card border px-2 py-2 text-center",
              isToday ? "border-primary bg-[#EEF4F0]" : "border-border bg-surface-raised",
            )}
          >
            <span className="text-[10px] uppercase text-text-muted">
              {day.toLocaleDateString("en-IN", { weekday: "short" })}
            </span>
            <span className="text-lg font-semibold">{day.getDate()}</span>
            <span
              className={cn(
                "mt-1 h-1.5 w-1.5 rounded-full",
                dot ? "bg-primary" : "bg-transparent",
              )}
            />
          </div>
        );
      })}
    </div>
  );
}
