"use client";

import { useState } from "react";
import { PrimaryButton } from "@/components/ui/buttons";

export type RxLine = {
  name: string;
  dose: string;
  frequency: string;
  duration: string;
  instructions: string;
};

const emptyLine = (): RxLine => ({
  name: "",
  dose: "",
  frequency: "",
  duration: "",
  instructions: "",
});

export function PrescriptionBuilder({
  onSave,
}: {
  onSave: (items: RxLine[]) => Promise<void>;
}) {
  const [lines, setLines] = useState<RxLine[]>([emptyLine()]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const update = (i: number, field: keyof RxLine, value: string) => {
    setLines((prev) => prev.map((l, idx) => (idx === i ? { ...l, [field]: value } : l)));
  };

  const submit = async () => {
    const items = lines.filter((l) => l.name.trim());
    if (items.length === 0) return;
    setSaving(true);
    try {
      await onSave(items);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-6 rounded-card border border-border bg-surface-raised p-4">
      <h3 className="text-sm font-semibold">Prescription</h3>
      <div className="mt-3 space-y-3">
        {lines.map((line, i) => (
          <div key={i} className="grid gap-2 sm:grid-cols-2">
            <input
              placeholder="Medicine"
              value={line.name}
              onChange={(e) => update(i, "name", e.target.value)}
              className="rounded border border-border px-3 py-2 text-sm sm:col-span-2"
            />
            <input
              placeholder="Dose"
              value={line.dose}
              onChange={(e) => update(i, "dose", e.target.value)}
              className="rounded border border-border px-3 py-2 text-sm"
            />
            <input
              placeholder="Frequency"
              value={line.frequency}
              onChange={(e) => update(i, "frequency", e.target.value)}
              className="rounded border border-border px-3 py-2 text-sm"
            />
            <input
              placeholder="Duration"
              value={line.duration}
              onChange={(e) => update(i, "duration", e.target.value)}
              className="rounded border border-border px-3 py-2 text-sm"
            />
            <input
              placeholder="Instructions"
              value={line.instructions}
              onChange={(e) => update(i, "instructions", e.target.value)}
              className="rounded border border-border px-3 py-2 text-sm"
            />
          </div>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setLines((l) => [...l, emptyLine()])}
          className="text-sm font-semibold text-primary"
        >
          + Add medicine
        </button>
        <PrimaryButton disabled={saving} onClick={submit}>
          {saving ? "Saving…" : "Save prescription"}
        </PrimaryButton>
        {saved && <span className="text-sm text-success">Saved.</span>}
      </div>
    </div>
  );
}
