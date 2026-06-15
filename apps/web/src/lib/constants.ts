export const PRIORITY_DISCLAIMER =
  "Flagged on objective out-of-range values for prioritization only — not a clinical assessment.";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const STAGE_LABELS: Record<string, string> = {
  extraction: "Reading your document",
  validation: "Checking the values",
  memory: "Building your health record",
  explanation: "Writing your explanation",
  brief: "Composing the doctor brief",
  summary: "Writing your Marathi summary",
  share: "Preparing your share link",
};
