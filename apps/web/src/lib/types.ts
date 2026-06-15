export type Trend = "up" | "down" | "stable";

export interface BriefFlag {
  severity: "info" | "warning" | "critical";
  text: string;
  type: "abnormal_lab" | "needs_review" | "missing_data" | "conflict";
}

export interface BriefPriority {
  level: "routine" | "review_soon";
  reasons: string[];
}

export interface DoctorBrief {
  brief_id: string;
  patient_id: string;
  generated_at: string;
  model: string;
  one_line: string;
  chief_concern: string;
  active_medications: Array<{
    name: string;
    dose?: string | null;
    frequency?: string | null;
    since?: string | null;
    source?: string | null;
  }>;
  recent_labs: Array<{
    test: string;
    value: number | string;
    unit?: string | null;
    flag?: string | null;
    date?: string | null;
    trend?: Trend | null;
    previous?: number | string | null;
  }>;
  active_conditions: Array<{
    condition: string;
    since?: string | null;
    source?: string | null;
  }>;
  allergies: Array<{
    substance: string;
    severity?: string | null;
  }>;
  timeline: Array<{ date: string; event: string }>;
  flags: BriefFlag[];
  suggested_questions: string[];
  source_documents: string[];
  confidence_notes?: string | null;
  referred_by?: string | null;
  referral_reason?: string | null;
  specialist_type?: string | null;
  priority?: BriefPriority | null;
}

export interface ShareSnapshot {
  share_id: string;
  token: string;
  created_at: string;
  expires_at?: string | null;
  read_only: boolean;
  patient_ref: string;
  brief: DoctorBrief;
  current_truth: {
    patient_id: string;
    entries: unknown[];
    generated_at: string;
  };
  audience?: "patient" | "specialist";
}

export interface ShareCreateResponse {
  share_id: string;
  token: string;
  url: string;
  qr_svg: string;
  created_at: string;
  expires_at?: string | null;
}

export interface PatientRecord {
  id: string;
  display_name?: string | null;
  lang_pref: string;
  created_at: string;
  patient_token?: string | null;
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  stage?: string | null;
  stages: string[];
  completed_stages: string[];
  progress: number;
  failed_at?: string | null;
  error?: { code?: string; message?: string; retryable?: boolean } | null;
  document_id?: string | null;
  result: Record<string, unknown>;
}

export interface CurrentTruthEntry {
  entry_type: string;
  normalized_key: string;
  value: Record<string, unknown>;
  confidence: number;
  state: string;
  source_claim_ids: string[];
}

export interface CurrentTruth {
  patient_id: string;
  entries: CurrentTruthEntry[];
  generated_at: string;
}

export interface PatientSummary {
  summary_id: string;
  patient_id: string;
  lang: string;
  greeting: string;
  what_we_found: string[];
  your_medicines: Array<{ name: string; how_to_take: string; plain: string }>;
  what_to_watch: string[];
  next_steps: string[];
  disclaimer: string;
}

export interface DocumentListItem {
  id: string;
  patient_id: string;
  doc_type?: string | null;
  mime?: string | null;
  source: string;
  status: string;
  uploaded_at: string;
}
