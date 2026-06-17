import { API_BASE } from "./constants";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

export async function subscribeToReminders(): Promise<void> {
  if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window)) {
    return;
  }

  // Only subscribe if the user has already granted permission or hasn't been asked.
  const permission = await Notification.requestPermission();
  if (permission !== "granted") return;

  const reg = await navigator.serviceWorker.ready;

  // Fetch VAPID public key — if push isn't configured, server returns 503 and we bail.
  let publicKey: string;
  try {
    const res = await fetch(`${API_BASE}/push/vapid-key`);
    if (!res.ok) return;
    const data = await res.json();
    publicKey = data.public_key;
  } catch {
    return;
  }

  const existing = await reg.pushManager.getSubscription();
  if (existing) {
    // Already subscribed — ensure it's registered with our backend.
    await _registerWithBackend(existing);
    return;
  }

  const subscription = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey),
  });

  await _registerWithBackend(subscription);
}

async function _registerWithBackend(sub: PushSubscription): Promise<void> {
  const json = sub.toJSON();
  const keys = json.keys ?? {};
  try {
    await fetch(`${API_BASE}/push/subscribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        endpoint: sub.endpoint,
        p256dh: keys.p256dh ?? "",
        auth: keys.auth ?? "",
      }),
    });
  } catch {
    // Non-fatal — push subscription will be retried on next app load.
  }
}
