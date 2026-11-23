#!/usr/bin/env python3
"""Put painted level scenes into Jack's Hero Squad.

Each level can be painted as one picture from its layout guide. The painter
keeps the layout but nudges platforms about, so this tool finds the ground
the painter actually drew and slides each platform's standing spots onto it.
Stairs and bridges take the midpoint of their two ends.

Give it a folder of pictures named scene-01.png ... scene-30.png. For each
one it writes hero-squad/scenes/NN.webp and adds to that level, inside the
LEVELS block of hero-squad/index.html:
  scene: {src, w, h}   the picture and its size in squares
  spots: {"x,y": [u, v]}   where feet go, as fractions of the picture

Run:  python3 tools/fit_hero_scenes.py <folder> [--check <folder for overlay pictures>]

tools/hero_scene_guides.json records how each guide was framed (made by
tools/render_hero_guides.py). Rebuilding the levels with
build_hero_levels.py changes the maps, so the scenes must be repainted after.
"""
import json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "hero-squad"
SQUASH, RISE = 0.7, 0.46


def ground_mask(im, theme):
    """Pixels that look like walkable ground for this world."""
    a = np.asarray(im.convert("RGB")).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if theme == "meadow":       # grass, including sunlit yellow-green, and dirt paths
        m = ((g > b * 1.4) & (g > r * 0.97) & (g > 110)) | ((r > 150) & (g > 105) & (b < g * 0.8) & (r < g * 1.5) & (b > 40))
    elif theme == "cave":       # lit paving: warm grey-tan stone and moss, not the violet dark
        m = (r > 95) & (g > 85) & (b < r * 1.12) & (r + g + b > 300)
    else:                       # snow and pale ice
        m = (r > 190) & (g > 215) & (b > 225)
    return ndimage.binary_opening(m, iterations=2)


