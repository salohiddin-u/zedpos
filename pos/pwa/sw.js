// Version: 2 (Update this number whenever you change the manifest or icons)

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('/admin/')) {
        return; // Let Django handle admin requests normally
    }
    event.respondWith(fetch(event.request));
});