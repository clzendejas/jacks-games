#!/usr/bin/env python3
"""Draw the coloring pages for Logan's Coloring Book.

Writes logans-coloring-book/packs/<pack>/<page>.svg and packs/packs.json.
Each page is plain line art made of simple shapes, back to front. A shape
with data-n="3" is a section to color with color number 3 of that page;
the colors are listed in the svg's data-palette. Shapes with data-fix are
already filled in (eyes), and class "ln" shapes are just lines.

To add a page: write a function below, add it to PACKS, run this script.
"""
import json, math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "logans-coloring-book" / "packs"
INK = "#33263f"

SKY, GRASS, SUN, SAND, WATER, CLOUD = "#9ad8ff", "#86d95b", "#ffd23f", "#f6dc9a", "#7fd0f2", "#e4f3ff"
PINK, HOT, RED, ORANGE, PURPLE, LAV = "#ffa3c8", "#ff6fae", "#f2545b", "#ff9a3d", "#a97bff", "#dccfff"
TEAL, BLUE, BROWN, CREAM, GOLD, LEAF = "#3fd0c0", "#5b8cff", "#8a5a34", "#ffe9c4", "#ffc533", "#4fbf6b"
BLUSH = "#ffe3f1"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Page:
    def __init__(self, title):
        self.title, self.pal, self.el, self.tf = title, {}, [], ""

    def _attrs(self, col, rot=None, sw=None):
        a = ""
        if col is None:
            a += ' class="ln" fill="none"'
        elif col.startswith("!"):
            a += f' data-fix="1" fill="{col[1:]}"'
        else:
            if col not in self.pal:
                self.pal[col] = len(self.pal) + 1
            a += f' data-n="{self.pal[col]}"'
        if sw is not None:
            a += f' stroke-width="{sw}"' if sw else ' stroke="none"'
        t = self.tf + (f" rotate({f(rot[0])} {f(rot[1])} {f(rot[2])})" if rot else "")
        if t.strip():
            a += f' transform="{t.strip()}"'
        return a

    def e(self, col, cx, cy, rx, ry, rot=0, sw=None):
        self.el.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}"{self._attrs(col, (rot, cx, cy) if rot else None, sw)}/>')

    def c(self, col, cx, cy, r, sw=None):
        self.el.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}"{self._attrs(col, None, sw)}/>')

    def r(self, col, x, y, w, h, rx=0, rot=0, sw=None):
        self.el.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(rx)}"{self._attrs(col, (rot, x + w / 2, y + h / 2) if rot else None, sw)}/>')

    def p(self, col, d, sw=None):
        self.el.append(f'<path d="{d}"{self._attrs(col, None, sw)}/>')

    def ln(self, d, sw=5):
        self.p(None, d, sw)

    def eye(self, x, y, r=11):
        self.c("!" + INK, x, y, r, 0)
        self.c("!#ffffff", x + r * 0.32, y - r * 0.36, r * 0.34, 0)

    def bigeye(self, x, y, r=24):
        self.c("!#ffffff", x, y, r)
        self.eye(x + r * 0.15, y + r * 0.1, r * 0.55)

    def smile(self, x, y, w, h=None):
        h = w * 0.7 if h is None else h
        self.ln(f"M{f(x - w)} {f(y)} Q{f(x)} {f(y + h)} {f(x + w)} {f(y)}")

    def svg(self):
        pal = " ".join(f"{n}:{c}" for c, n in self.pal.items())
        body = "\n".join(self.el)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" data-title="{self.title}" data-palette="{pal}" '
                f'fill="#ffffff" stroke="{INK}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">\n{body}\n</svg>\n')


# ---------- shape helpers (each returns a path "d") ----------
def scallop(cx, cy, rx, ry, n, start=0.0, bulge=1.12):
    pts = [(cx + rx * math.cos(start + 2 * math.pi * k / n), cy + ry * math.sin(start + 2 * math.pi * k / n)) for k in range(n)]
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for k in range(1, n + 1):
        a, b = pts[k - 1], pts[k % n]
        r = math.dist(a, b) / 2 * bulge
        d += f" A{f(r)} {f(r)} 0 0 1 {f(b[0])} {f(b[1])}"
    return d + "Z"


