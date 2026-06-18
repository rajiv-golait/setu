"use client";

import { useEffect } from "react";
import { drainUploadQueue } from "@/lib/offline-queue";
import { uploadDocumentWithId } from "@/lib/api";

export function ServiceWorkerRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    // Register the SW only. Push subscription happens after the user accepts the
    // in-app pre-prompt (ReminderOptIn) — never silently on load.
    navigator.serviceWorker.register("/service-worker.js").catch(() => undefined);

    const syncQueue = () => {
      drainUploadQueue(async (item) => {
        const file = new File([item.blob], item.filename, {
          type: item.blob.type || "image/jpeg",
        });
        await uploadDocumentWithId(item.patientId, file, item.docType, item.id);
      }).catch(() => undefined);
    };

    window.addEventListener("online", syncQueue);
    syncQueue();
    return () => window.removeEventListener("online", syncQueue);
  }, []);

  return null;
}
