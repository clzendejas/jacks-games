const CACHE='rainbow-bottles-v2';
const FILES=['./','index.html','jack.webp','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
// Network first so updates show up right away; fall back to the saved copy when offline or slow.
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const saved=()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('index.html'));
  const fresh=fetch(e.request).then(res=>{
    if(res.ok){const copy=res.clone();caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});}
    return res;
  });
  const slow=new Promise(r=>setTimeout(r,2500)).then(saved);
  e.respondWith(Promise.race([fresh.catch(saved),slow]).then(r=>r||fresh));
});
