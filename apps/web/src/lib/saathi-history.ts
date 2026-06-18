export interface SaathiMessage {
  role: "user" | "assistant";
  content: string;
  action?: "urgent_care" | "see_doctor" | "monitor" | "none";
}

export const SAATHI_SESSION_KEY = "setu_saathi_history";
/** Set when Saathi has an unseen proactive message (drives the nav coral dot). */
export const SAATHI_UNREAD_KEY = "setu_saathi_unread";

export function loadSaathiHistory(): SaathiMessage[] {
  try {
    const raw = sessionStorage.getItem(SAATHI_SESSION_KEY);
    return raw ? (JSON.parse(raw) as SaathiMessage[]) : [];
  } catch {
    return [];
  }
}

export function saveSaathiHistory(msgs: SaathiMessage[]): void {
  try {
    sessionStorage.setItem(SAATHI_SESSION_KEY, JSON.stringify(msgs.slice(-20)));
  } catch {
    /* non-fatal */
  }
}

/** Append a proactive Saathi message and flag it unread (for the nav dot). */
export function pushSaathiMessage(msg: SaathiMessage): void {
  const next = [...loadSaathiHistory(), msg];
  saveSaathiHistory(next);
  try {
    sessionStorage.setItem(SAATHI_UNREAD_KEY, "1");
    window.dispatchEvent(new Event("saathi-unread"));
  } catch {
    /* non-fatal */
  }
}

export function hasSaathiUnread(): boolean {
  try {
    return sessionStorage.getItem(SAATHI_UNREAD_KEY) === "1";
  } catch {
    return false;
  }
}

export function clearSaathiUnread(): void {
  try {
    sessionStorage.removeItem(SAATHI_UNREAD_KEY);
    window.dispatchEvent(new Event("saathi-unread"));
  } catch {
    /* non-fatal */
  }
}
