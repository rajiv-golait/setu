"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { createClient } from "@/lib/supabase/client";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";

  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!SUPABASE_ENABLED) {
    return (
      <div className="flex min-h-screen items-center justify-center px-5">
        <p className="text-center text-text-muted">
          Supabase auth is disabled. Use the app directly — no login required.
        </p>
      </div>
    );
  }

  const supabase = createClient();
  if (!supabase) {
    return (
      <div className="flex min-h-screen items-center justify-center px-5">
        <p className="text-center text-danger">Supabase is not configured.</p>
      </div>
    );
  }

  const normalizedPhone = phone.startsWith("+") ? phone : `+91${phone.replace(/\D/g, "")}`;

  const sendOtp = async () => {
    setError(null);
    setLoading(true);
    try {
      const { error: err } = await supabase.auth.signInWithOtp({ phone: normalizedPhone });
      if (err) throw err;
      setStep("otp");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not send OTP");
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    setError(null);
    setLoading(true);
    try {
      const { error: err } = await supabase.auth.verifyOtp({
        phone: normalizedPhone,
        token: otp,
        type: "sms",
      });
      if (err) throw err;
      const { data: userData } = await supabase.auth.getUser();
      const role = (userData.user?.app_metadata as { role?: string } | undefined)?.role;
      let dest = next.startsWith("/login") ? "/onboarding" : next;
      if (role === "provider") dest = "/doctor";
      else if (role === "health_worker") dest = "/worker";
      else if (role === "admin") dest = "/admin";
      router.replace(dest);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-10 animate-setu-fade">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">Setu</p>
      <h1 className="mt-1 text-[26px] font-semibold">Sign in with your phone</h1>
      <p className="mt-2 text-sm text-text-muted">
        We use your number only to secure your health record.
      </p>

      {step === "phone" ? (
        <div className="mt-8 space-y-4">
          <label className="block">
            <span className="text-sm font-semibold">Mobile number</span>
            <input
              type="tel"
              inputMode="tel"
              placeholder="9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="mt-2 w-full rounded-card border border-border bg-surface-raised px-4 py-3 text-base"
            />
          </label>
          <PrimaryButton disabled={loading || phone.replace(/\D/g, "").length < 10} onClick={sendOtp}>
            {loading ? "Sending…" : "Send OTP"}
          </PrimaryButton>
        </div>
      ) : (
        <div className="mt-8 space-y-4">
          <p className="text-sm text-text-muted">Code sent to {normalizedPhone}</p>
          <label className="block">
            <span className="text-sm font-semibold">Enter OTP</span>
            <input
              type="text"
              inputMode="numeric"
              placeholder="123456"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="mt-2 w-full rounded-card border border-border bg-surface-raised px-4 py-3 text-base tracking-widest"
            />
          </label>
          <PrimaryButton disabled={loading || otp.length < 4} onClick={verifyOtp}>
            {loading ? "Verifying…" : "Verify & continue"}
          </PrimaryButton>
          <button
            type="button"
            onClick={() => setStep("phone")}
            className="text-sm font-semibold text-primary"
          >
            Change number
          </button>
        </div>
      )}

      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
    </div>
  );
}