def smooth(pts, seg=10):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(seg):
            t = s / seg
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def tube(pts, w0, w1=None):
    """A fat smooth line through pts, w0 wide at the start and w1 at the end."""
    w1 = w0 if w1 is None else w1
    P = smooth(pts)
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        m = math.hypot(tx, ty) or 1
        h = (w0 + (w1 - w0) * i / (n - 1)) / 2
        L.append((x - ty / m * h, y + tx / m * h))
        R.append((x + ty / m * h, y - tx / m * h))
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in L)
    d += f" A{f(w1 / 2)} {f(w1 / 2)} 0 0 0 {f(R[-1][0])} {f(R[-1][1])} L"
    d += " L".join(f"{f(x)} {f(y)}" for x, y in reversed(R))
    d += f" A{f(w0 / 2)} {f(w0 / 2)} 0 0 0 {f(L[0][0])} {f(L[0][1])}Z"
    return d


def heart(cx, cy, s):
    return (f"M{f(cx)} {f(cy + s * .95)} C{f(cx - s * 1.7)} {f(cy - s * .1)} {f(cx - s * .85)} {f(cy - s * 1.25)} {f(cx)} {f(cy - s * .45)} "
            f"C{f(cx + s * .85)} {f(cy - s * 1.25)} {f(cx + s * 1.7)} {f(cy - s * .1)} {f(cx)} {f(cy + s * .95)}Z")


def star(cx, cy, R, r=None, n=5, rot=-90):
    r = R * 0.45 if r is None else r
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + 180 * k / n)
        q = R if k % 2 == 0 else r
        pts.append(f"{f(cx + q * math.cos(a))} {f(cy + q * math.sin(a))}")
    return "M" + " L".join(pts) + "Z"


def poly(cx, cy, r, n, rot=0):
    return star(cx, cy, r, r * math.cos(math.pi / n), n / 2, rot) if False else \
        "M" + " L".join(f"{f(cx + r * math.cos(math.radians(rot + 360 * k / n)))} {f(cy + r * math.sin(math.radians(rot + 360 * k / n)))}" for k in range(n)) + "Z"


def arch(cx, cy, r):
    return f"M{f(cx - r)} {f(cy)} A{f(r)} {f(r)} 0 0 1 {f(cx + r)} {f(cy)}Z"


def drip(x0, x1, y, h, depths, r=14):
    w = (x1 - x0) / len(depths)
    d = f"M{f(x0)} {f(y + r)} Q{f(x0)} {f(y)} {f(x0 + r)} {f(y)} H{f(x1 - r)} Q{f(x1)} {f(y)} {f(x1)} {f(y + r)} V{f(y + h)}"
    x = x1
    for dep in depths:
        d += f" Q{f(x - w / 2)} {f(y + h + dep * 2)} {f(x - w)} {f(y + h)}"
        x -= w
    return d + "Z"


def hill(y, dip=40):
    return f"M-10 {y} Q300 {y - dip} 610 {y} V610 H-10Z"


def cloud(p, cx, cy, s=1.0, col=CLOUD):
    p.p(col, scallop(cx, cy, 70 * s, 30 * s, 7, start=0.2))


# ---------- zoo ----------
def lion():
    p = Page("Lion")
    TAN, MANE = "#f5b95f", "#d0702a"
    p.r(SKY, -10, -10, 620, 620)
    p.p(GRASS, hill(480))
    p.c(SUN, 85, 85, 46)
    p.p(TAN, tube([(390, 500), (470, 510), (505, 450), (490, 400)], 18))
    p.e(MANE, 487, 380, 22, 32, -12)
    p.e(TAN, 300, 465, 108, 92)
    p.e(TAN, 222, 540, 46, 26)
    p.e(TAN, 378, 540, 46, 26)
    p.e(CREAM, 300, 485, 56, 58)
    p.r(TAN, 258, 450, 38, 104, 19)
    p.r(TAN, 304, 450, 38, 104, 19)
    p.p(MANE, scallop(300, 240, 168, 162, 12, start=0.26))
    for x in (198, 402):
        p.c(TAN, x, 128, 36)
        p.c(PINK, x, 128, 17)
    p.c(TAN, 300, 245, 120)
    p.e(CREAM, 300, 295, 64, 46)
    p.p(BROWN, "M276 258 Q300 248 324 258 Q320 282 300 290 Q280 282 276 258Z")
    p.ln("M300 290 V304 M300 304 Q282 326 264 308 M300 304 Q318 326 336 308")
    p.eye(252, 222, 13)
    p.eye(348, 222, 13)
    return p


