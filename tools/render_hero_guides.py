"""Render a plain layout guide for every Hero Squad level.

Each guide shows the level's platforms, stairs and bridges with no characters.
The guides are the layout reference when a level is painted as one scene, and
tools/hero_scene_guides.json records how each one was framed so that
tools/fit_hero_scenes.py can line the painting up with the level.

Needs Playwright and Chrome. Run:  python3 tools/render_hero_guides.py <output folder>
Before rendering, take the "scene" and "spots" entries out of the levels (or
rebuild them with build_hero_levels.py) so the guides show the pieced-together map.
"""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
URL=(ROOT/'hero-squad'/'index.html').as_uri()
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('guides')
W,H=1600,1200
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(channel='chrome')
        OUT.mkdir(parents=True, exist_ok=True); frames={}
        pg=await b.new_page(viewport={'width':W,'height':H+70}, device_scale_factor=1)
        await pg.goto(URL); await pg.wait_for_timeout(800)
        n=await pg.evaluate('LEVELS.length')
        for LV in range(n):
            info=await pg.evaluate('''(i)=>{
              startLevel(i);
              G.ents.forEach(e=>e.alive=false); G.introUntil=0;
              if(!window.sp0){ window.sp0=window.sprite; window.badge=function(){}; window.sprite=function(k){ if(k==='hero'||k==='key') return; return sp0.apply(null,arguments); }; }
              delete ART['back-'+G.theme]; document.getElementById('side').style.display='none'; G.hero.fx=-99; G.hero.fy=-99;
              const tall=G.H*SQUASH-G.topU;                       // map height in squares, cliffs excluded
              ts=Math.min(cw/(G.W+2.6), ch/(tall+3.4)); th=ts*SQUASH; eh=ts*RISE;
              cam.free=true; cam.x=-(cw-G.W*ts)/2; cam.y=G.topU*ts-1.2*ts-(ch-(tall+3.4)*ts)/2;
              return {ts, x0:cam.x/ts, y0:cam.y/ts, w:cw/ts, h:ch/ts, cw, ch};
            }''', LV)
            await pg.wait_for_timeout(450)
            el=await pg.query_selector('#cv'); await el.screenshot(path=str(OUT/f'block{LV+1}.png'))
            Image.open(OUT/f'block{LV+1}.png').convert('RGB').save(OUT/f'level-{LV+1:02d}.jpg', quality=90)
            (OUT/f'block{LV+1}.png').unlink()
            frames[str(LV+1)]=info
        (ROOT/'tools'/'hero_scene_guides.json').write_text(json.dumps(frames, separators=(',',':')))
        await b.close()
asyncio.run(main())
