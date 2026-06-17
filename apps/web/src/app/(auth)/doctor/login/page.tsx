"use client";

import { Suspense } from "react";
import LoginForm from "../../login/login-form";

export default function DoctorLoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-text-muted">Loading…</div>}>
      <LoginForm portal="provider" />
    </Suspense>
  );
}
