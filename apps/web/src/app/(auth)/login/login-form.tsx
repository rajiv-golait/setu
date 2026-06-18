"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthBrand } from "@/components/auth/auth-brand";
import { PrimaryButton } from "@/components/ui/buttons";
import { getAuthMe, getPatientMe, getProviderMe } from "@/lib/api";
import { homeForRole, roleFromMetadata, type UserRole } from "@/lib/auth/role";
import { createClient } from "@/lib/supabase/client";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";

export type LoginPortal = "patient" | "provider";

const PORTAL_COPY: Record<
  LoginPortal,
  { badge: string; title: string; subtitle: string; defaultNext: string; otherHref: string; otherLabel: string }
> = {
  patient: {
    badge: "Setu · Patient",
    title: "Sign in with your phone",
    subtitle: "We use your number only to secure your health record.",
    defaultNext: "/",
    otherHref: "/doctor/login",
    otherLabel: "Doctor or specialist? Sign in here",
  },
  provider: {
    badge: "Setu · Doctor",
    title: "Doctor sign in",
    subtitle: "For specialists and clinic staff. Use the mobile number registered with your clinic.",
    defaultNext: "/doctor",
    otherHref: "/login",
    otherLabel: "Patient? Sign in here",
  },
};

async function patientDestAfterLogin(): Promise<string> {
  const record = await getPatientMe().catch(() => null);
  return record?.onboarding_completed ? "/" : "/onboarding";
}

function roleAllowedOnPortal(portal: LoginPortal, role: UserRole): boolean {
  if (portal === "provider") return role === "provider" || role === "admin";
  return true;
}

function portalRoleError(portal: LoginPortal): string {
  if (portal === "provider") {
    return "This number is not registered as a doctor. Ask your admin to set role to provider in Supabase, or use patient sign-in.";
  }
  return "Sign-in failed for this portal.";
}

type LoginFormProps = {
  portal?: LoginPortal;
};

export default function LoginForm({ portal = "patient" }: LoginFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const copy = PORTAL_COPY[portal];
  const next = searchParams.get("next") ?? copy.defaultNext;

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
      const role = roleFromMetadata(
        userData.user?.app_metadata as Record<string, unknown> | undefined,
      );

      if (!roleAllowedOnPortal(portal, role)) {
        await supabase.auth.signOut();
        throw new Error(portalRoleError(portal));
      }

      let dest = next;
      try {
        const me = await getAuthMe();
        if (me.role === "provider" && me.verification_status !== "approved") {
          const provider = await getProviderMe().catch(() => null);
          if (!provider?.display_name || !provider?.specialty) {
            router.replace("/doctor/onboarding");
            return;
          }
          router.replace("/doctor/pending");
          return;
        }
        if (next.startsWith("/login") || next.startsWith("/doctor/login")) {
          dest = homeForRole(me.role as UserRole);
        } else if (portal === "provider") {
          dest = "/doctor";
        } else if (portal === "patient" && dest === "/") {
          dest = me.role === "patient" ? await patientDestAfterLogin() : homeForRole(me.role as UserRole);
        }
      } catch {
        if (next.startsWith("/login") || next.startsWith("/doctor/login")) {
          dest = homeForRole(role);
        } else if (portal === "provider") {
          dest = "/doctor";
        } else if (portal === "patient" && dest === "/") {
          dest = role === "patient" ? await patientDestAfterLogin() : homeForRole(role);
        }
      }

      router.replace(dest);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-10 animate-setu-fade">
      <AuthBrand
        badge={copy.badge}
        title={copy.title}
        subtitle={copy.subtitle}
        welcomeHref={portal === "patient" ? "/welcome" : "/for-doctors"}
      />

      {step === "phone" ? (
        <div className="mt-8 space-y-4">
          <label className="block">
            <span className="text-sm font-semibold">Mobile number</span>
            <input
              type="tel"
              inputMode="tel"
              placeholder="Enter 10-digit mobile number"
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
              placeholder="Enter 6-digit OTP"
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

      <p className="mt-8 text-center text-sm">
        <Link href={copy.otherHref} className="font-semibold text-primary">
          {copy.otherLabel}
        </Link>
      </p>
    </div>
  );
}