def monkey():
    p = Page("Monkey")
    FUR, FACE, BAN = "#9a6238", "#f6cf9f", "#ffe14d"
    p.r(SKY, -10, -10, 620, 620)
    p.p(GRASS, hill(500))
    p.e(LEAF, 60, 50, 120, 42, -28)
    p.e(LEAF, 545, 55, 120, 42, 28)
    p.p(FUR, tube([(370, 500), (450, 510), (500, 450), (480, 380), (440, 400)], 16))
    p.p(FUR, tube([(232, 395), (170, 345), (140, 270)], 30, 26))
    p.c(FACE, 136, 256, 24)
    p.e(FUR, 300, 455, 92, 100)
    p.e(FACE, 300, 468, 54, 66)
    p.e(FUR, 236, 548, 52, 26)
    p.e(FUR, 364, 548, 52, 26)
    p.p(BAN, "M452 455 Q520 440 548 360 Q556 350 566 360 Q562 470 470 500 Q452 490 452 455Z")
    p.p(FUR, tube([(368, 395), (425, 420), (452, 468)], 30, 26))
    p.c(FACE, 456, 478, 24)
    for x in (166, 434):
        p.c(FUR, x, 215, 50)
        p.c(FACE, x, 215, 28)
    p.c(FUR, 300, 220, 116)
    p.p(FACE, "M300 158 C338 118 408 148 398 212 C436 302 362 326 300 326 C238 326 164 302 202 212 C192 148 262 118 300 158Z")
    p.eye(262, 212, 13)
    p.eye(338, 212, 13)
    p.ln("M290 252 q10 8 20 0")
    p.smile(300, 274, 44, 34)
    return p


def elephant():
    p = Page("Elephant")
    GREY, EAR = "#aab6cc", "#8d9bb8"
    p.r(SKY, -10, -10, 620, 620)
    p.p(GRASS, hill(510, 30))
    p.c(SUN, 510, 85, 46)
    cloud(p, 250, 90)
    p.p(GREY, tube([(490, 330), (540, 365), (535, 420)], 15))
    p.r(GREY, 250, 420, 58, 120, 22)
    p.r(GREY, 420, 420, 58, 120, 22)
    p.e(GREY, 370, 345, 150, 112)
    p.r(GREY, 305, 430, 62, 122, 24)
    p.r(GREY, 462, 430, 62, 122, 24)
    for x in (305, 462):
        p.ln(f"M{x + 12} 548 v-12 M{x + 31} 550 v-12 M{x + 50} 548 v-12", 4)
    p.p(GREY, tube([(148, 320), (108, 400), (118, 480), (176, 492)], 50, 28))
    p.c(GREY, 215, 285, 102)
    p.p(CREAM, "M168 362 Q150 418 196 428 Q182 396 192 366Z")
    p.e(EAR, 268, 285, 64, 90)
    p.e(PINK, 268, 288, 38, 60)
    p.eye(172, 262, 13)
    p.c(PINK, 160, 312, 15)
    return p


def giraffe():
    p = Page("Giraffe")
    YEL, SPOT = "#ffd66b", "#b9793a"
    p.r(SKY, -10, -10, 620, 620)
    p.p(GRASS, hill(520, 30))
    p.c(SUN, 510, 90, 46)
    cloud(p, 430, 190, 0.8)
    for x in (335, 455):
        p.r(YEL, x, 400, 32, 150, 14)
        p.r(SPOT, x - 3, 535, 38, 26, 9)
    p.p(YEL, tube([(488, 330), (530, 370), (525, 425)], 14))
    p.e(SPOT, 525, 440, 11, 20)
    p.p(YEL, tube([(345, 335), (290, 230), (262, 135)], 64, 44))
    p.e(YEL, 400, 345, 108, 76)
    for x in (300, 420):
        p.r(YEL, x, 400, 32, 150, 14)
        p.r(SPOT, x - 3, 535, 38, 26, 9)
    for a in ((372, 322, 26, 19), (440, 352, 27, 20), (462, 300, 18, 15), (392, 380, 18, 13), (318, 262, 17, 21), (290, 196, 14, 18)):
        p.e(SPOT, *a)
    p.e(YEL, 298, 84, 28, 14, -30)
    for x, y in ((228, 36), (262, 42)):
        p.r(YEL, x, y, 16, 44, 7)
        p.c(SPOT, x + 8, y - 2, 13)
    p.e(YEL, 232, 112, 64, 46, -15)
    p.e(CREAM, 184, 128, 40, 30, -15)
    p.eye(236, 100, 11)
    p.ln("M166 122 v1 M184 116 v1", 6)
    p.ln("M170 142 Q190 152 206 140", 4)
    return p


