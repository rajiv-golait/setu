import { API_BASE } from "./constants";
import type {
  AccessLogEntry,
  AdminProviderRecord,
  AnalyticsOverview,
  Appointment,
  AssignedPatient,
  CurrentTruth,
  DoctorBrief,
  DocumentListItem,
  Encounter,
  HealthWorkerRecord,
  JobStatus,
  PatientRecord,
  PatientSummary,
  ProviderRecord,
  ReminderSchedule,
  ShareCreateResponse,
  ShareSnapshot,
  TriageRequest,
  TriageResult,
  VitalReading,
  VitalsSummary,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public retryable = false,
    public status = 500,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type TokenProvider = () => Promise<string | null>;

let tokenProvider: TokenProvider | null = null;

export function setApiTokenProvider(provider: TokenProvider | null) {
  tokenProvider = provider;
}

async function authHeaders(): Promise<Record<string, string>> {
  if (!tokenProvider) return {};
  const token = await tokenProvider();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(await authHeaders()),
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      `Cannot reach the API (${url}). Start the backend: cd apps/api && uvicorn app.main:app --reload --port 8000`,
      "NETWORK_ERROR",
      true,
      0,
    );
  }

  if (!res.ok) {
    let body: {
      error?: {
        code?: string;
        message?: string;
        retryable?: boolean;
        details?: Record<string, unknown>;
      };
    } = {};
    try {
      body = await res.json();
    } catch {
      /* empty */
    }
    throw new ApiError(
      formatApiError(body, res.statusText),
      body.error?.code,
      body.error?.retryable ?? false,
      res.status,
    );
  }

  return res.json() as Promise<T>;
}

function formatApiError(
  body: { error?: { message?: string; details?: Record<string, unknown> } },
  fallback: string,
): string {
  const msg = body.error?.message ?? fallback;
  const hint = body.error?.details?.hint;
  return typeof hint === "string" ? `${msg}. ${hint}` : msg;
}

export async function getPatientMe(): Promise<PatientRecord> {
  return request<PatientRecord>("/patients/me");
}

export async function updatePatientMe(body: {
  display_name?: string;
  lang_pref?: string;
  onboarding_completed?: boolean;
}): Promise<PatientRecord> {
  return request<PatientRecord>("/patients/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function createPatient(displayName?: string, langPref = "mr"): Promise<PatientRecord> {
  return request<PatientRecord>("/patients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: displayName, lang_pref: langPref }),
  });
}

export async function getPatient(patientId: string): Promise<PatientRecord> {
  return request<PatientRecord>(`/patients/${patientId}`);
}

export async function grantConsent(body: {
  patient_id: string;
  lang: string;
  purpose?: "document_processing";
  channel?: "web";
}): Promise<{ consent_id: string; granted_at: string }> {
  return request("/consent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_id: body.patient_id,
      purpose: body.purpose ?? "document_processing",
      lang: body.lang,
      channel: body.channel ?? "web",
    }),
  });
}

export async function getConsentStatus(
  patientId: string,
  purpose = "document_processing",
): Promise<{ patient_id: string; purpose: string; granted: boolean }> {
  const q = new URLSearchParams({ patient_id: patientId, purpose });
  return request(`/consent/status?${q}`);
}

export async function listDocuments(patientId: string): Promise<DocumentListItem[]> {
  return request<DocumentListItem[]>(`/patients/${patientId}/documents`);
}

export async function getBrief(patientId: string): Promise<DoctorBrief> {
  return request<DoctorBrief>(`/patients/${patientId}/brief`);
}

export async function getMemory(patientId: string): Promise<CurrentTruth> {
  return request<CurrentTruth>(`/patients/${patientId}/memory`);
}

export async function getSummary(patientId: string, lang = "mr"): Promise<PatientSummary> {
  return request<PatientSummary>(`/patients/${patientId}/summary?lang=${lang}`);
}

export async function getLatestShare(patientId: string): Promise<ShareCreateResponse> {
  return request<ShareCreateResponse>(`/patients/${patientId}/share`);
}

export async function ensurePatientShare(patientId: string): Promise<ShareCreateResponse> {
  try {
    return await getLatestShare(patientId);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      return createShare(patientId);
    }
    throw e;
  }
}

export async function createShare(patientId: string): Promise<ShareCreateResponse> {
  return request<ShareCreateResponse>("/shares", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id: patientId }),
  });
}

export async function getBriefSnapshot(
  token: string,
  view?: "specialist",
): Promise<ShareSnapshot> {
  const q = view === "specialist" ? "?view=specialist" : "";
  return request<ShareSnapshot>(`/brief/${token}${q}`);
}

