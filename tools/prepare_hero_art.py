#!/usr/bin/env python3
"""Turn raw character pictures into game art for Jack's Hero Squad.

Give it a folder of pictures named after tools/hero_art_sources.txt
(hero.png, goblin.png, floor-meadow.png, ...). Characters and objects have
their white background cut away and are trimmed; floors and back walls are
only resized. Results go to hero-squad/art/ as .webp, and the game page and
its offline list are updated to use whatever is there.

Run:  python3 tools/prepare_hero_art.py <folder of raw pictures>
"""
import re, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "hero-squad"
ART = GAME / "art"
IN_GAME = ["hero", "goblin", "ogre", "slime", "bat", "mushroom", "skeleton", "imp", "dragon", "yeti",
           "add", "mul", "key", "chest", "door", "wall-meadow", "wall-cave", "wall-ice",
           "floor-meadow", "floor-cave", "floor-ice", "back-meadow", "back-cave", "back-ice",
           "cliff-meadow", "cliff-cave", "cliff-ice", "stairs-meadow", "stairs-cave", "stairs-ice",
           "stairs-side-meadow", "stairs-side-cave", "stairs-side-ice", "bridge-away",
           "deep-meadow", "deep-cave", "deep-ice",
           "flower-fairy", "frost-fairy", "star-fairy", "archer", "princess", "sorceress", "dragon-pup", "giant", "wolf-rider"]


def kinds():
    out = {}
    for line in (ROOT / "tools" / "hero_art_sources.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, kind, _ = line.split()
            out[name] = kind
    return out


# pictures where flat white is also trapped inside the outline (under an arm, inside a bow or a key ring)
POCKETS = {"bridge-away", "goblin", "archer", "sorceress", "skeleton", "key", "giant", "frost-fairy", "wolf-rider", "princess", "hero"}
# pockets edged with soft shading need a looser test
LOOSE = {"key": 0.4, "archer": 0.4, "bridge-away": 0.3}
# pictures painted on a plain backdrop that is not white: the backdrop is whatever colour the corner is
TINTED = {"stairs-side-ice"}
# pictures with a pale glow around them, which needs a wider idea of "white"
GLOW = {"mul": 205}


def cut_out(im, name=""):
    """Remove the white that touches the picture's edge; keep white inside outlines."""
    rgb = np.asarray(im.convert("RGB")).astype(np.int16)
    if name in TINTED:
        white = np.abs(rgb - rgb[2, 2]).max(axis=2) < 20
    else:
        white = rgb.min(axis=2) > GLOW.get(name, 236)
    labels, count = ndimage.label(white)
    edge = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    edge.discard(0)
    bg = np.isin(labels, list(edge))
    if name in POCKETS:
        # a trapped pocket of background is large and perfectly flat white; painted whites are shaded
        pure = rgb.min(axis=2) >= 253
        sizes = ndimage.sum(white, labels, range(1, count + 1))
        flat = ndimage.sum(pure, labels, range(1, count + 1))
        need = white.size * 0.0004
        for i in range(1, count + 1):
            if i not in edge and sizes[i - 1] > need and flat[i - 1] > LOOSE.get(name, 0.85) * sizes[i - 1]:
                bg |= labels == i
    bg = ndimage.binary_dilation(bg, iterations=2 if name in GLOW else 1)   # eat the pale fringe
    alpha = Image.fromarray((~bg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    box = Image.fromarray((~bg * 255).astype(np.uint8)).getbbox()
    return out.crop(box) if box else out


def main():
    src = Path(sys.argv[1])
    ART.mkdir(exist_ok=True)
    kind = kinds()
    for f in sorted(src.iterdir()):
        name = f.stem
        if name not in kind or f.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            continue
        im = Image.open(f)
        if kind[name] == "cut":
            im = cut_out(im, name)
            im.thumbnail((520, 520), Image.LANCZOS)
        else:
            im = im.convert("RGB")
            im.thumbnail((1600, 1600), Image.LANCZOS)
        im.save(ART / f"{name}.webp", quality=88, method=6)
        print("made", name, im.size)

    have = [n for n in IN_GAME if (ART / f"{n}.webp").exists()]
    page = (GAME / "index.html").read_text()
    table = "{" + ",".join(f"'{n}':'art/{n}.webp'" for n in have) + "}"
    page, n = re.subn(r"const ART_FILES = \{.*?\};", lambda m: f"const ART_FILES = {table};", page, flags=re.S)
    assert n == 1
    (GAME / "index.html").write_text(page)

    sw = (GAME / "sw.js").read_text()
    files = ["./", "index.html", "jack.webp", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"]
    files += [f"art/{n}.webp" for n in have]
    files += sorted(f"scenes/{p.name}" for p in (GAME / "scenes").glob("*.webp"))
    sw = re.sub(r"const FILES=\[.*?\];", lambda m: "const FILES=" + str(files).replace(" ", "") + ";", sw, flags=re.S)
    ver = int(re.search(r"hero-squad-v(\d+)", sw).group(1)) + 1
    sw = re.sub(r"hero-squad-v\d+", f"hero-squad-v{ver}", sw)
    (GAME / "sw.js").write_text(sw)
    print(len(have), "pictures in the game; offline list is version", ver)


if __name__ == "__main__":
    main()
