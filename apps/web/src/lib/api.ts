import { API_BASE } from "./constants";
import type {
  CurrentTruth,
  DoctorBrief,
  DocumentListItem,
  JobStatus,
  PatientRecord,
  PatientSummary,
  ShareCreateResponse,
  ShareSnapshot,
} from "./types";

class ApiError extends Error {
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let body: { error?: { code?: string; message?: string; retryable?: boolean } } = {};
    try {
      body = await res.json();
    } catch {
      /* empty */
    }
    throw new ApiError(
      body.error?.message ?? res.statusText,
      body.error?.code,
      body.error?.retryable ?? false,
      res.status,
    );
  }

  return res.json() as Promise<T>;
}

export async function createPatient(displayName?: string): Promise<PatientRecord> {
  return request<PatientRecord>("/patients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: displayName, lang_pref: "mr" }),
  });
}

export async function getPatient(patientId: string): Promise<PatientRecord> {
  return request<PatientRecord>(`/patients/${patientId}`);
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

export async function uploadDocument(
  patientId: string,
  file: File,
): Promise<{ document_id: string; job_id: string; status: string }> {
  const form = new FormData();
  form.append("patient_id", patientId);
  form.append("file", file);
  return request(`/documents`, { method: "POST", body: form });
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

export { ApiError };
