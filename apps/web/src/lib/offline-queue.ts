const DB_NAME = "setu-offline";
const STORE = "uploads";
const DB_VERSION = 1;

export interface QueuedUpload {
  id: string;
  patientId: string;
  blob: Blob;
  docType: string;
  filename: string;
  createdAt: string;
  attempts: number;
  lastError?: string;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error);
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id" });
      }
    };
  });
}

export async function enqueueUpload(
  item: Omit<QueuedUpload, "createdAt" | "attempts">,
): Promise<void> {
  const db = await openDb();
  const row: QueuedUpload = {
    ...item,
    createdAt: new Date().toISOString(),
    attempts: 0,
  };
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(row);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
  if ("serviceWorker" in navigator) {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sync = (reg as ServiceWorkerRegistration & { sync?: { register: (tag: string) => Promise<void> } }).sync;
      await sync?.register("setu-upload-sync");
    } catch {
      /* background sync not supported */
    }
  }
}

export async function listQueuedUploads(): Promise<QueuedUpload[]> {
  const db = await openDb();
  const rows = await new Promise<QueuedUpload[]>((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result as QueuedUpload[]);
    req.onerror = () => reject(req.error);
  });
  db.close();
  return rows;
}

export async function removeQueuedUpload(id: string): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

export async function drainUploadQueue(
  uploadFn: (item: QueuedUpload) => Promise<void>,
): Promise<{ synced: number; failed: number }> {
  const items = await listQueuedUploads();
  let synced = 0;
  let failed = 0;
  for (const item of items) {
    try {
      await uploadFn(item);
      await removeQueuedUpload(item.id);
      synced++;
    } catch (e) {
      failed++;
      const db = await openDb();
      const updated = {
        ...item,
        attempts: item.attempts + 1,
        lastError: e instanceof Error ? e.message : "upload failed",
      };
      await new Promise<void>((resolve, reject) => {
        const tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).put(updated);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
      db.close();
    }
  }
  return { synced, failed };
}
