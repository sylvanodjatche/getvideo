const CACHE_NAME = 'getvideo-v2';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((key) => caches.delete(key)));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Toujours Network First pour les assets dynamiques et l'API
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