# ---------- princesses ----------
def princess():
    p = Page("Princess")
    SKIN, HAIR, DRESS = "#f3bb8f", "#6b4226", HOT
    p.r(SKY, -10, -10, 620, 620)
    p.p(GRASS, hill(540, 30))
    p.p(PINK, heart(95, 120, 34))
    p.p(PINK, heart(500, 430, 26))
    p.e(HAIR, 300, 235, 108, 135)
    p.p(SKIN, tube([(250, 305), (198, 355), (186, 410)], 24))
    p.p(DRESS, "M244 335 Q150 440 110 555 Q300 590 490 555 Q450 440 356 335Z")
    p.p(GOLD, "M110 555 Q300 590 490 555 L498 578 Q300 618 102 578Z")
    p.ln("M440 300 L474 236", 7)
    p.p(SUN, star(482, 216, 34))
    p.p(SKIN, tube([(350, 305), (410, 330), (442, 296)], 24))
    p.c(DRESS, 244, 296, 32)
    p.c(DRESS, 356, 296, 32)
    p.p(PURPLE, "M256 288 Q300 304 344 288 L360 344 Q300 360 240 344Z")
    p.c(SKIN, 300, 205, 80)
    p.p(HAIR, "M221 212 Q214 120 300 118 Q386 120 379 212 Q352 152 300 164 Q248 152 221 212Z")
    p.p(GOLD, "M252 124 L260 66 L282 100 L300 56 L318 100 L340 66 L348 124Z")
    p.c(RED, 300, 104, 10)
    p.eye(272, 212, 11)
    p.eye(328, 212, 11)
    p.c(PINK, 250, 236, 13)
    p.c(PINK, 350, 236, 13)
    p.smile(300, 240, 22, 18)
    return p


def castle():
    p = Page("Castle")
    STONE, ROOF, WALL = "#c5cce0", PURPLE, LAV
    p.r(SKY, -10, -10, 620, 620)
    p.c(SUN, 515, 80, 44)
    cloud(p, 95, 100, 0.9)
    p.p(GRASS, hill(490, 60))
    p.r(STONE, 255, 150, 90, 160)
    p.p(HOT, "M238 152 L300 46 L362 152Z")
    p.ln("M300 46 V8", 5)
    p.p(SUN, "M300 8 L338 20 L300 32Z")
    p.c(SUN, 300, 205, 20)
    for x in (105, 405):
        p.r(STONE, x, 225, 90, 262)
        p.p(ROOF, f"M{x - 16} 227 L{x + 45} 112 L{x + 106} 227Z")
        p.ln(f"M{x + 45} 112 V72", 5)
        p.p(HOT, f"M{x + 45} 72 L{x + 80} 84 L{x + 45} 96Z")
        p.p(SUN, f"M{x + 28} 320 V288 Q{x + 45} 262 {x + 62} 288 V320Z")
    p.p(WALL, "M195 492 V272 H227 V300 H259 V272 H291 V300 H309 V272 H341 V300 H373 V272 H405 V492Z")
    p.p(BROWN, "M262 492 V416 Q300 370 338 416 V492Z")
    p.ln("M300 380 V492", 4)
    p.p(SAND, "M262 492 H338 Q340 540 390 610 H210 Q260 540 262 492Z")
    return p


def crown():
    p = Page("Crown")
    p.r(BLUSH, -10, -10, 620, 620)
    for x, y, s in ((80, 90, 30), (525, 110, 36), (300, 60, 22)):
        p.p(SUN, star(x, y, s, s * 0.35, 4))
    p.c(GOLD, 78, 515, 20)
    p.c(GOLD, 522, 515, 20)
    p.p(PURPLE, "M90 468 Q300 432 510 468 Q545 515 510 562 Q300 592 90 562 Q55 515 90 468Z")
    p.p(GOLD, "M132 440 L98 205 L200 305 L300 150 L400 305 L502 205 L468 440Z")
    p.c(HOT, 98, 192, 24)
    p.c(HOT, 502, 192, 24)
    p.c(HOT, 300, 136, 28)
    p.p(RED, heart(300, 300, 34))
    p.r(ORANGE, 122, 392, 356, 66, 16)
    p.c(BLUE, 300, 425, 21)
    p.p(TEAL, poly(205, 425, 24, 4))
    p.p(TEAL, poly(395, 425, 24, 4))
    return p


