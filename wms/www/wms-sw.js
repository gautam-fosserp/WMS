// WMS service worker. Bump VERSION to force clients to drop old caches.
const VERSION = 'v1'
const CACHE = `wms-static-${VERSION}`

const OFFLINE_HTML = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WMS offline</title>
<style>body{font-family:system-ui,sans-serif;background:#f8fafc;color:#0f172a;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;text-align:center;padding:24px}
button{margin-top:16px;padding:10px 20px;border:0;border-radius:12px;background:#0f172a;color:#fff;font-size:16px}</style></head>
<body><div><h1>You're offline</h1><p>Check your connection and try again.</p>
<button onclick="location.reload()">Retry</button></div></body></html>`

self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  if (req.method !== 'GET') return
  const url = new URL(req.url)
  if (url.origin !== self.location.origin) return

  // Pages: always network (they carry the CSRF token); friendly page when offline
  if (req.mode === 'navigate' && url.pathname.startsWith('/wms-mobile')) {
    event.respondWith(
      fetch(req).catch(() => new Response(OFFLINE_HTML, {
        status: 503,
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      }))
    )
    return
  }

  // Built frontend files have hashed names, so cache-first is safe
  if (url.pathname.startsWith('/assets/wms/frontend/')) {
    event.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone()
          caches.open(CACHE).then((c) => c.put(req, copy))
        }
        return res
      }))
    )
  }
  // Everything else, including /api/*, goes straight to the network
})
