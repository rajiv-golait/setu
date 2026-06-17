const KEY = "setu_upload_meta";

export interface UploadMeta {
  fileName: string;
  size: number;
  mime: string;
}

export function saveUploadMeta(meta: UploadMeta) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(meta));
}

export function loadUploadMeta(): UploadMeta | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as UploadMeta) : null;
  } catch {
    return null;
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function mimeLabel(mime: string): string {
  if (mime === "application/pdf") return "PDF";
  if (mime.startsWith("image/")) return mime.split("/")[1]?.toUpperCase() ?? "IMAGE";
  return "FILE";
}
