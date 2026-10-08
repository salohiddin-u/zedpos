

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim()); // Take control of the page immediately
});

self.addEventListener('fetch', (event) => {
    // Ignore Django admin requests
    if (event.request.url.includes('/admin/')) {
        return; 
    }
    
    // Try the network, if it fails (offline), return a basic fallback so the PWA doesn't crash
    event.respondWith(
        fetch(event.request).catch(() => {
            return new Response("You are currently offline.");
        })
    );
});