const CACHE = "iot-cache-v1";
const ASSETS = [
  "/", "/static/css/styles.css", "/static/js/app.js"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  e.respondWith(
    caches.match(req).then(cached => cached || fetch(req).catch(() => cached))
  );
});
