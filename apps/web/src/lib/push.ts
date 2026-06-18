import { getVapidKey, subscribeToPush, unsubscribeFromPush } from "@/lib/api";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const out = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i += 1) out[i] = rawData.charCodeAt(i);
  return out;
}

export function pushSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

/** Is there already an active push subscription in this browser? */
export async function isSubscribed(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await navigator.serviceWorker.ready;
    return (await reg.pushManager.getSubscription()) !== null;
  } catch {
    return false;
  }
}

/**
 * Requests permission, creates a push subscription, and registers it with the
 * backend (authenticated). Returns true only if fully subscribed.
 * Call this AFTER the user has accepted the in-app pre-prompt.
 */
export async function subscribeToReminders(): Promise<boolean> {
  if (!pushSupported()) return false;

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return false;

  const reg = await navigator.serviceWorker.ready;

  let publicKey: string;
  try {
    const { public_key } = await getVapidKey();
    if (!public_key) return false;
    publicKey = public_key;
  } catch {
    return false; // push not configured on the server
  }

  let subscription = await reg.pushManager.getSubscription();
  if (!subscription) {
    subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey) as BufferSource,
    });
  }

  const json = subscription.toJSON();
  const keys = json.keys ?? {};
  try {
    await subscribeToPush({
      endpoint: subscription.endpoint,
      p256dh: keys.p256dh ?? "",
      auth: keys.auth ?? "",
    });
    return true;
  } catch {
    return false;
  }
}

/** Turn off medicine reminders: remove the local subscription + backend row. */
export async function unsubscribeFromReminders(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (!sub) return true;
    await unsubscribeFromPush(sub.endpoint).catch(() => undefined);
    await sub.unsubscribe();
    return true;
  } catch {
    return false;
  }
}
