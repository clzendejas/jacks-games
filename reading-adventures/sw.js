const CACHE='reading-adventures-v9';
const FILES=["./", "index.html", "jack.webp", "andika-700.woff2", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png", "sounds/s.mp3", "sounds/a.mp3", "sounds/t.mp3", "sounds/p.mp3", "sounds/i.mp3", "sounds/n.mp3", "sounds/m.mp3", "sounds/d.mp3", "sounds/g.mp3", "sounds/o.mp3", "sounds/c.mp3", "sounds/k.mp3", "sounds/e.mp3", "sounds/u.mp3", "sounds/r.mp3", "sounds/h.mp3", "sounds/b.mp3", "sounds/f.mp3", "sounds/l.mp3", "sounds/j.mp3", "sounds/v.mp3", "sounds/w.mp3", "sounds/x.mp3", "sounds/y.mp3", "sounds/z.mp3", "sounds/qu.mp3", "sounds/sh.mp3", "sounds/ch.mp3", "sounds/th.mp3", "sounds/ng.mp3"];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
// Saved copy first when the network is slow; never hand a page back in place of a sound or image.
self.addEventListener('fetch',e=>{
  const req=e.request; if(req.method!=='GET')return;
  e.respondWith((async()=>{
    const cache=await caches.open(CACHE);
    const hit=await cache.match(req,{ignoreSearch:true});
    const fresh=fetch(req).then(res=>{ if(res.ok) cache.put(req,res.clone()).catch(()=>{}); return res; });
    if(!hit){
      try{ return await fresh; }
      catch(err){ if(req.mode==='navigate'){ const page=await cache.match('index.html'); if(page) return page; } throw err; }
    }
    const quick=await Promise.race([fresh.catch(()=>null), new Promise(r=>setTimeout(()=>r(null),2500))]);
    return (quick && quick.ok) ? quick : hit;
  })());
});
