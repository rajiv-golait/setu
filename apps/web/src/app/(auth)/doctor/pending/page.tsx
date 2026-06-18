"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAuthMe } from "@/lib/api";
import { AuthBrand } from "@/components/auth/auth-brand";
import { PrimaryButton } from "@/components/ui/buttons";

export default function DoctorPendingPage() {
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    getAuthMe()
      .then((me) => setStatus(me.verification_status ?? "pending"))
      .catch(() => setStatus("pending"));
  }, []);

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-10">
      <AuthBrand
        badge="Setu · Doctor"
        title="Verification in progress"
        subtitle={`Your account is ${status ?? "pending"} admin review. Complete your profile while you wait.`}
        welcomeHref="/for-doctors"
      />
      <div className="flex flex-col gap-3">
        <Link href="/doctor/settings">
          <PrimaryButton>Complete your profile</PrimaryButton>
        </Link>
        <Link href="/doctor/login" className="text-center text-sm text-text-muted">
          Sign out
        </Link>
      </div>
    </div>
  );
}