def carriage():
    p = Page("Carriage")
    p.r(SKY, -10, -10, 620, 620)
    cloud(p, 110, 90, 0.9)
    p.p(HOT, heart(480, 90, 28))
    p.p(GRASS, hill(480, 30))
    p.r(SAND, -10, 520, 620, 100)
    p.c(GOLD, 300, 150, 18)
    p.e(GOLD, 300, 178, 46, 18)
    p.e(PINK, 300, 320, 196, 142)
    p.e(HOT, 300, 320, 112, 142)
    p.p(CLOUD, "M246 340 V270 Q300 214 354 270 V340Z")
    p.ln("M300 232 V340", 4)
    p.r(GOLD, 140, 440, 320, 24, 12)
    for x in (165, 435):
        p.c(PURPLE, x, 480, 66)
        p.c(LAV, x, 480, 44)
        p.ln(" ".join(f"M{f(x + 20 * math.cos(a))} {f(480 + 20 * math.sin(a))} L{f(x + 44 * math.cos(a))} {f(480 + 44 * math.sin(a))}"
                      for a in (k * math.pi / 3 for k in range(6))), 4)
        p.c(GOLD, x, 480, 20)
    return p


# ---------- unicorns ----------
def _unicorn(p, wings=False):
    BODY, HOOF = "#ffd3ea", PURPLE
    M1, M2, M3 = HOT, PURPLE, TEAL
    p.p(M1, tube([(468, 318), (540, 326), (562, 400), (532, 456)], 36, 14))
    p.p(M2, tube([(466, 334), (520, 362), (526, 436), (494, 480)], 36, 14))
    p.p(M3, tube([(460, 348), (494, 390), (486, 450), (452, 482)], 34, 14))
    for x in (305, 452):
        p.r(BODY, x, 395, 36, 130, 16)
        p.r(HOOF, x - 2, 505, 40, 28, 9)
    for col, x, y, r in ((M2, 288, 168, 33), (M3, 306, 220, 35), (M1, 326, 272, 35)):
        p.c(col, x, y, r)
    p.p(BODY, tube([(300, 350), (262, 270), (240, 200)], 96, 68))
    p.e(BODY, 365, 350, 128, 82)
    if wings:
        p.p(LAV, "M350 345 Q340 250 432 186 Q444 212 434 236 Q472 214 496 222 Q484 252 464 264 Q492 270 502 288 Q470 314 440 314 Q410 352 350 345Z")
        p.ln("M392 322 Q400 280 440 250 M418 318 Q436 296 466 286", 4)
    for x in (255, 402):
        p.r(BODY, x, 395, 36, 130, 16)
        p.r(HOOF, x - 2, 505, 40, 28, 9)
    p.p(BODY, "M250 156 L280 92 L296 160Z")
    p.p(GOLD, "M210 142 L200 34 L250 130Z")
    p.ln("M206 100 L234 106 M203 68 L220 74", 4)
    p.e(BODY, 205, 188, 82, 60, -18)
    p.c(M1, 256, 142, 28)
    p.eye(204, 174, 13)
    p.c(PINK, 172, 212, 13)
    p.ln("M138 196 v1", 6)
    p.ln("M144 220 Q160 234 178 228", 4)


def unicorn():
    p = Page("Unicorn")
    p.r(SKY, -10, -10, 620, 620)
    p.p(GRASS, hill(520, 30))
    cloud(p, 470, 100)
    p.p(SUN, star(90, 90, 34))
    p.p(SUN, star(545, 250, 22))
    _unicorn(p)
    return p


def unicorn_face():
    p = Page("Flower unicorn")
    BODY = "#ffd3ea"
    p.r(LAV, -10, -10, 620, 620)
    for x, y in ((70, 80), (535, 85)):
        p.p(SUN, star(x, y, 30))
    p.p(HOT, scallop(165, 350, 85, 170, 8, start=0.4))
    p.p(TEAL, scallop(435, 350, 85, 170, 8, start=0.4))
    for s in (1, -1):
        p.p(BODY, f"M{300 - s * 105} 215 L{300 - s * 122} 96 L{300 - s * 40} 170Z")
        p.p(PINK, f"M{300 - s * 98} 190 L{300 - s * 108} 128 L{300 - s * 66} 168Z")
    p.p(GOLD, "M266 170 L300 18 L334 170Z")
    p.ln("M282 110 L322 124 M290 70 L314 80", 4)
    p.e(BODY, 300, 335, 132, 165)
    p.e(PINK, 300, 452, 86, 58)
    p.ln("M272 450 v2 M328 450 v2", 7)
    p.ln("M278 478 Q300 492 322 478", 4)
    for s in (1, -1):
        x = 300 + s * 58
        p.ln(f"M{x - 24} 330 Q{x} 356 {x + 24} 330 M{x - 24} 334 l{-8 * 1} 8 M{x + 24} 334 l8 8 M{x} 346 v10", 5)
    p.c(HOT, 208, 395, 22)
    p.c(HOT, 392, 395, 22)
    for x, y, col in ((212, 232, PURPLE), (300, 205, HOT), (388, 232, PURPLE)):
        p.p(col, scallop(x, y, 34, 34, 5, start=-math.pi / 2))
        p.c(SUN, x, y, 14)
    return p


