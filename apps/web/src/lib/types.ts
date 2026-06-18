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
  consult_room?: string | null;
}

export interface ReminderItem {
  type: "medication" | "lab_test_due" | "refill_due";
  label: string;
  frequency_text?: string | null;
  times_of_day?: string[];
  relative_to_food?: string | null;
  due_date?: string | null;
  source_claim_id?: string | null;
  needs_confirmation?: boolean;
  note?: string | null;
}

export interface ReminderSchedule {
  patient_id: string;
  reminders: ReminderItem[];
  disclaimer: string;
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
  onboarding_completed?: boolean;
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
  language?: string;
  lang?: string;
  /** Reasoner that produced this summary; non-"mock" → real AI ("AI verified"). */
  model?: string;
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

// --- Provider / doctor portal ---

export interface ProviderRecord {
  id: string;
  display_name?: string | null;
  specialty?: string | null;
  facility?: string | null;
  verification_status?: string;
  experience_years?: number | null;
  languages?: string[] | null;
  location?: string | null;
  consultation_fee?: number | null;
  bio?: string | null;
  created_at: string;
}

export interface ProviderDashboard {
  pending_requests: number;
  today_appointments: number;
  completed_this_week: number;
  patient_count: number;
  follow_ups_due: number;
}

export interface AppointmentSlot {
  id: string;
  provider_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
}

export interface PatientProfile {
  patient_id: string;
  date_of_birth?: string | null;
  gender?: string | null;
  blood_group?: string | null;
  allergies_known?: string[] | null;
  chronic_conditions?: string[] | null;
  emergency_contact?: Record<string, string> | null;
  district?: string | null;
  state?: string | null;
}

export interface TimelineEvent {
  event_type: string;
  title: string;
  at: string;
  meta?: Record<string, unknown> | null;
}

export interface Encounter {
  id: string;
  patient_id: string;
  provider_id: string;
  appointment_id?: string | null;
  status: string;
  encounter_type: string;
}

export interface AuthMe {
  user_id: string;
  role: string;
  verification_status?: string | null;
  provider_id?: string | null;
  patient_id?: string | null;
  health_worker_id?: string | null;
}

export interface AdminProviderRecord extends ProviderRecord {
  supabase_user_id: string;
  phone?: string | null;
  verification_status?: string;
}

// --- Triage (F1) ---

export type TriagePriority = "low" | "medium" | "high";
export type TriageRecommendation = "visit_phc" | "schedule_specialist" | "emergency";

export interface TriageResult {
  id: string;
  patient_id: string;
  priority: TriagePriority;
  recommendation: TriageRecommendation;
  rationale: Record<string, unknown>;
  message?: string | null;
  lang: string;
  engine_version: string;
  created_at: string;
  disclaimer?: string;
}

export interface TriageRequest {
  symptoms: string[];
  age?: number | null;
  existing_conditions?: string[];
  document_ids?: string[];
}

// --- Appointments (F2) ---

export type AppointmentStatus =
  | "requested"
  | "accepted"
  | "confirmed"
  | "completed"
  | "declined"
  | "cancelled";

export interface Appointment {
  id: string;
  patient_id: string;
  provider_id?: string | null;
  slot_id?: string | null;
  specialty: string;
  status: AppointmentStatus;
  scheduled_for?: string | null;
  consult_room?: string | null;
  referral_id?: string | null;
  triage_id?: string | null;
  notes?: string | null;
  requested_at: string;
  created_at: string;
  updated_at: string;
  provider_name?: string | null;
  provider_specialty?: string | null;
}

// --- Vitals (F5) ---

export type VitalType = "blood_pressure" | "blood_sugar" | "spo2" | "heart_rate";

export interface VitalReading {
  id: string;
  patient_id: string;
  vital_type: VitalType;
  value: Record<string, unknown>;
  unit: string;
  measured_at: string;
  source: string;
  created_at: string;
  flag?: string | null;
  flag_message?: string | null;
}

export interface VitalsSummary {
  patient_id: string;
  latest: Partial<Record<VitalType, VitalReading>>;
  trends: Partial<Record<VitalType, Trend>>;
}

// --- Health worker (F4) ---

export interface HealthWorkerRecord {
  id: string;
  display_name?: string | null;
  facility_type?: string | null;
  facility_name?: string | null;
  district?: string | null;
  created_at: string;
}

export interface AssignedPatient {
  id: string;
  display_name?: string | null;
  lang_pref: string;
  is_rural?: boolean;
  assigned_at: string;
}

// --- Admin analytics (F6) ---

export interface AnalyticsOverview {
  consultations_completed: number;
  rural_patients: number;
  total_patients: number;
  languages: Array<{ lang_pref: string; count: number }>;
  referral_completion_rate: number;
  high_priority_triage: number;
  avg_consultation_minutes?: number | null;
}

// --- Access audit ---

export interface AccessLogEntry {
  id: string;
  actor_role: string;
  action: string;
  resource: string;
  created_at: string;
}
