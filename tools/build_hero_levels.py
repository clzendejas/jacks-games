#!/usr/bin/env python3
"""Build the Adventure levels for Jack's Hero Squad.

Each level is a small map of platforms at different heights, joined by
stairs and bridges, with open water or a chasm between them. The hero has a
power number; he can beat any monster whose number is not bigger than his,
and its number is added to his. Monsters guard the stairs and bridges, so
the map opens up as he grows. The boss ends the level.

Every level written here is checked by playing out every possible order of
moves: a level is kept only if no order of winning moves can leave the
player stuck. Wrong picks cost a heart, but they can never make a level
unwinnable.

Run:  python3 tools/build_hero_levels.py
It rewrites the LEVELS block inside hero-squad/index.html.

A map square is [x, y, height, kind]. Kinds: f floor, b bridge,
n stairs rising to the back, e stairs rising to the right, w stairs rising
to the left. y grows toward the player; higher ground is always further
back, so nothing is ever hidden behind a cliff.
"""
import json, random, re, sys
from pathlib import Path
from collections import deque

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "hero-squad" / "index.html"

WORLDS = [
    dict(theme="meadow", mons=["slime", "goblin", "mushroom"], boss="ogre"),
    dict(theme="cave", mons=["bat", "skeleton", "imp"], boss="dragon"),
    dict(theme="ice", mons=["slime", "skeleton", "goblin", "bat", "imp", "mushroom"], boss="yeti"),
]
LEVELS_PER_WORLD = 10
MAX_W, MAX_H, MAX_HEIGHT = 12, 9, 3
SIDES = {(0, -1): "N", (0, 1): "S", (1, 0): "E", (-1, 0): "W"}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


def plan(idx):
    """What goes into level idx (0-based)."""
    w, i = divmod(idx, LEVELS_PER_WORLD)
    if idx == 0:
        rooms, mons = 2, 2
    elif idx < 3:
        rooms, mons = 3, 3
    elif idx < 6:
        rooms, mons = 4, 4
    elif w == 0:
        rooms, mons = 4 + (i % 2), 5
    elif w == 1:
        rooms, mons = 5, 5 + (i >= 5)
    else:
        rooms, mons = 5 + (i % 2), 6 + (i >= 5)
    return dict(
        world=w, rooms=rooms, mons=mons, big=1 if idx >= 3 else 0,
        potions=0 if idx < 3 else (1 if idx < 12 else 1 + (i % 3 == 0)),
        double=idx >= 6 and i % 3 == 0,
        door=idx >= 8 and i % 2 == 0,
        chest=idx >= 2 and i % 2 == 1,
        decor=0 if idx < 2 else 1 + w,
        start={0: (2, 4), 1: (5, 9), 2: (10, 20)}[w],
    )


# ---------- the map ----------

def edge_height(cell, side):
    """Height of a square along one of its sides, or None if that side is a wall of the stairs."""
    h, t = cell
    if t in "fb":
        return h
    return {"n": {"N": h + 1, "S": h}, "e": {"E": h + 1, "W": h}, "w": {"W": h + 1, "E": h}}[t].get(side)


def can_step(cells, a, b):
    side = SIDES[(b[0] - a[0], b[1] - a[1])]
    ha, hb = edge_height(cells[a], side), edge_height(cells[b], OPPOSITE[side])
    return ha is not None and ha == hb


def around(c):
    return [(c[0] + dx, c[1] + dy) for dx, dy in SIDES]


def top(cell):
    return cell[0] + (cell[1] in "new")


