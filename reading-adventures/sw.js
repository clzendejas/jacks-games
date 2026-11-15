const CACHE='reading-adventures-v1';
const FILES=["./", "index.html", "jack.webp", "andika-700.woff2", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png", "sounds/s.mp3", "sounds/a.mp3", "sounds/t.mp3", "sounds/p.mp3", "sounds/i.mp3", "sounds/n.mp3", "sounds/m.mp3", "sounds/d.mp3", "sounds/g.mp3", "sounds/o.mp3", "sounds/c.mp3", "sounds/k.mp3", "sounds/e.mp3", "sounds/u.mp3", "sounds/r.mp3", "sounds/h.mp3", "sounds/b.mp3", "sounds/f.mp3", "sounds/l.mp3", "sounds/j.mp3", "sounds/v.mp3", "sounds/w.mp3", "sounds/x.mp3", "sounds/y.mp3", "sounds/z.mp3", "sounds/qu.mp3", "sounds/sh.mp3", "sounds/ch.mp3", "sounds/th.mp3", "sounds/ng.mp3"];
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
