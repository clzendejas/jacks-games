const CACHE='logans-coloring-book-v2';
const FILES=['./','index.html','logan.webp','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png','packs/packs.json'];
// Save the app shell, then every picture listed in packs.json, so the whole book works offline.
self.addEventListener('install',e=>{e.waitUntil((async()=>{
  const c=await caches.open(CACHE);
  await c.addAll(FILES);
  const packs=await (await c.match('packs/packs.json')).json();
  await Promise.all(packs.flatMap(p=>p.pages.map(g=>c.add('packs/'+p.id+'/'+g.id+'.svg').catch(()=>{}))));
  await self.skipWaiting();
})())});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
// Saved copy first when the network is slow; never hand a page back in place of a picture.
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
