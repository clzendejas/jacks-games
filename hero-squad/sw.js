const CACHE='hero-squad-v11';
const FILES=['./','index.html','jack.webp','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png','art/hero.webp','art/goblin.webp','art/ogre.webp','art/slime.webp','art/bat.webp','art/mushroom.webp','art/skeleton.webp','art/imp.webp','art/dragon.webp','art/yeti.webp','art/add.webp','art/mul.webp','art/key.webp','art/chest.webp','art/door.webp','art/wall-meadow.webp','art/wall-cave.webp','art/wall-ice.webp','art/floor-meadow.webp','art/floor-cave.webp','art/floor-ice.webp','art/back-meadow.webp','art/back-cave.webp','art/back-ice.webp','art/cliff-meadow.webp','art/cliff-cave.webp','art/cliff-ice.webp','art/stairs-meadow.webp','art/stairs-cave.webp','art/stairs-ice.webp','art/stairs-side-meadow.webp','art/stairs-side-cave.webp','art/stairs-side-ice.webp','art/bridge-away.webp','art/deep-meadow.webp','art/deep-cave.webp','art/deep-ice.webp','art/flower-fairy.webp','art/frost-fairy.webp','art/star-fairy.webp','art/archer.webp','art/princess.webp','art/sorceress.webp','art/dragon-pup.webp','art/giant.webp','art/wolf-rider.webp','scenes/01.webp','scenes/02.webp','scenes/03.webp','scenes/04.webp','scenes/05.webp','scenes/06.webp','scenes/07.webp','scenes/08.webp','scenes/09.webp','scenes/10.webp','scenes/11.webp','scenes/12.webp','scenes/13.webp','scenes/14.webp','scenes/15.webp','scenes/16.webp','scenes/17.webp','scenes/18.webp','scenes/19.webp','scenes/20.webp','scenes/21.webp','scenes/22.webp','scenes/23.webp','scenes/24.webp','scenes/25.webp','scenes/26.webp','scenes/27.webp','scenes/28.webp','scenes/29.webp','scenes/30.webp'];
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