def rainbow():
    p = Page("Rainbow")
    p.r(SKY, -10, -10, 620, 620)
    p.c(SUN, 90, 90, 46)
    p.p(HOT, heart(505, 95, 26))
    p.p(GRASS, hill(540, 30))
    for col, r in ((RED, 262), (ORANGE, 222), (SUN, 182), (GRASS, 142), (BLUE, 102), (SKY, 62)):
        p.p(col, arch(300, 480, r))
    cloud(p, 95, 482, 1.25)
    cloud(p, 505, 482, 1.25)
    return p


def flying_unicorn():
    p = Page("Flying unicorn")
    NIGHT = "#5a63c8"
    p.r(NIGHT, -10, -10, 620, 620)
    p.c(SUN, 500, 100, 56)
    p.c(GOLD, 520, 85, 12)
    p.c(GOLD, 482, 122, 9)
    for x, y, s in ((70, 70, 24), (360, 55, 18), (60, 330, 18)):
        p.p(SUN, star(x, y, s))
    p.tf = "translate(10 -28)"
    _unicorn(p, wings=True)
    p.tf = ""
    cloud(p, 120, 545, 1.5)
    cloud(p, 330, 570, 1.6)
    cloud(p, 530, 545, 1.4)
    return p


# ---------- under the sea ----------
def _sea(p, sand_y=530):
    p.r(WATER, -10, -10, 620, 620)
    p.p(SAND, f"M-10 {sand_y} Q150 {sand_y - 26} 300 {sand_y} T610 {sand_y} V610 H-10Z")


def fish():
    p = Page("Fish")
    _sea(p)
    p.p(LEAF, tube([(75, 560), (55, 480), (95, 420), (70, 350)], 26, 12))
    p.p(LEAF, tube([(535, 560), (555, 500), (520, 450), (540, 390)], 26, 12))
    p.c(CLOUD, 105, 190, 22)
    p.c(CLOUD, 80, 120, 15)
    p.p(HOT, star(455, 555, 34, 15))
    p.p(SUN, "M425 300 L550 205 Q522 300 550 395Z")
    p.p(SUN, "M225 215 Q300 105 395 222Z")
    p.p(SUN, "M270 388 Q320 455 372 384Z")
    p.e(ORANGE, 290, 300, 165, 102)
    p.p(SUN, "M305 204 Q350 300 305 396 Q268 300 305 204Z")
    p.p(SUN, "M385 222 Q418 300 385 378 Q356 300 385 222Z")
    p.bigeye(195, 272, 26)
    p.ln("M140 322 Q170 348 205 332", 5)
    p.c(PINK, 222, 320, 13)
    return p


def octopus():
    p = Page("Octopus")
    _sea(p, 545)
    p.c(CLOUD, 85, 150, 22)
    p.c(CLOUD, 520, 110, 18)
    p.c(CLOUD, 545, 200, 12)
    legs = [[(225, 345), (150, 390), (105, 460), (140, 520)], [(258, 372), (212, 440), (196, 510), (240, 548)],
            [(288, 380), (284, 450), (300, 510), (272, 560)]]
    for k, pts in enumerate(legs):
        for s in (1, -1):
            q = [(300 + s * (x - 300), y) for x, y in pts] if not (k == 2 and s == -1) else [(322, 380), (336, 450), (360, 505), (345, 560)]
            p.p(PURPLE if k != 1 else HOT, tube(q, 44, 18))
    p.e(PURPLE, 300, 250, 142, 132)
    p.c(PINK, 218, 168, 17)
    p.c(PINK, 384, 176, 14)
    p.c(PINK, 300, 142, 12)
    p.bigeye(252, 250, 27)
    p.bigeye(348, 250, 27)
    p.smile(300, 300, 30, 26)
    p.c(HOT, 206, 300, 15)
    p.c(HOT, 394, 300, 15)
    return p