def add_room(rng, cells, rooms, big):
    """Try to hang one more platform off an existing one. Returns True if it fitted."""
    R = rng.choice(rooms)
    kind = rng.choice(["N", "N", "N", "S", "E", "W", "E", "W", "bE", "bW", "bN"])
    w, d = rng.randint(2, 3 + big), rng.randint(2, 2 + big)
    h = R["h"]
    if kind == "N":                                   # stairs up to a platform behind
        sx = rng.randint(R["x0"], R["x1"])
        conn, nh, link = [(sx, R["y0"] - 1, h, "n")], h + 1, (sx, R["y0"])
        x0, y1 = sx - rng.randint(0, w - 1), R["y0"] - 2
        y0, entry = y1 - d + 1, (sx, y1)
    elif kind == "S":                                 # stairs down to a platform in front
        if h < 1:
            return False
        sx = rng.randint(R["x0"], R["x1"])
        conn, nh, link = [(sx, R["y1"] + 1, h - 1, "n")], h - 1, (sx, R["y1"])
        x0, y0 = sx - rng.randint(0, w - 1), R["y1"] + 2
        y1, entry = y0 + d - 1, (sx, y0)
    elif kind in ("E", "W"):                          # stairs up or down to a platform beside
        up = h < 1 or rng.random() < 0.6
        nh = h + 1 if up else h - 1
        sy = rng.randint(R["y0"], R["y1"])
        if kind == "E":
            cx, x0, t, link = R["x1"] + 1, R["x1"] + 2, "e" if up else "w", (R["x1"], sy)
            entry = (x0, sy)
        else:
            cx, x0, t, link = R["x0"] - 1, R["x0"] - 1 - w, "w" if up else "e", (R["x0"], sy)
            entry = (x0 + w - 1, sy)
        conn = [(cx, sy, min(h, nh), t)]
        y0 = sy - rng.randint(0, d - 1)
        y1 = y0 + d - 1
    elif kind in ("bE", "bW"):                        # a bridge to a platform beside
        n, sy, nh = rng.randint(1, 2), rng.randint(R["y0"], R["y1"]), h
        if kind == "bE":
            conn, x0, link = [(R["x1"] + 1 + i, sy, h, "b") for i in range(n)], R["x1"] + 1 + n, (R["x1"], sy)
            entry = (x0, sy)
        else:
            conn, x0, link = [(R["x0"] - 1 - i, sy, h, "b") for i in range(n)], R["x0"] - n - w, (R["x0"], sy)
            entry = (x0 + w - 1, sy)
        y0 = sy - rng.randint(0, d - 1)
        y1 = y0 + d - 1
    else:                                             # a bridge to a platform behind
        n, sx, nh = rng.randint(1, 2), rng.randint(R["x0"], R["x1"]), h
        conn, link = [(sx, R["y0"] - 1 - i, h, "b") for i in range(n)], (sx, R["y0"])
        y1 = R["y0"] - 1 - n
        y0, x0, entry = y1 - d + 1, sx - rng.randint(0, w - 1), (sx, y1)
    x1 = x0 + w - 1
    if nh > MAX_HEIGHT:
        return False
    new = {(x, y): (nh, "f") for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    for x, y, hh, t in conn:
        if (x, y) in new:
            return False
        new[(x, y)] = (hh, t)
    if any(c in cells for c in new):
        return False
    first = conn[0][:2]
    for c, (hh, t) in new.items():
        for n in around(c):
            if n in cells and not (c == first and n == link):
                oh, ot = cells[n]
                # platforms may stand side by side as terraces, but never level with each other,
                # and stairs and bridges touch nothing except their two ends
                if t != "f" or ot != "f" or oh == hh:
                    return False
    both = dict(cells)
    both.update(new)
    xs, ys = [c[0] for c in both], [c[1] for c in both]
    if max(xs) - min(xs) + 1 > MAX_W or max(ys) - min(ys) + 1 > MAX_H:
        return False
    # higher ground must be further back, or it would hide what is behind it
    for (x, y), cell in new.items():
        for (ox, oy), other in both.items():
            if ox != x or oy == y:
                continue
            back, front = ((x, y), cell), ((ox, oy), other)
            if back[0][1] > front[0][1]:
                back, front = front, back
            rows = front[0][1] - back[0][1]
            if top(front[1]) - top(back[1]) > int((rows - 1) * 1.5):
                return False
    cells.update(new)
    rooms.append(dict(x0=x0, y0=y0, x1=x1, y1=y1, h=nh, entry=entry, link=link, parent=R, depth=R["depth"] + 1,
                      conn=[c[:2] for c in conn]))
    return True


def make_map(rng, p):
    for _ in range(400):
        w, d = rng.randint(2, 3), 2
        cells = {(x, y): (0, "f") for x in range(w) for y in range(d)}
        rooms = [dict(x0=0, y0=0, x1=w - 1, y1=d - 1, h=0, entry=None, link=None, parent=None, depth=0, conn=[])]
        tries = 0
        while len(rooms) < p["rooms"] and tries < 300:
            tries += 1
            add_room(rng, cells, rooms, p["big"])
        if len(rooms) == p["rooms"] and max(r["h"] for r in rooms) >= 1:
            return cells, rooms
    return None


# ---------- playing it out ----------

def region(cells, start, blocked):
    seen = {start}
    q = deque([start])
    while q:
        c = q.popleft()
        for n in around(c):
            if n in cells and n not in seen and n not in blocked and can_step(cells, c, n):
                seen.add(n)
                q.append(n)
    return seen


def in_reach(cells, e, reach):
    c = (e["x"], e["y"])
    return any(n in reach and can_step(cells, n, c) for n in around(c))


def no_dead_ends(cells, hero, decor, ents, start_power):
    """Play out every order of winning moves. True if none gets stuck."""
    boss = next(i for i, e in enumerate(ents) if e["t"] == "boss")
    seen = set()
    stack = [(0, start_power)]
    while stack:
        mask, power = stack.pop()
        if (mask, power) in seen:
            continue
        seen.add((mask, power))
        if mask >> boss & 1:
            continue
        left = {(e["x"], e["y"]): i for i, e in enumerate(ents) if not mask >> i & 1}
        reach = region(cells, hero, decor | set(left))
        keys = sum(1 for i, e in enumerate(ents) if e["t"] == "key" and mask >> i & 1) \
            - sum(1 for i, e in enumerate(ents) if e["t"] == "door" and mask >> i & 1)
        moves = 0
        for i in left.values():
            e = ents[i]
            if not in_reach(cells, e, reach):
                continue
            t = e["t"]
            if t in ("mon", "boss"):
                if power < e["n"]:
                    continue
                nxt = power + e["n"]
            elif t == "add":
                nxt = power + e["n"]
            elif t == "mul":
                nxt = power * e["n"]
            elif t == "door":
                if keys < 1:
                    continue
                nxt = power
            else:  # key, chest
                nxt = power
            moves += 1
            stack.append((mask | 1 << i, nxt))
        if not moves:
            return False
    return True


def attempt(idx, rng):
    p = plan(idx)
    world = WORLDS[p["world"]]
    made = make_map(rng, p)
    if not made:
        return None
    cells, rooms = made

    # the boss lives on the platform furthest along; a locked gate, if any, guards its entrance
    boss_room = max(rooms[1:], key=lambda r: (r["depth"], r["h"], -r["y0"]))
    if any(r["parent"] is boss_room for r in rooms):
        return None
    reserved = {r["entry"] for r in rooms[1:]} | {r["link"] for r in rooms[1:]}
    used = set()
    ents = []

    def put(e, c):
        e["x"], e["y"] = c
        used.add(c)
        ents.append(e)

    def spare(room=None, avoid=()):
        pool = [c for c, cell in cells.items() if cell[1] == "f" and c not in used and c not in avoid
                and (room is None or (room["x0"] <= c[0] <= room["x1"] and room["y0"] <= c[1] <= room["y1"]))]
        # characters stand taller than their square: nothing directly in front of or behind another on level ground
        pool = [c for c in pool if not any((c[0], c[1] + s) in used and cells[(c[0], c[1] + s)][0] == cells[c][0]
                                           for s in (-1, 1))]
        return rng.choice(pool) if pool else None

    home = rooms[0]
    start = (home["x0"], home["y1"])
    if start in reserved:
        return None
    used.add(start)
    guards = 0
    for r in rooms[1:]:
        if r is boss_room and p["door"]:
            put(dict(t="door"), r["entry"])
        else:
            put(dict(t="mon", k=rng.choice(world["mons"])), r["entry"])
            guards += 1
    far = max((c for c in cells if boss_room["x0"] <= c[0] <= boss_room["x1"] and boss_room["y0"] <= c[1] <= boss_room["y1"]
               and c not in used),
              key=lambda c: abs(c[0] - boss_room["entry"][0]) + abs(c[1] - boss_room["entry"][1]) + rng.random())
    put(dict(t="boss", k=world["boss"]), far)
    others = [r for r in rooms if r is not boss_room]
    extras = [dict(t="mon", k=rng.choice(world["mons"])) for _ in range(max(0, p["mons"] - guards))]
    extras += [dict(t="add") for _ in range(p["potions"])]
    if p["double"]:
        extras.append(dict(t="mul", n=2))
    if p["door"]:
        extras.append(dict(t="key"))
    for e in extras:
        c = spare(rng.choice(others), avoid=reserved if e["t"] != "mon" else ())
        if not c:
            return None
        put(e, c)
    if p["chest"]:
        c = spare(rng.choice(rooms), avoid=reserved)
        if not c:
            return None
        put(dict(t="chest", n=10 * rng.randint(1, 3 + p["world"])), c)

    # a few bushes, rocks or crystals in platform corners
    decor = set()
    for _ in range(p["decor"]):
        r = rng.choice(rooms)
        if (r["x1"] - r["x0"] + 1) * (r["y1"] - r["y0"] + 1) < 6:
            continue
        c = rng.choice([(r["x0"], r["y0"]), (r["x1"], r["y0"])])        # back corners only: never in front of anyone
        if c in used or c in reserved or c in decor or (c[0], c[1] + 1) in used:
            continue
        decor.add(c)

    # the numbers: walk the map in one possible order, sizing each thing so that step can be won
    power = rng.randint(*p["start"]) if idx else 3
    start_power, added, keys = power, 0, 0
    left = [e for e in ents]
    first = True
    while True:
        reach = region(cells, start, decor | {(e["x"], e["y"]) for e in left})
        front = [e for e in left if in_reach(cells, e, reach) and e["t"] != "boss" and (e["t"] != "door" or keys)]
        if not front:
            break
        e = rng.choice(front)
        if first and e["t"] != "mon":
            mons = [m for m in front if m["t"] == "mon"]
            if not mons:
                return None
            e = rng.choice(mons)
        if e["t"] == "mon":
            # first one is an easy win; later ones stay well inside what he has,
            # so the numbers grow steadily instead of doubling every time
            if first:
                lo, hi = max(1, power // 2), power
            else:
                lo = max(1, -(-power * 35 // 100))
                hi = max(lo, power * 8 // 10)
            e["n"] = rng.randint(lo, hi)
            power += e["n"]
            added += e["n"]
        elif e["t"] == "add":
            # a potion is a small boost sized to where he started, so it never wins the level for him
            e["n"] = rng.randint(max(1, start_power // 2), max(2, start_power))
            power += e["n"]
            added += e["n"]
        elif e["t"] == "mul":
            power *= 2
        elif e["t"] == "key":
            keys += 1
        elif e["t"] == "door":
            keys -= 1
        first = False
        left.remove(e)
    if [e["t"] for e in left] != ["boss"]:
        return None
    # with a doubler, the least he can end with is doubling before anything else
    least = start_power * (2 if p["double"] else 1) + added
    left[0]["n"] = rng.randint(-(-least * 3 // 4), least)

    # there has to be a real choice at the start
    reach = region(cells, start, decor | {(e["x"], e["y"]) for e in ents})
    seen = [e for e in ents if e["t"] == "mon" and in_reach(cells, e, reach)]
    if not any(e["n"] <= start_power for e in seen):
        return None
    if idx and not any(e["n"] > start_power for e in ents if e["t"] == "mon"):
        return None
    if not no_dead_ends(cells, start, decor, ents, start_power):
        return None

    # shift so the map starts at 0,0
    mx, my = min(c[0] for c in cells), min(c[1] for c in cells)
    for e in ents:
        e["x"] -= mx
        e["y"] -= my
    return dict(
        w=max(c[0] for c in cells) - mx + 1, h=max(c[1] for c in cells) - my + 1, theme=world["theme"],
        hero=dict(x=start[0] - mx, y=start[1] - my, p=start_power),
        cells=sorted([c[0] - mx, c[1] - my, cell[0], cell[1]] for c, cell in cells.items()),
        walls=sorted([c[0] - mx, c[1] - my] for c in decor), ents=ents)


def build(count):
    out = []
    for idx in range(count):
        rng = random.Random(9100 + idx)
        for _ in range(20000):
            level = attempt(idx, rng)
            if level:
                break
        else:
            sys.exit(f"could not build level {idx + 1}")
        out.append(level)
    return out


def main():
    levels = build(len(WORLDS) * LEVELS_PER_WORLD)
    blob = json.dumps(levels, separators=(",", ":"))
    page = PAGE.read_text()
    page, n = re.subn(r"/\*LEVELS\*/.*?/\*END\*/", lambda m: "/*LEVELS*/" + blob + "/*END*/", page, flags=re.S)
    if n != 1:
        sys.exit("LEVELS marker not found in hero-squad/index.html")
    PAGE.write_text(page)
    for i, lv in enumerate(levels, 1):
        nums = [e["n"] for e in lv["ents"] if e["t"] == "mon"]
        boss = next(e["n"] for e in lv["ents"] if e["t"] == "boss")
        extra = [e["t"] for e in lv["ents"] if e["t"] not in ("mon", "boss")]
        kinds = "".join(sorted({c[3] for c in lv["cells"]} - {"f"}))
        tops = max(c[2] for c in lv["cells"])
        print(f"{i:2} {lv['theme']:7} {lv['w']:2}x{lv['h']} heights 0-{tops} links {kinds:4} start {lv['hero']['p']:3} "
              f"monsters {nums} boss {boss} {extra}")


if __name__ == "__main__":
    main()
