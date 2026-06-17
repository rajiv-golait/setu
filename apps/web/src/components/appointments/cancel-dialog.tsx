"use client";

import { useState } from "react";
import { SecondaryButton } from "@/components/ui/buttons";

const REASONS = [
  "Schedule conflict",
  "Feeling better",
  "Need a different doctor",
  "Other",
];

export function CancelDialog({
  onConfirm,
}: {
  onConfirm: (reason: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState(REASONS[0]);
  const [busy, setBusy] = useState(false);

  if (!open) {
    return (
      <SecondaryButton onClick={() => setOpen(true)}>Cancel appointment</SecondaryButton>
    );
  }

  return (
    <div className="mt-4 rounded-card border border-border bg-surface-raised p-4">
      <p className="text-sm font-semibold">Cancel appointment</p>
      <select
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="mt-2 w-full rounded border border-border px-3 py-2 text-sm"
      >
        {REASONS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <div className="mt-3 flex gap-2">
        <SecondaryButton
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await onConfirm(reason);
              setOpen(false);
            } finally {
              setBusy(false);
            }
          }}
        >
          Confirm cancel
        </SecondaryButton>
        <button type="button" className="text-sm text-text-muted" onClick={() => setOpen(false)}>
          Back
        </button>
      </div>
    </div>
  );
}