def turtle():
    p = Page("Turtle")
    SKINC, SHELL, PATCH = "#8fdc7a", "#3aa88c", "#f2c14e"
    _sea(p)
    p.p(LEAF, tube([(70, 560), (90, 490), (55, 430), (80, 370)], 26, 12))
    p.c(CLOUD, 520, 120, 20)
    p.c(CLOUD, 545, 60, 13)
    p.e(SKINC, 185, 408, 66, 28, 28)
    p.e(SKINC, 400, 418, 70, 28, -28)
    p.p(SKINC, "M135 385 L78 398 L128 356Z")
    p.e(SKINC, 478, 298, 64, 54)
    p.p(SHELL, "M128 372 Q138 188 290 184 Q442 188 452 372 Q290 402 128 372Z")
    p.p(PATCH, "M128 372 Q290 402 452 372 Q458 398 442 404 Q290 434 138 404 Q122 398 128 372Z")
    p.p(PATCH, poly(290, 285, 48, 6))
    p.p(PATCH, poly(196, 312, 34, 6))
    p.p(PATCH, poly(384, 312, 34, 6))
    p.eye(496, 286, 12)
    p.c(PINK, 478, 322, 12)
    p.ln("M505 318 Q520 326 530 312", 4)
    return p


def whale():
    p = Page("Whale")
    WH, DEEP = "#5b8cff", "#3f7fd6"
    p.r(SKY, -10, -10, 620, 620)
    p.c(SUN, 505, 85, 46)
    cloud(p, 330, 80, 0.9)
    p.p(WATER, "M-10 345 Q45 322 100 345 T210 345 T320 345 T430 345 T540 345 T650 345 V610 H-10Z")
    for x, rot in ((112, -24), (150, 0), (188, 24)):
        p.e(CLOUD, x, 222 - (0 if rot else 18), 13, 30, rot)
    p.ln("M150 262 V285", 6)
    p.e(WH, 486, 262, 48, 23, 35)
    p.e(WH, 558, 262, 48, 23, -35)
    p.p(WH, tube([(430, 400), (492, 352), (522, 288)], 70, 26))
    p.e(WH, 275, 412, 205, 118)
    p.p(CREAM, "M82 440 Q275 482 470 436 Q420 530 275 530 Q130 530 82 440Z")
    p.e(DEEP, 318, 462, 54, 22, 30)
    p.eye(150, 392, 13)
    p.c(PINK, 172, 428, 13)
    p.ln("M96 422 Q128 446 160 438", 5)
    p.p(DEEP, "M-10 545 Q45 522 100 545 T210 545 T320 545 T430 545 T540 545 T650 545 V610 H-10Z")
    return p


# ---------- yummy treats ----------
def cupcake():
    p = Page("Cupcake")
    p.r(BLUSH, -10, -10, 620, 620)
    p.r(SUN, -10, 530, 620, 90)
    p.p(HOT, heart(85, 110, 28))
    p.p(HOT, heart(515, 150, 22))
    top = [170 + 52 * k for k in range(6)]
    bot = [205 + 38 * k for k in range(6)]
    for k in range(5):
        p.p(TEAL if k % 2 == 0 else BLUE, f"M{top[k]} 385 H{top[k + 1]} L{bot[k + 1]} 548 H{bot[k]}Z")
    p.p(PINK, scallop(300, 362, 165, 56, 10, start=0.3))
    p.p(HOT, scallop(300, 290, 122, 50, 8, start=0.4))
    p.p(PINK, scallop(300, 226, 80, 42, 6, start=0.5))
    p.ln("M300 136 Q310 100 338 90", 5)
    p.c(RED, 300, 162, 32)
    p.c("!#ffffff", 288, 150, 8, 0)
    p.ln("M210 350 l14 10 M380 345 l-12 12 M300 372 l16 0 M250 286 l12 -10 M345 292 l14 8 M300 232 l-12 8", 6)
    return p


