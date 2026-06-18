export type PatientLang = "mr" | "hi" | "en";

export const PATIENT_LANGS: Array<{ id: PatientLang; label: string; sub: string }> = [
  { id: "mr", label: "मराठी", sub: "Marathi" },
  { id: "hi", label: "हिंदी", sub: "Hindi" },
  { id: "en", label: "English", sub: "English" },
];

export function isPatientLang(v: string): v is PatientLang {
  return v === "mr" || v === "hi" || v === "en";
}
