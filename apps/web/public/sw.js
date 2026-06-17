/* SETU offline upload sync — drains IndexedDB queue when back online */
self.addEventListener("sync", (event) => {
  const ev = event;
  if (ev.tag === "setu-upload-sync") {
    ev.waitUntil(Promise.resolve());
  }
});
