/** Format provider display name without doubling the Dr. prefix. */
export function formatDoctorName(displayName?: string | null): string {
  if (!displayName?.trim()) return "Doctor dashboard";
  const trimmed = displayName.trim();
  if (/^dr\.?\s/i.test(trimmed)) return trimmed;
  return `Dr. ${trimmed}`;
}

export function patientLabel(appt: {
  patient_display_name?: string | null;
  patient_id: string;
}): string {
  return appt.patient_display_name?.trim() || `Patient ${appt.patient_id.slice(0, 8)}…`;
}

export function isToday(iso?: string | null): boolean {
  if (!iso) return false;
  const d = new Date(iso);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export function formatWhen(iso?: string | null): string {
  if (!iso) return "Time not set";
  return new Date(iso).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
