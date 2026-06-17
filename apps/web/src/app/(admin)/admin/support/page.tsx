"use client";

import { useCallback, useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/role-shells";
import { listSupportTickets, updateSupportTicket } from "@/lib/api";
import type { SupportTicket } from "@/lib/api";

export default function AdminSupportPage() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTickets(await listSupportTickets());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load tickets");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const setStatus = async (id: string, status: string) => {
    await updateSupportTicket(id, status);
    await load();
  };

  return (
    <AdminShell>
      <p className="text-sm text-text-muted">Support and dispute tickets from patients, doctors, and workers.</p>
      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      <div className="mt-6">
        {loading ? (
          <p className="text-sm text-text-faint">Loading…</p>
        ) : tickets.length === 0 ? (
          <p className="text-sm text-text-muted">No tickets yet.</p>
        ) : (
          <ul className="space-y-4">
            {tickets.map((t) => (
              <li
                key={t.id}
                className="rounded-card border border-border bg-surface-raised p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold">{t.subject}</p>
                    <p className="mt-1 text-sm text-text-muted">{t.body}</p>
                    <p className="mt-2 text-xs text-text-faint">
                      {t.reporter_role} · {new Date(t.created_at).toLocaleString("en-IN")}
                    </p>
                  </div>
                  <span className="rounded-full border border-border px-2 py-0.5 text-xs font-semibold capitalize">
                    {t.status}
                  </span>
                </div>
                {t.status === "open" && (
                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setStatus(t.id, "in_progress")}
                      className="text-sm font-semibold text-primary"
                    >
                      Mark in progress
                    </button>
                    <button
                      type="button"
                      onClick={() => setStatus(t.id, "resolved")}
                      className="text-sm font-semibold text-success"
                    >
                      Resolve
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </AdminShell>
  );
}
