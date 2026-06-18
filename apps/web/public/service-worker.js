/* SETU PWA — app shell + background sync hook for offline upload outbox */
const CACHE = "setu-shell-v2";
const SHELL = [
  "/",
  "/icon.svg",
  "/manifest.json",
  "/apple-touch-icon.png",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ).then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.pathname.startsWith("/api/v1")) return;
  event.respondWith(
    fetch(request).catch(() => caches.match(request).then((r) => r ?? caches.match("/"))),
  );
});

self.addEventListener("sync", (event) => {
  if (event.tag === "setu-upload-sync") {
    event.waitUntil(Promise.resolve());
  }
});

self.addEventListener("push", (event) => {
  const d = event.data?.json() ?? {};
  // Deep-link target travels with the notification so the click lands on Today
  // (or the relevant screen) instead of a bare root.
  const url = d.url || (d.data && d.data.url) || "/";
  event.waitUntil(
    self.registration.showNotification(d.title ?? "Setu", {
      body: d.body ?? "",
      icon: "/icons/icon-192x192.png",
      badge: "/icons/icon-192x192.png",
      data: { url },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ("focus" in client) {
          client.navigate(target);
          return client.focus();
        }
      }
      return self.clients.openWindow(target);
    }),
  );
});
