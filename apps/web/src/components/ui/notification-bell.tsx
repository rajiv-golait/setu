"use client";

import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import {
  getUnreadNotificationCount,
  listNotifications,
  markNotificationRead,
  type InAppNotification,
} from "@/lib/api";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);
  const [items, setItems] = useState<InAppNotification[]>([]);

  const refresh = () => {
    if (!SUPABASE_ENABLED) return;
    getUnreadNotificationCount().then(setCount).catch(() => setCount(0));
    listNotifications().then(setItems).catch(() => setItems([]));
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 30000);
    return () => clearInterval(t);
  }, []);

  if (!SUPABASE_ENABLED) return null;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          refresh();
        }}
        className="relative rounded-full p-2 text-primary"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute right-0 top-0 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-danger px-1 text-[10px] font-bold text-white">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-1 w-72 rounded-card border border-border bg-surface-raised shadow-lg">
          <p className="border-b border-border px-3 py-2 text-xs font-semibold uppercase text-text-muted">
            Notifications
          </p>
          <ul className="max-h-64 overflow-y-auto">
            {items.length === 0 ? (
              <li className="px-3 py-4 text-sm text-text-muted">No notifications yet.</li>
            ) : (
              items.map((n) => (
                <li key={n.id} className="border-b border-border px-3 py-2 text-sm">
                  <p className="font-semibold">{n.title}</p>
                  <p className="text-text-muted">{n.body}</p>
                  {n.status === "pending" && (
                    <button
                      type="button"
                      className="mt-1 text-xs font-semibold text-primary"
                      onClick={() => {
                        void markNotificationRead(n.id).then(refresh);
                      }}
                    >
                      Mark read
                    </button>
                  )}
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
