/** Shared specialty labels for booking, referrals, and admin doctor setup. */
export const MEDICAL_SPECIALTIES = [
  "General physician",
  "Cardiologist",
  "Dermatologist",
  "Endocrinologist",
  "Gynecologist",
  "Pediatrician",
  "Ophthalmologist",
  "Nephrologist",
  "Orthopaedic",
  "Neurologist",
  "Psychiatrist",
] as const;

export type MedicalSpecialty = (typeof MEDICAL_SPECIALTIES)[number];
