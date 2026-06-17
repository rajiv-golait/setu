"use client";

import { Wifi, WifiOff } from "lucide-react";
import { useOfflineQueue } from "@/lib/hooks/use-offline-queue";
import { useLocale } from "@/lib/hooks/use-locale";

export function ConnectionBadge() {
  const { connection, pendingCount, syncing } = useOfflineQueue();
  const { t } = useLocale();

  if (connection === "online" && pendingCount === 0 && !syncing) return null;

  const label =
    connection === "offline"
      ? "Offline — uploads will sync when online"
      : connection === "slow"
        ? "Slow connection"
        : syncing
          ? "Syncing uploads…"
          : pendingCount > 0
            ? `${pendingCount} ${t("offline.queued")}`
            : null;

  if (!label) return null;

  return (
    <div
      className={`mb-4 flex items-center gap-2 rounded-card px-3 py-2 text-xs font-semibold ${
        connection === "offline"
          ? "border border-warning/30 bg-warning-bg text-warning"
          : "border border-border bg-surface-raised text-text-muted"
      }`}
    >
      {connection === "offline" ? (
        <WifiOff className="h-3.5 w-3.5 shrink-0" aria-hidden />
      ) : (
        <Wifi className="h-3.5 w-3.5 shrink-0" aria-hidden />
      )}
      <span>{label}</span>
    </div>
  );
}
