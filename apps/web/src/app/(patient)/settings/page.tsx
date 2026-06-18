"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, Trash2 } from "lucide-react";
import { deletePatientData, getAccessLog, getNotificationPreferences, updateNotificationPreference, withdrawConsent, createSupportTicket } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import { clearLocalConsent } from "@/lib/consent";
import { ErrorPanel } from "@/components/ui/state-panel";
import {
  isSubscribed,
  pushSupported,
  subscribeToReminders,
  unsubscribeFromReminders,
} from "@/lib/push";
import type { AccessLogEntry } from "@/lib/types";

export default function SettingsPage() {
  const { patient, ready, clearPatient } = usePatient();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [accessLog, setAccessLog] = useState<AccessLogEntry[]>([]);
  const [withdrew, setWithdrew] = useState(false);
  const [notifPrefs, setNotifPrefs] = useState<Array<{ channel: string; enabled: boolean }>>([]);
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketBody, setTicketBody] = useState("");
  const [ticketSent, setTicketSent] = useState(false);
  const [pushOn, setPushOn] = useState(false);
  const [pushBusy, setPushBusy] = useState(false);
  const [pushAvailable, setPushAvailable] = useState(false);

  useEffect(() => {
    if (!patient?.id) return;
    getAccessLog(patient.id)
      .then(setAccessLog)
      .catch(() => setAccessLog([]));
    getNotificationPreferences()
      .then(setNotifPrefs)
      .catch(() => setNotifPrefs([]));
  }, [patient?.id]);

  useEffect(() => {
    if (!pushSupported()) return;
    setPushAvailable(true);
    isSubscribed().then(setPushOn).catch(() => setPushOn(false));
  }, []);

  const toggleReminders = async () => {
    setPushBusy(true);
    try {
      if (pushOn) {
        await unsubscribeFromReminders();
        setPushOn(false);
      } else {
        const ok = await subscribeToReminders();
        setPushOn(ok);
      }
    } finally {
      setPushBusy(false);
    }
  };

  const toggleNotif = async (channel: string, enabled: boolean) => {
    await updateNotificationPreference(channel, enabled);
    setNotifPrefs((prefs) => {
      const existing = prefs.find((p) => p.channel === channel);
      if (existing) {
        return prefs.map((p) => (p.channel === channel ? { ...p, enabled } : p));
      }
      return [...prefs, { channel, enabled }];
    });
  };

  const onWithdrawConsent = async () => {
    if (!patient?.id) return;
    try {
      await withdrawConsent(patient.id);
      clearLocalConsent(patient.id);
      setWithdrew(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not withdraw consent");
    }
  };

  const onDelete = async () => {
    if (!patient?.id) return;
    setBusy(true);
    setError(null);
    try {
      await deletePatientData(patient.id);
      setDone(true);
      clearPatient();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete data");
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  if (!ready) return null;

  return (
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
        <ChevronLeft className="h-4 w-4" aria-hidden />
        Back
      </Link>
      <h1 className="text-[23px] font-semibold tracking-tight">Privacy & data</h1>
      <p className="mt-1 text-sm text-text-muted">
        Your documents are processed only with consent. Raw images are purged after the retention window.
      </p>

      {done && (
        <div className="mt-4 rounded-card border border-success-border bg-success-bg p-4 text-sm text-success">
          Your uploaded images were deleted. Structured summaries may remain until you contact support.
        </div>
      )}

      {error && (
        <div className="mt-4">
          <ErrorPanel title="Delete failed" message={error} />
        </div>
      )}

      {pushAvailable && (
        <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Medicine reminders</h2>
              <p className="mt-1 text-sm text-text-muted">
                {pushOn
                  ? "On — Saathi will nudge you when it's time to take your medicines."
                  : "Off — turn on a gentle nudge when it's time for your medicines."}
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={pushOn}
              aria-label="Medicine reminders"
              disabled={pushBusy}
              onClick={toggleReminders}
              className={`relative h-7 w-12 shrink-0 rounded-full transition-colors disabled:opacity-50 ${
                pushOn ? "bg-success" : "bg-border-warm"
              }`}
            >
              <span
                className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-transform ${
                  pushOn ? "translate-x-[22px]" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
        </section>
      )}

      <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
        <h2 className="text-sm font-semibold">Notification preferences</h2>
        <p className="mt-2 text-sm text-text-muted">
          Appointment reminders via SMS, email, or WhatsApp when configured.
        </p>
        <div className="mt-4 space-y-3">
          {(["sms", "email", "whatsapp"] as const).map((ch) => {
            const pref = notifPrefs.find((p) => p.channel === ch);
            const enabled = pref?.enabled ?? false;
            return (
              <label key={ch} className="flex items-center justify-between text-sm">
                <span className="font-semibold capitalize">{ch}</span>
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => void toggleNotif(ch, e.target.checked)}
                />
              </label>
            );
          })}
        </div>
      </section>

      <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
        <h2 className="text-sm font-semibold">Withdraw processing consent</h2>
        <p className="mt-2 text-sm text-text-muted">
          Stops new document processing until you consent again.
        </p>
        {withdrew ? (
          <p className="mt-3 text-sm text-success">Consent withdrawn.</p>
        ) : (
          <button
            type="button"
            onClick={onWithdrawConsent}
            className="mt-4 min-h-[44px] w-full rounded-[13px] border border-border text-sm font-semibold text-primary"
          >
            Withdraw consent
          </button>
        )}
      </section>

      {accessLog.length > 0 && (
        <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
          <h2 className="text-sm font-semibold">Who viewed my data</h2>
          <ul className="mt-3 space-y-2 text-sm text-text-muted">
            {accessLog.slice(0, 10).map((e) => (
              <li key={e.id}>
                {e.actor_role} · {e.action} ·{" "}
                {new Date(e.created_at).toLocaleString("en-IN")}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
        <h2 className="text-sm font-semibold">Delete my uploaded documents</h2>
        <p className="mt-2 text-sm text-text-muted">
          Removes stored prescription and lab images for your account. This cannot be undone.
        </p>
        {!confirming ? (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            disabled={!patient?.id || done}
            className="mt-4 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-[13px] border border-danger-border bg-danger-bg text-sm font-semibold text-danger disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" aria-hidden />
            Delete my data
          </button>
        ) : (
          <div className="mt-4 flex flex-col gap-2">
            <p className="text-sm font-semibold text-danger">Are you sure?</p>
            <button
              type="button"
              onClick={onDelete}
              disabled={busy}
              className="min-h-[44px] rounded-[13px] bg-danger text-sm font-semibold text-white"
            >
              {busy ? "Deleting…" : "Yes, delete uploaded images"}
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              className="min-h-[44px] rounded-[13px] border border-border text-sm font-semibold text-primary"
            >
              Cancel
            </button>
          </div>
        )}
      </section>

      <section className="mt-6 rounded-card border border-border bg-surface-raised p-4 shadow-card">
        <h2 className="text-sm font-semibold">Report an issue</h2>
        <p className="mt-2 text-sm text-text-muted">Open a support ticket for data or account disputes.</p>
        {ticketSent ? (
          <p className="mt-3 text-sm text-success">Ticket submitted. We will respond via your registered contact.</p>
        ) : (
          <div className="mt-3 space-y-2">
            <input
              value={ticketSubject}
              onChange={(e) => setTicketSubject(e.target.value)}
              placeholder="Subject"
              className="w-full rounded-card border border-border px-3 py-2 text-sm"
            />
            <textarea
              value={ticketBody}
              onChange={(e) => setTicketBody(e.target.value)}
              rows={3}
              placeholder="Describe the issue…"
              className="w-full rounded-card border border-border px-3 py-2 text-sm"
            />
            <button
              type="button"
              disabled={!ticketSubject.trim() || !ticketBody.trim()}
              onClick={async () => {
                await createSupportTicket({ subject: ticketSubject, body: ticketBody });
                setTicketSent(true);
              }}
              className="min-h-[44px] w-full rounded-[13px] border border-border text-sm font-semibold text-primary disabled:opacity-50"
            >
              Submit ticket
            </button>
          </div>
        )}
      </section>

      <p className="mt-6 text-xs text-text-faint">
        SETU is designed for DPDP consent and data minimization. This is not a HIPAA or GDPR certification.
      </p>
    </div>
  );
}