def fit(level, info, im):
    W, H = im.size
    k = W / info["cw"]
    ts = info["ts"] * k
    th, eh = ts * SQUASH, ts * RISE
    cx, cy = info["x0"] * ts, info["y0"] * ts
    cells = {(x, y): (h, t) for x, y, h, t in level["cells"]}
    m = ground_mask(im, level["theme"])
    ii = np.pad(m.astype(np.float64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    def frac(x0, y0, x1, y1):
        x0, y0, x1, y1 = [int(round(v)) for v in (x0, y0, x1, y1)]
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if x1 <= x0 or y1 <= y0:
            return 0
        return (ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]) / ((x1 - x0) * (y1 - y0))

    # platforms: floor squares joined at the same height
    seen, rooms = set(), []
    for c, (h, t) in cells.items():
        if t != "f" or c in seen:
            continue
        grp, q = [c], [c]
        seen.add(c)
        while q:
            x, y = q.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in cells and n not in seen and cells[n] == (h, "f"):
                    seen.add(n)
                    grp.append(n)
                    q.append(n)
        rooms.append((h, grp))
    spots, weak = {}, []
    step = max(2, ts / 24)
    for h, grp in rooms:
        xs, ys = [c[0] for c in grp], [c[1] for c in grp]
        X0, X1 = min(xs) * ts - cx, (max(xs) + 1) * ts - cx
        Y0, Y1 = min(ys) * th - h * eh - cy, (max(ys) + 1) * th - h * eh - cy
        best = None
        for sc in (1.0, 0.92, 0.84, 0.76):
            w, d = (X1 - X0) * sc, (Y1 - Y0) * sc
            for dy in np.arange(-1.6 * th, 0.9 * th, step):
                for dx in np.arange(-1.0 * ts, 1.0 * ts, step):
                    x0, y0 = (X0 + X1) / 2 + dx - w / 2, (Y0 + Y1) / 2 + dy - d / 2
                    inner = frac(x0, y0, x0 + w, y0 + d)
                    outer = frac(x0 - w * 0.12, y0 - d * 0.14, x0 + w * 1.12, y0 + d * 1.14)   # prefers the middle of the patch
                    score = inner + 0.6 * outer - 0.12 * (abs(dx) / ts + abs(dy) / th) - 0.5 * (1 - sc)
                    if best is None or score > best[0]:
                        best = (score, x0, y0, w, d, inner)
        _, x0, y0, w, d, inner = best
        if inner < 0.72:
            weak.append((min(xs), min(ys), round(inner, 2)))
        nx, ny = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        for x, y in grp:
            spots[(x, y)] = [(x0 + (x - min(xs) + 0.5) * w / nx) / W, (y0 + (y - min(ys) + 0.7) * d / ny) / H]
    # stairs and bridges sit between the squares at their two ends
    for _ in range(4):
        for c in cells:
            if c in spots:
                continue
            x, y = c
            t = cells[c][1]
            pairs = [((x, y - 1), (x, y + 1))] if t == "n" else [((x - 1, y), (x + 1, y))] if t in "ew" \
                else [((x - 1, y), (x + 1, y)), ((x, y - 1), (x, y + 1))]
            for a, b in pairs:
                if a in spots and b in spots:
                    spots[c] = [(spots[a][0] + spots[b][0]) / 2, (spots[a][1] + spots[b][1]) / 2]
                    break
    for c in cells:                       # a two-square bridge: space its squares evenly between the ends
        if c in spots:
            continue
        x, y = c
        for dx, dy in ((1, 0), (0, 1)):
            a, b = (x - dx, y - dy), (x + dx, y + dy)
            far = (x + 2 * dx, y + 2 * dy)
            near = (x - 2 * dx, y - 2 * dy)
            if a in spots and b in cells and far in spots:
                spots[c] = [spots[a][0] + (spots[far][0] - spots[a][0]) / 3, spots[a][1] + (spots[far][1] - spots[a][1]) / 3]
            elif b in spots and a in cells and near in spots:
                spots[c] = [spots[b][0] + (spots[near][0] - spots[b][0]) / 3, spots[b][1] + (spots[near][1] - spots[b][1]) / 3]
    missing = [c for c in cells if c not in spots]
    return {f"{x},{y}": [round(u, 4), round(v, 4)] for (x, y), (u, v) in spots.items()}, weak, missing


def overlay(level, spots, im, out):
    """The scene with every standing spot marked and every walkable step drawn as a line."""
    o = im.copy()
    d = ImageDraw.Draw(o)
    W, H = o.size
    r = max(4, W // 220)
    cells = {(x, y): (h, t) for x, y, h, t in level["cells"]}
    for (x, y), (h, t) in cells.items():
        for n in ((x + 1, y), (x, y + 1)):
            if n in cells and f"{x},{y}" in spots and f"{n[0]},{n[1]}" in spots:
                link = t != "f" or cells[n][1] != "f"
                if link or cells[n] == (h, t):
                    a, b = spots[f"{x},{y}"], spots[f"{n[0]},{n[1]}"]
                    d.line((a[0] * W, a[1] * H, b[0] * W, b[1] * H), fill=(255, 255, 0) if link else (255, 255, 255), width=max(2, r // 2))
    for key, (u, v) in spots.items():
        d.ellipse((u * W - r, v * H - r, u * W + r, v * H + r), fill=(255, 0, 255), outline=(255, 255, 255))
    for e in level["ents"]:
        u, v = spots[f"{e['x']},{e['y']}"]
        d.rectangle((u * W - r * 2, v * H - r * 5, u * W + r * 2, v * H - r), outline=(0, 0, 0), width=3)
    u, v = spots[f"{level['hero']['x']},{level['hero']['y']}"]
    d.rectangle((u * W - r * 2, v * H - r * 6, u * W + r * 2, v * H - r), outline=(255, 210, 63), width=4)
    o.save(out)


def main():
    src = Path(sys.argv[1])
    check = Path(sys.argv[sys.argv.index("--check") + 1]) if "--check" in sys.argv else None
    guides = json.loads((ROOT / "tools" / "hero_scene_guides.json").read_text())
    page = (GAME / "index.html").read_text()
    m = re.search(r"/\*LEVELS\*/(.*?)/\*END\*/", page, re.S)
    levels = json.loads(m.group(1))
    (GAME / "scenes").mkdir(exist_ok=True)
    if check:
        check.mkdir(parents=True, exist_ok=True)
    for i, level in enumerate(levels, 1):
        f = next((p for p in (src / f"scene-{i:02d}.png", src / f"scene-{i:02d}.jpg") if p.exists()), None)
        if not f:
            continue
        im = Image.open(f).convert("RGB")
        info = guides[str(i)]
        spots, weak, missing = fit(level, info, im)
        if missing:
            print(f"level {i}: no spot for {missing}; left on the pieced-together map")
            continue
        small = im.copy()
        small.thumbnail((2048, 2048), Image.LANCZOS)
        small.save(GAME / "scenes" / f"{i:02d}.webp", quality=84, method=6)
        level["scene"] = dict(src=f"scenes/{i:02d}.webp", w=round(info["w"], 4), h=round(info["w"] * im.size[1] / im.size[0], 4))
        level["spots"] = spots
        if check:
            overlay(level, spots, small, check / f"check-{i:02d}.jpg")
        print(f"level {i}: {len(spots)} spots" + (f", weak fit on platforms at {weak}" if weak else ""))
    blob = json.dumps(levels, separators=(",", ":"))
    page = page[:m.start()] + "/*LEVELS*/" + blob + "/*END*/" + page[m.end():]
    (GAME / "index.html").write_text(page)

    sw = (GAME / "sw.js").read_text()
    files = json.loads(re.search(r"const FILES=(\[.*?\]);", sw, re.S).group(1).replace("'", '"'))
    files = [f for f in files if not f.startswith("scenes/")] + sorted(f"scenes/{p.name}" for p in (GAME / "scenes").glob("*.webp"))
    sw = re.sub(r"const FILES=\[.*?\];", lambda _: "const FILES=" + str(files).replace(" ", "") + ";", sw, flags=re.S)
    ver = int(re.search(r"hero-squad-v(\d+)", sw).group(1)) + 1
    (GAME / "sw.js").write_text(re.sub(r"hero-squad-v\d+", f"hero-squad-v{ver}", sw))


if __name__ == "__main__":
    main()
