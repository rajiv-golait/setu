import { ApiError, getVapidKey, subscribeToPush, unsubscribeFromPush } from "@/lib/api";

export type PushFailureReason =
  | "unsupported"
  | "denied"
  | "no_vapid"
  | "no_sw"
  | "auth"
  | "server";

export type PushSubscribeResult =
  | { ok: true }
  | { ok: false; reason: PushFailureReason; message: string };

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

export function pushFailureMessage(result: Extract<PushSubscribeResult, { ok: false }>): string {
  return result.message;
}

async function ensurePushServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!("serviceWorker" in navigator)) return null;
  try {
    let reg = await navigator.serviceWorker.getRegistration("/");
    if (!reg) {
      reg = await navigator.serviceWorker.register("/service-worker.js", { scope: "/" });
    }
    const ready = await Promise.race([
      navigator.serviceWorker.ready,
      new Promise<null>((resolve) => setTimeout(() => resolve(null), 12_000)),
    ]);
    if (!ready) return null;
    return reg;
  } catch {
    return null;
  }
}

/** Is there already an active push subscription in this browser? */
export async function isSubscribed(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await ensurePushServiceWorker();
    if (!reg) return false;
    return (await reg.pushManager.getSubscription()) !== null;
  } catch {
    return false;
  }
}

/**
 * Requests permission, creates a push subscription, and registers it with the
 * backend (authenticated). Returns structured success/failure.
 */
export async function subscribeToReminders(): Promise<PushSubscribeResult> {
  if (!pushSupported()) {
    return {
      ok: false,
      reason: "unsupported",
      message: "This browser does not support medicine reminders.",
    };
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    return {
      ok: false,
      reason: "denied",
      message: "Notification permission was blocked. Allow notifications in browser settings and try again.",
    };
  }

  const reg = await ensurePushServiceWorker();
  if (!reg) {
    return {
      ok: false,
      reason: "no_sw",
      message: "Could not start the app helper for reminders. Refresh the page and try again.",
    };
  }

  let publicKey: string;
  try {
    const { public_key } = await getVapidKey();
    if (!public_key) {
      return {
        ok: false,
        reason: "no_vapid",
        message: "Reminders aren't available just yet — we'll turn them on soon.",
      };
    }
    publicKey = public_key;
  } catch (e) {
        if (e instanceof ApiError && (e.status === 503 || e.status === 0)) {
      return {
        ok: false,
        reason: "no_vapid",
        message: "Reminders aren't available just yet — we'll turn them on soon.",
      };
    }
    return {
      ok: false,
      reason: "server",
      message: e instanceof Error ? e.message : "Could not reach the server.",
    };
  }

  try {
    let subscription = await reg.pushManager.getSubscription();
    if (!subscription) {
      subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey) as BufferSource,
      });
    }

    const json = subscription.toJSON();
    const keys = json.keys ?? {};
    await subscribeToPush({
      endpoint: subscription.endpoint,
      p256dh: keys.p256dh ?? "",
      auth: keys.auth ?? "",
    });
    return { ok: true };
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      return {
        ok: false,
        reason: "auth",
        message: "Please sign in again, then turn reminders on.",
      };
    }
    return {
      ok: false,
      reason: "server",
      message: e instanceof Error ? e.message : "Could not save your reminder subscription.",
    };
  }
}

/** Turn off medicine reminders: remove the local subscription + backend row. */
export async function unsubscribeFromReminders(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await ensurePushServiceWorker();
    if (!reg) return false;
    const sub = await reg.pushManager.getSubscription();
    if (!sub) return true;
    await unsubscribeFromPush(sub.endpoint).catch(() => undefined);
    await sub.unsubscribe();
    return true;
  } catch {
    return false;
  }
}