def icecream():
    p = Page("Ice cream")
    CONE = "#e8b56c"
    p.r("#c9f5e6", -10, -10, 620, 620)
    p.p(HOT, heart(90, 130, 28))
    p.p(SUN, star(510, 120, 30))
    p.p(HOT, heart(505, 450, 22))
    p.p(SUN, star(95, 440, 24))
    p.p(CONE, "M212 335 L300 580 L388 335Z")
    L = lambda t: (212 + 88 * t, 335 + 245 * t)
    R = lambda t: (388 - 88 * t, 335 + 245 * t)
    for a, b in ((.18, .52), (.42, .76)):
        p.ln(f"M{f(L(a)[0])} {f(L(a)[1])} L{f(R(b)[0])} {f(R(b)[1])} M{f(R(a)[0])} {f(R(a)[1])} L{f(L(b)[0])} {f(L(b)[1])}", 4)
    p.p(PINK, scallop(300, 338, 104, 26, 7, start=0.2))
    p.c(PINK, 300, 285, 96)
    p.c("#fff0a8", 300, 185, 80)
    p.c(PURPLE, 300, 102, 62)
    p.c(RED, 300, 38, 22)
    p.ln("M250 270 l12 10 M340 262 l-10 12 M300 310 l14 0 M262 170 l10 -8 M335 180 l10 8 M290 96 l12 6", 6)
    return p


def donut():
    p = Page("Donut")
    DOUGH = "#e9b16c"
    p.r("#bfe8ff", -10, -10, 620, 620)
    p.e(CREAM, 300, 305, 285, 270)
    p.c(DOUGH, 300, 300, 200)
    p.p(HOT, scallop(300, 300, 164, 164, 11, start=0.1, bulge=1.25))
    p.c(DOUGH, 300, 300, 74)
    p.c(CREAM, 300, 300, 52)
    cols = (SUN, BLUE, PURPLE)
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.2
        x, y = 300 + 118 * math.cos(a), 300 + 118 * math.sin(a)
        p.r(cols[k % 3], x - 24, y - 10.5, 48, 21, 10.5, rot=(k * 67) % 180)
    return p


def cake():
    p = Page("Birthday cake")
    p.r(LAV, -10, -10, 620, 620)
    p.r(SUN, -10, 560, 620, 60)
    p.ln("M-10 40 Q300 130 610 40", 4)
    for k, x in enumerate((60, 180, 300, 420, 540)):
        y = 40 + 45 * (1 - ((x - 300) / 310) ** 2) + 2
        p.p((HOT, TEAL, SUN)[k % 3], f"M{x - 28} {f(y)} L{x + 28} {f(y)} L{x} {f(y + 52)}Z")
    p.e(TEAL, 300, 582, 96, 18)
    p.r(TEAL, 280, 520, 40, 60)
    p.e(TEAL, 300, 515, 226, 26)
    p.r(PINK, 130, 380, 340, 128, 14)
    p.p(HOT, drip(130, 470, 380, 26, (14, 22, 10, 24, 14, 20)))
    for x in (200, 300, 400):
        p.c(SUN, x, 468, 16)
    p.r("#fff0a8", 190, 262, 220, 124, 14)
    p.p(PURPLE, drip(190, 410, 262, 24, (16, 10, 22, 12)))
    for k, x in enumerate((238, 291, 344)):
        p.r((TEAL, HOT, BLUE)[k], x, 200, 18, 64, 5)
        p.p(ORANGE, f"M{x + 9} 196 q-16 -24 0 -46 q16 22 0 46Z")
    return p


PACKS = [
    ("zoo", "Zoo animals", "#86d95b", [("lion", lion), ("monkey", monkey), ("elephant", elephant), ("giraffe", giraffe)]),
    ("princesses", "Princesses", "#ff6fae", [("princess", princess), ("castle", castle), ("crown", crown), ("carriage", carriage)]),
    ("unicorns", "Unicorns", "#a97bff", [("unicorn", unicorn), ("flower-unicorn", unicorn_face), ("rainbow", rainbow), ("flying-unicorn", flying_unicorn)]),
    ("sea", "Under the sea", "#3fd0c0", [("fish", fish), ("octopus", octopus), ("turtle", turtle), ("whale", whale)]),
    ("treats", "Yummy treats", "#ff9a3d", [("cupcake", cupcake), ("ice-cream", icecream), ("donut", donut), ("cake", cake)]),
]

if __name__ == "__main__":
    index = []
    for pid, name, color, pages in PACKS:
        (OUT / pid).mkdir(parents=True, exist_ok=True)
        entry = {"id": pid, "name": name, "color": color, "pages": []}
        for slug, fn in pages:
            pg = fn()
            (OUT / pid / f"{slug}.svg").write_text(pg.svg())
            entry["pages"].append({"id": slug, "name": pg.title})
            print(f"{pid}/{slug}: {len(pg.el)} shapes, {len(pg.pal)} colors")
        index.append(entry)
    (OUT / "packs.json").write_text(json.dumps(index, indent=1) + "\n")
