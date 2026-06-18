"use client";

import { useEffect, useState } from "react";
import { BellRing, Check } from "lucide-react";
import { SaathiAvatar } from "@/components/characters/saathi-avatar";
import { isSubscribed, pushSupported, subscribeToReminders } from "@/lib/push";

const DISMISS_KEY = "setu_reminder_optin_dismissed";

/**
 * Friendly in-app pre-prompt shown BEFORE the raw browser permission dialog.
 * Saathi asks first; only on "Yes" do we call the browser permission + subscribe.
 * Hides itself if push is unsupported, already subscribed, or dismissed.
 */
export function ReminderOptIn() {
  const [state, setState] = useState<"hidden" | "ask" | "working" | "on">("hidden");

  useEffect(() => {
    if (!pushSupported()) return;
    let cancelled = false;
    void (async () => {
      if (await isSubscribed()) {
        if (!cancelled) setState("on");
        return;
      }
      const dismissed = sessionStorage.getItem(DISMISS_KEY) === "1";
      if (!cancelled && !dismissed) setState("ask");
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state === "hidden") return null;

  if (state === "on") {
    return (
      <div className="flex items-center gap-2 rounded-card border border-success-border bg-success-bg px-4 py-3 text-sm text-success">
        <Check className="h-4 w-4 shrink-0" aria-hidden />
        Medicine reminders are on. I&apos;ll nudge you when it&apos;s time.
      </div>
    );
  }

  return (
    <div className="rounded-hero border border-saathi-border bg-saathi-bg p-4">
      <div className="flex items-start gap-3">
        <SaathiAvatar state="happy" size={48} label={null} />
        <div className="min-w-0 flex-1">
          <p className="font-display text-[15px] font-semibold text-text">
            Can I remind you about your medicines?
          </p>
          <p className="mt-0.5 text-sm text-text-muted">
            I&apos;ll send a gentle nudge at the right time — only if you want.
          </p>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              disabled={state === "working"}
              onClick={async () => {
                setState("working");
                const ok = await subscribeToReminders();
                setState(ok ? "on" : "ask");
              }}
              className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-[13px] bg-saathi px-4 text-sm font-semibold text-white disabled:opacity-50"
            >
              <BellRing className="h-4 w-4" aria-hidden />
              {state === "working" ? "Setting up…" : "Yes, remind me"}
            </button>
            <button
              type="button"
              onClick={() => {
                sessionStorage.setItem(DISMISS_KEY, "1");
                setState("hidden");
              }}
              className="min-h-[44px] rounded-[13px] border border-saathi-border px-4 text-sm font-semibold text-text-muted"
            >
              Not now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
