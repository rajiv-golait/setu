"use client";

import { Suspense } from "react";
import LoginForm from "./login-form";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-text-muted">Loading…</div>}>
      <LoginForm />
    </Suspense>
  );
}