export async function getJob(jobId: string): Promise<JobStatus> {
  return request<JobStatus>(`/jobs/${jobId}`);
}

export async function retryJob(jobId: string): Promise<{ job_id: string; status: string }> {
  return request(`/jobs/${jobId}/retry`, { method: "POST" });
}

export interface DocumentExplanation {
  document_id: string;
  explanation: string | null;
  source?: string | null;
}

export async function getDocumentExplanation(docId: string): Promise<DocumentExplanation> {
  return request<DocumentExplanation>(`/webchat/explanation/${docId}`);
}

export async function saathiChat(
  patientId: string,
  message: string,
  history: { role: string; content: string }[],
  lang = "mr",
): Promise<{ reply: string; action: string; safe: boolean }> {
  return request(`/patients/${patientId}/saathi`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, lang }),
  });
}

export async function uploadDocument(
  patientId: string,
  file: File,
  docType?: string,
): Promise<{ document_id: string; job_id: string; status: string; duplicate?: boolean }> {
  const form = new FormData();
  form.append("patient_id", patientId);
  form.append("file", file);
  if (docType) form.append("doc_type", docType);
  return request(`/documents`, { method: "POST", body: form });
}

export type BatchUploadItem = {
  document_id: string;
  job_id: string;
  status: string;
  duplicate?: boolean;
};

export async function uploadDocumentsBatch(
  patientId: string,
  files: File[],
  docType?: string,
): Promise<{ batch_id: string; items: BatchUploadItem[] }> {
  const form = new FormData();
  form.append("patient_id", patientId);
  for (const file of files) {
    form.append("files", file);
  }
  if (docType) form.append("doc_type", docType);
  return request(`/documents/batch`, { method: "POST", body: form });
}

