"use client";

import { useEffect, useState } from "react";
import { listProviderSlots, patchAppointment } from "@/lib/api";
import type { AppointmentSlot } from "@/lib/types";
import { PrimaryButton } from "@/components/ui/buttons";

export function RescheduleFlow({
  appointmentId,
  providerId,
  onDone,
}: {
  appointmentId: string;
  providerId: string;
  onDone: () => void;
}) {
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listProviderSlots(providerId).then(setSlots).catch(() => setSlots([]));
  }, [providerId]);

  const submit = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      await patchAppointment(appointmentId, "reschedule", { new_slot_id: selected });
      onDone();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-4 rounded-card border border-border bg-surface-raised p-4">
      <p className="text-sm font-semibold">Reschedule — pick a new slot</p>
      <div className="mt-2 max-h-40 space-y-1 overflow-y-auto">
        {slots.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSelected(s.id)}
            className={`block w-full rounded border px-3 py-2 text-left text-sm ${
              selected === s.id ? "border-primary bg-[#EEF4F0]" : "border-border"
            }`}
          >
            {new Date(s.starts_at).toLocaleString("en-IN")}
          </button>
        ))}
      </div>
      <PrimaryButton className="mt-3" disabled={!selected || busy} onClick={submit}>
        {busy ? "Rescheduling…" : "Confirm new time"}
      </PrimaryButton>
    </div>
  );
}
