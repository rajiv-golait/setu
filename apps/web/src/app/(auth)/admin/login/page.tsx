"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { AuthBrand } from "@/components/auth/auth-brand";
import { ensureDevAdmin } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";
import { roleFromMetadata } from "@/lib/auth/role";

const DEV_EMAIL = process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL ?? "itsmerajiv021@gmail.com";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState(DEV_EMAIL);
  const [password, setPassword] = useState("setu-admin-dev");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!SUPABASE_ENABLED) {
    return (
      <div className="flex min-h-screen items-center justify-center px-5">
        <p className="text-center text-text-muted">Supabase auth is disabled.</p>
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

  const signIn = async () => {
    setError(null);
    setLoading(true);
    const trimmedEmail = email.trim();
    try {
      const bootstrap = await ensureDevAdmin().catch(() => ({
        ok: false as const,
        message: "Could not reach the API. Is apps/api running?",
      }));

      if (!bootstrap.ok) {
        throw new Error(
          bootstrap.message ??
            "Add SUPABASE_SERVICE_ROLE_KEY to apps/api/.env, restart the API, then try again. " +
              "Find it in Supabase → Project Settings → API → service_role (secret).",
        );
      }

      const { error: err } = await supabase.auth.signInWithPassword({
        email: trimmedEmail,
        password,
      });

      if (err) {
        if (err.message.toLowerCase().includes("rate limit")) {
          throw new Error(
            "Supabase email rate limit exceeded. Wait about an hour, or add SUPABASE_SERVICE_ROLE_KEY " +
              "to apps/api/.env and restart the API so the admin account is created without email.",
          );
        }
        throw err;
      }

      const { data: userData } = await supabase.auth.getUser();
      const role = roleFromMetadata(
        userData.user?.app_metadata as Record<string, unknown> | undefined,
        userData.user?.email,
      );
      if (role !== "admin") {
        await supabase.auth.signOut();
        throw new Error(
          `This account is not an admin. Use ${DEV_EMAIL} or set NEXT_PUBLIC_DEV_ADMIN_EMAIL.`,
        );
      }
      router.replace("/admin/users");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-10 animate-setu-fade">
      <AuthBrand
        badge="Setu · Admin"
        title="Admin sign in"
        subtitle="Manage users, doctors, and platform operations."
      />

      <div className="space-y-4">
        <label className="block">
          <span className="text-sm font-semibold">Email</span>
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-2 w-full rounded-card border border-border bg-surface-raised px-4 py-3 text-base"
          />
        </label>
        <label className="block">
          <span className="text-sm font-semibold">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-2 w-full rounded-card border border-border bg-surface-raised px-4 py-3 text-base"
          />
        </label>
        <PrimaryButton disabled={loading || !email || !password} onClick={signIn}>
          {loading ? "Signing in…" : "Sign in"}
        </PrimaryButton>
      </div>

      {error && <p className="mt-4 text-sm text-danger">{error}</p>}

      <p className="mt-8 text-center text-sm text-text-muted">
        Default: <span className="font-semibold">{DEV_EMAIL}</span> /{" "}
        <span className="font-semibold">setu-admin-dev</span>
        <br />
        Requires <span className="font-semibold">SUPABASE_SERVICE_ROLE_KEY</span> in{" "}
        <span className="font-mono text-xs">apps/api/.env</span> — the API creates the account
        without sending email.
      </p>

      <p className="mt-4 text-center text-sm">
        <Link href="/login" className="font-semibold text-primary">
          Patient sign in
        </Link>
        {" · "}
        <Link href="/doctor/login" className="font-semibold text-primary">
          Doctor sign in
        </Link>
      </p>
    </div>
  );
}
