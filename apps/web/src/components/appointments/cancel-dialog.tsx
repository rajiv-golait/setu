"use client";

import { useEffect, useState } from "react";
import { SecondaryButton } from "@/components/ui/buttons";

const REASONS = [
  "Schedule conflict",
  "Feeling better",
  "Need a different doctor",
  "Other",
];

export function CancelDialog({
  onConfirm,
  disabled = false,
}: {
  onConfirm: (reason: string) => Promise<void>;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState(REASONS[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (disabled) {
      setOpen(false);
      setError(null);
    }
  }, [disabled]);

  if (disabled) {
    return null;
  }

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
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
      <div className="mt-3 flex gap-2">
        <SecondaryButton
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError(null);
            try {
              await onConfirm(reason);
              setOpen(false);
            } catch (e) {
              setError(e instanceof Error ? e.message : "Could not cancel appointment");
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
