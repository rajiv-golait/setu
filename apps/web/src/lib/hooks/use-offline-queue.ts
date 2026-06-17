"use client";

import { useCallback, useEffect, useState } from "react";
import {
  drainUploadQueue,
  listQueuedUploads,
  type QueuedUpload,
} from "@/lib/offline-queue";
import { uploadDocumentWithId } from "@/lib/api";

export type ConnectionState = "online" | "offline" | "slow";

export function useOfflineQueue() {
  const [queue, setQueue] = useState<QueuedUpload[]>([]);
  const [connection, setConnection] = useState<ConnectionState>("online");
  const [syncing, setSyncing] = useState(false);

  const refresh = useCallback(() => {
    listQueuedUploads()
      .then(setQueue)
      .catch(() => setQueue([]));
  }, []);

  const sync = useCallback(async () => {
    if (!navigator.onLine || syncing) return;
    setSyncing(true);
    try {
      await drainUploadQueue(async (item) => {
        const file = new File([item.blob], item.filename, {
          type: item.blob.type || "image/jpeg",
        });
        await uploadDocumentWithId(item.patientId, file, item.docType, item.id);
      });
    } finally {
      setSyncing(false);
      refresh();
    }
  }, [syncing, refresh]);

  useEffect(() => {
    const updateConnection = () => {
      if (!navigator.onLine) {
        setConnection("offline");
        return;
      }
      const conn = (navigator as Navigator & { connection?: { effectiveType?: string } })
        .connection;
      const slow =
        conn?.effectiveType === "2g" || conn?.effectiveType === "slow-2g";
      setConnection(slow ? "slow" : "online");
    };

    updateConnection();
    refresh();
    const onOnline = () => {
      updateConnection();
      sync();
    };
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", updateConnection);
    const id = setInterval(refresh, 12_000);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", updateConnection);
      clearInterval(id);
    };
  }, [refresh, sync]);

  const pending = queue.filter((q) => q.attempts < 5);
  const failed = queue.filter((q) => q.attempts >= 5);

  return {
    queue: pending,
    failed,
    pendingCount: pending.length,
    failedCount: failed.length,
    connection,
    syncing,
    refresh,
    sync,
  };
}
