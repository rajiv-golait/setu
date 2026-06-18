"use client";

import { useState } from "react";
import { SecondaryButton } from "@/components/ui/buttons";

const REASONS = [
  "Not available at this time",
  "Outside my specialty",
  "Schedule full",
  "Other",
];

export function DeclineDialog({
  onConfirm,
  className,
}: {
  onConfirm: (reason: string) => Promise<void>;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState(REASONS[0]);
  const [busy, setBusy] = useState(false);

  if (!open) {
    return (
      <SecondaryButton className={className ?? "flex-1"} onClick={() => setOpen(true)}>
        Decline
      </SecondaryButton>
    );
  }

  return (
    <div className="mt-3 rounded-card border border-border bg-surface p-3">
      <p className="text-sm font-semibold">Decline request</p>
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
      <div className="mt-2 flex gap-2">
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
          Confirm decline
        </SecondaryButton>
        <button type="button" className="text-sm text-text-muted" onClick={() => setOpen(false)}>
          Back
        </button>
      </div>
    </div>
  );
}
