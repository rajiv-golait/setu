/* SETU PWA — app shell + background sync hook for offline upload outbox */
const CACHE = "setu-shell-v1";
const SHELL = ["/", "/icon.svg", "/manifest.json"];

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
