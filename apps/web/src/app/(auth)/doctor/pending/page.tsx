"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAuthMe } from "@/lib/api";

export default function DoctorPendingPage() {
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    getAuthMe()
      .then((me) => setStatus(me.verification_status ?? "pending"))
      .catch(() => setStatus("pending"));
  }, []);

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-5 py-10 text-center">
      <h1 className="text-2xl font-semibold">Verification in progress</h1>
      <p className="mt-3 text-sm text-text-muted">
        Your doctor account is {status ?? "pending"} admin review. Upload credentials in
        settings and contact your clinic admin if this takes more than 48 hours.
      </p>
      <div className="mt-6 flex flex-col gap-3">
        <Link href="/doctor/settings" className="font-semibold text-primary">
          Complete your profile
        </Link>
        <Link href="/login" className="text-sm text-text-muted">
          Sign out
        </Link>
      </div>
    </div>
  );
}
