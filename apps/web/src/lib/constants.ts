export const PRIORITY_DISCLAIMER =
  "Flagged on objective out-of-range values for prioritization only — not a clinical assessment.";

/** Browser calls same-origin `/api/v1` (proxied by Next.js). SSR hits the API directly. */
function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
  if (typeof window !== "undefined") return configured;
  if (configured.startsWith("http://") || configured.startsWith("https://")) return configured;
  const backend = (process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  return `${backend}${configured.startsWith("/") ? configured : `/${configured}`}`;
}

export const API_BASE = resolveApiBase();

export const STAGE_LABELS: Record<string, string> = {
  extraction: "Reading your document",
  validation: "Checking the values",
  memory: "Building your health record",
  explanation: "Writing your explanation",
  brief: "Composing the doctor brief",
  summary: "Writing your Marathi summary",
  share: "Preparing your share link",
};
