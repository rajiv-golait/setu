"use client";

import { useEffect, useState } from "react";
import { listQueuedUploads } from "@/lib/offline-queue";
import { useLocale } from "@/lib/hooks/use-locale";

export function OfflineQueueBanner() {
  const { t } = useLocale();
  const [count, setCount] = useState(0);

  useEffect(() => {
    const refresh = () => {
      listQueuedUploads().then((items) => setCount(items.length)).catch(() => setCount(0));
    };
    refresh();
    window.addEventListener("online", refresh);
    const id = setInterval(refresh, 10_000);
    return () => {
      window.removeEventListener("online", refresh);
      clearInterval(id);
    };
  }, []);

  if (count === 0) return null;

  return (
    <div className="mb-4 rounded-card border border-warning/30 bg-warning-bg px-4 py-3 text-sm text-warning">
      <span className="font-semibold">{count}</span> {t("offline.queued")}
    </div>
  );
}
