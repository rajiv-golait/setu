"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/cn";

export function BackLink({
  href,
  label = "Back",
  className,
}: {
  href?: string;
  label?: string;
  className?: string;
}) {
  const router = useRouter();

  if (href) {
    return (
      <Link
        href={href}
        className={cn(
          "mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary",
          className,
        )}
      >
        <ChevronLeft className="h-4 w-4" aria-hidden />
        {label}
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={() => router.back()}
      className={cn(
        "mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary",
        className,
      )}
    >
      <ChevronLeft className="h-4 w-4" aria-hidden />
      {label}
    </button>
  );
}