export async function createReferral(body: {
  patient_id: string;
  specialty: string;
  reason?: string;
}): Promise<{ id: string; specialty: string; reason?: string | null }> {
  return request("/referrals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getReminders(patientId: string): Promise<ReminderSchedule> {
  return request(`/patients/${patientId}/reminders`);
}

export async function getBriefFhir(patientId: string): Promise<Record<string, unknown>> {
  const res = await request<{ bundle: Record<string, unknown> }>(
    `/patients/${patientId}/brief/fhir`,
  );
  return res.bundle;
}

export async function getEsanjeewaniExport(patientId: string): Promise<string> {
  const res = await request<{ text: string }>(
    `/patients/${patientId}/brief/exports/esanjeewani`,
  );
  return res.text;
}

export async function getPublicEsanjeewani(token: string): Promise<string> {
  const url = `${API_BASE}/brief/${token}/exports/esanjeewani`;
  const res = await fetch(url, { headers: { Accept: "text/plain" }, cache: "no-store" });
  if (!res.ok) throw new ApiError("Could not load eSanjeevani export", undefined, false, res.status);
  return res.text();
}

export async function getPublicFhirBundle(token: string): Promise<Record<string, unknown>> {
  const url = `${API_BASE}/brief/${token}/fhir`;
  const res = await fetch(url, { headers: { Accept: "application/json" }, cache: "no-store" });
  if (!res.ok) throw new ApiError("Could not load FHIR export", undefined, false, res.status);
  return res.json() as Promise<Record<string, unknown>>;
}

export async function deletePatientData(
  patientId: string,
): Promise<{ patient_id: string; documents: number; raw_files_purged: number }> {
  return request(`/patients/${patientId}/data`, { method: "DELETE" });
}

// --- Provider ---

export async function getProviderMe(): Promise<ProviderRecord> {
  return request<ProviderRecord>("/providers/me");
}

export async function updateProviderMe(body: {
  display_name?: string;
  specialty?: string;
  facility?: string;
  location?: string;
  bio?: string;
  consultation_fee?: number;
  experience_years?: number;
  languages?: string[];
}): Promise<ProviderRecord> {
  return request<ProviderRecord>("/providers/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// --- Triage ---

export async function runTriage(
  patientId: string,
  body: TriageRequest,
): Promise<TriageResult> {
  return request<TriageResult>(`/patients/${patientId}/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listTriage(patientId: string): Promise<TriageResult[]> {
  return request<TriageResult[]>(`/patients/${patientId}/triage`);
}

// --- Appointments ---

export async function createAppointment(body: {
  patient_id: string;
  specialty: string;
  provider_id?: string;
  slot_id?: string;
  scheduled_for?: string;
  referral_id?: string;
  triage_id?: string;
  notes?: string;
}): Promise<Appointment> {
  return request<Appointment>("/appointments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listAppointments(status?: string): Promise<Appointment[]> {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<Appointment[]>(`/appointments${q}`);
}

export async function getAppointment(appointmentId: string): Promise<Appointment> {
  return request<Appointment>(`/appointments/${appointmentId}`);
}

export async function patchAppointment(
  appointmentId: string,
  action: string,
  opts?: { reason?: string; new_slot_id?: string },
): Promise<Appointment> {
  return request<Appointment>(`/appointments/${appointmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...opts }),
  });
}

/** Accept/decline/complete/cancel with refresh-safe handling for stale UI state. */
export async function doctorAppointmentAction(
  appointmentId: string,
  action: string,
  opts?: { reason?: string; new_slot_id?: string },
): Promise<Appointment> {
  try {
    return await patchAppointment(appointmentId, action, opts);
  } catch (e) {
    if (!(e instanceof ApiError)) throw e;
    const msg = e.message;
    const terminal =
      (action === "accept" && msg.includes("status 'accepted'")) ||
      (action === "complete" && msg.includes("status 'completed'")) ||
      (action === "cancel" && msg.includes("status 'cancelled'")) ||
      (action === "cancel" && msg.includes("status 'completed'")) ||
      (action === "decline" && msg.includes("status 'declined'"));
    if (terminal) {
      return getAppointment(appointmentId);
    }
    throw e;
  }
}

export interface VisitSummary {
  encounter_id: string;
  appointment_id: string | null;
  status: string;
  notes: Array<{ note_type: string; body: string; at: string }>;
  prescriptions: Array<{ id: string; items: Record<string, unknown>; issued_at: string }>;
  disclaimer: string;
}

export async function getAppointmentVisitSummary(appointmentId: string): Promise<VisitSummary> {
  return request(`/appointments/${appointmentId}/visit-summary`);
}

export interface PatientContext {
  patient_id: string;
  brief: Record<string, unknown> | null;
  current_truth: CurrentTruth | null;
  past_briefs: Array<{
    brief_id: string;
    generated_at: string;
    one_line: string;
    chief_concern: string;
  }>;
  med_history: Record<string, Array<{
    date: string | null;
    dose: string | null;
    dose_unit: string | null;
    frequency: string | null;
    confidence: number;
  }>>;
  lab_trends: Record<string, Array<{
    value: unknown;
    unit: string | null;
    date: string | null;
    flag: string | null;
  }>>;
  vital_trends: Record<string, Array<{
    measured_at: string;
    value: Record<string, unknown>;
    flag: string | null;
  }>>;
}

export async function getAppointmentPatientContext(
  appointmentId: string,
): Promise<PatientContext> {
  return request<PatientContext>(`/appointments/${appointmentId}/patient-context`);
}

// --- Vitals ---

export async function createVital(
  patientId: string,
  body: {
    vital_type: string;
    value: Record<string, unknown>;
    unit: string;
    measured_at?: string;
    source?: string;
  },
): Promise<VitalReading> {
  return request<VitalReading>(`/patients/${patientId}/vitals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listVitals(
  patientId: string,
  vitalType?: string,
): Promise<VitalReading[]> {
  const q = vitalType ? `?vital_type=${encodeURIComponent(vitalType)}` : "";
  return request<VitalReading[]>(`/patients/${patientId}/vitals${q}`);
}

export async function getVitalsSummary(patientId: string): Promise<VitalsSummary> {
  return request<VitalsSummary>(`/patients/${patientId}/vitals/summary`);
}

// --- Health worker (F4) — `/workers/*` per Phase 6 API contract ---

export async function getHealthWorkerMe(): Promise<HealthWorkerRecord> {
  return request<HealthWorkerRecord>("/workers/me");
}

export async function registerPatientAsWorker(body: {
  display_name: string;
  phone?: string;
  lang_pref?: string;
  is_rural?: boolean;
}): Promise<PatientRecord> {
  return request<PatientRecord>("/workers/patients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listWorkerPatients(): Promise<AssignedPatient[]> {
  return request<AssignedPatient[]>("/workers/patients");
}

export async function proxyUploadForWorker(
  patientId: string,
  file: File,
  docType?: string,
): Promise<{ document_id: string; job_id: string; status: string }> {
  const form = new FormData();
  form.append("patient_id", patientId);
  form.append("file", file);
  if (docType) form.append("doc_type", docType);
  return request(`/workers/patients/${patientId}/documents`, { method: "POST", body: form });
}

export async function createWorkerShare(patientId: string): Promise<ShareCreateResponse> {
  return request<ShareCreateResponse>(`/workers/patients/${patientId}/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

// --- Admin analytics ---

export async function getAnalyticsOverview(
  from?: string,
  to?: string,
): Promise<AnalyticsOverview> {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const q = params.toString() ? `?${params}` : "";
  return request<AnalyticsOverview>(`/admin/analytics/overview${q}`);
}

// --- Admin doctor registry ---

export async function listAdminProviders(): Promise<AdminProviderRecord[]> {
  return request<AdminProviderRecord[]>("/admin/providers");
}

export async function grantAdminProvider(body: {
  phone: string;
  display_name?: string;
  specialty?: string;
  facility?: string;
}): Promise<AdminProviderRecord> {
  return request<AdminProviderRecord>("/admin/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function revokeAdminProvider(providerId: string): Promise<void> {
  await request(`/admin/providers/${providerId}`, { method: "DELETE" });
}

// --- Compliance ---

export async function withdrawConsent(patientId: string): Promise<{ withdrawn: boolean }> {
  return request("/consent/withdraw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id: patientId }),
  });
}

export async function getAccessLog(patientId: string): Promise<AccessLogEntry[]> {
  return request<AccessLogEntry[]>(`/patients/${patientId}/access-log`);
}

export async function getAuthMe(): Promise<import("./types").AuthMe> {
  return request("/auth/me");
}

/** Local dev: create dev admin via service role when configured. */
export async function ensureDevAdmin(): Promise<{ ok: boolean; message?: string }> {
  return request("/auth/dev/ensure-admin", { method: "POST" });
}

export async function searchProviders(params?: {
  specialty?: string;
  location?: string;
  lang?: string;
}): Promise<ProviderRecord[]> {
  const q = new URLSearchParams();
  if (params?.specialty) q.set("specialty", params.specialty);
  if (params?.location) q.set("location", params.location);
  if (params?.lang) q.set("lang", params.lang);
  const suffix = q.toString() ? `?${q}` : "";
  return request<ProviderRecord[]>(`/providers${suffix}`);
}

export async function getProviderPublic(id: string): Promise<ProviderRecord> {
  return request<ProviderRecord>(`/providers/${id}`);
}

export async function getProviderDashboard(): Promise<import("./types").ProviderDashboard> {
  return request("/providers/me/dashboard");
}

export async function listProviderSlots(
  providerId: string,
  from?: string,
  to?: string,
): Promise<import("./types").AppointmentSlot[]> {
  const q = new URLSearchParams();
  if (from) q.set("from", from);
  if (to) q.set("to", to);
  const suffix = q.toString() ? `?${q}` : "";
  return request(`/providers/${providerId}/slots${suffix}`);
}

export async function getPatientProfile(): Promise<import("./types").PatientProfile> {
  return request("/patients/me/profile");
}

export async function updatePatientProfile(
  body: Partial<import("./types").PatientProfile>,
): Promise<import("./types").PatientProfile> {
  return request("/patients/me/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getPatientTimeline(patientId: string): Promise<import("./types").TimelineEvent[]> {
  return request(`/patients/${patientId}/timeline`);
}

export async function getProviderPatientBrief(patientId: string): Promise<DoctorBrief> {
  return request(`/providers/patients/${patientId}/brief`);
}

export async function recordVideoJoined(appointmentId: string): Promise<{ ok: boolean }> {
  return request(`/appointments/${appointmentId}/video-joined`, { method: "POST" });
}

export async function listEncountersForPatient(patientId: string): Promise<import("./types").Encounter[]> {
  return request(`/encounters/patient/${patientId}/list`);
}

export async function addEncounterNote(
  encounterId: string,
  body: { note_type: string; body: string; is_draft?: boolean },
): Promise<{ id: string }> {
  return request(`/encounters/${encounterId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function draftEncounterSummary(
  encounterId: string,
): Promise<{ draft_note_id: string; body: string }> {
  return request(`/encounters/${encounterId}/draft-summary`, { method: "POST" });
}

export async function completeEncounter(encounterId: string): Promise<{ status: string }> {
  return request(`/encounters/${encounterId}/complete`, { method: "POST" });
}

export async function addEncounterPrescription(
  encounterId: string,
  items: Array<Record<string, string>>,
): Promise<{ id: string }> {
  return request(`/encounters/${encounterId}/prescriptions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
}

export interface InAppNotification {
  id: string;
  title: string;
  body: string;
  data?: Record<string, unknown> | null;
  status: string;
  created_at: string;
}

export async function listNotifications(): Promise<InAppNotification[]> {
  return request("/notifications");
}

export async function getUnreadNotificationCount(): Promise<number> {
  const res = await request<{ count: number }>("/notifications/unread-count");
  return res.count;
}

export async function markNotificationRead(id: string): Promise<void> {
  await request(`/notifications/${id}/read`, { method: "PATCH" });
}

export async function listProviderPatients(): Promise<Array<{ id: string; display_name?: string | null }>> {
  return request("/providers/me/patients");
}

export async function listAdminAppointments(status?: string): Promise<Appointment[]> {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/admin/appointments${q}`);
}

export async function getAdminProvider(id: string): Promise<AdminProviderRecord> {
  return request(`/admin/providers/${id}`);
}

export async function listAdminProviderCredentials(providerId: string): Promise<
  Array<{ id: string; doc_type: string; status: string; created_at: string }>
> {
  return request(`/admin/providers/${providerId}/credentials`);
}

export async function registerProvider(body: {
  display_name?: string;
  specialty?: string;
  facility?: string;
}): Promise<ProviderRecord> {
  return request("/providers/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function symptomChatTriage(body: {
  symptoms: string[];
  age?: number;
  existing_conditions?: string[];
  lang?: string;
}): Promise<{ priority: string; recommendation: string; message: string; disclaimer: string }> {
  return request("/chat/triage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function verifyAdminProvider(
  providerId: string,
  status: string,
): Promise<AdminProviderRecord> {
  return request(`/admin/providers/${providerId}/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export async function listAdminPatients(): Promise<PatientRecord[]> {
  return request("/admin/patients");
}

export async function setAdminUserRole(body: {
  phone: string;
  role: "patient" | "provider";
  display_name?: string;
  specialty?: string;
  facility?: string;
}): Promise<{
  supabase_user_id: string;
  phone: string;
  role: string;
  provider_id: string | null;
}> {
  return request("/admin/users/set-role", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function uploadProviderCredential(
  docType: string,
  file: File,
): Promise<{ id: string; doc_type: string; status: string }> {
  const form = new FormData();
  form.append("doc_type", docType);
  form.append("file", file);
  return request("/providers/me/credentials", { method: "POST", body: form });
}

export interface SupportTicket {
  id: string;
  subject: string;
  body: string;
  status: string;
  reporter_role: string;
  created_at: string;
}

export async function createSupportTicket(body: {
  subject: string;
  body: string;
}): Promise<SupportTicket> {
  return request("/support/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listSupportTickets(): Promise<SupportTicket[]> {
  return request("/support/tickets");
}

export async function updateSupportTicket(
  ticketId: string,
  status: string,
): Promise<{ id: string; status: string }> {
  return request(`/support/tickets/${ticketId}?status=${encodeURIComponent(status)}`, {
    method: "PATCH",
  });
}

export async function getNotificationPreferences(): Promise<
  Array<{ channel: string; enabled: boolean }>
> {
  return request("/notifications/preferences");
}

export async function updateNotificationPreference(
  channel: string,
  enabled: boolean,
): Promise<{ channel: string; enabled: boolean }> {
  return request("/notifications/preferences", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel, enabled }),
  });
}

export async function getProviderAvailability(): Promise<
  Array<{ day_of_week: number; start_time: string; end_time: string; slot_minutes: number }>
> {
  return request("/providers/me/availability");
}

export async function getEncounter(encounterId: string): Promise<Encounter & { consult_room?: string | null }> {
  return request(`/encounters/${encounterId}`);
}

export async function setProviderAvailability(
  rules: Array<{ day_of_week: number; start_time: string; end_time: string; slot_minutes: number }>,
): Promise<void> {
  await request("/providers/me/availability", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rules }),
  });
}

export async function uploadDocumentWithId(
  patientId: string,
  file: File,
  docType?: string,
  uploadId?: string,
): Promise<{ document_id: string; job_id: string; status: string }> {
  const form = new FormData();
  form.append("patient_id", patientId);
  form.append("file", file);
  if (docType) form.append("doc_type", docType);
  const headers: Record<string, string> = {};
  if (uploadId) headers["X-Upload-Id"] = uploadId;
  return request(`/documents`, { method: "POST", body: form, headers });
}

// --- Web Push (medicine reminders) ---

export async function getVapidKey(): Promise<{ public_key: string }> {
  return request<{ public_key: string }>("/push/vapid-key");
}

export async function subscribeToPush(body: {
  endpoint: string;
  p256dh: string;
  auth: string;
}): Promise<{ ok: boolean }> {
  return request("/push/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function unsubscribeFromPush(endpoint: string): Promise<{ ok: boolean }> {
  return request("/push/subscribe", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint }),
  });
}
