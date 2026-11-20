#!/usr/bin/env python3
"""Pack logans-coloring-book into one self-contained HTML file (pictures and
logo embedded) for previewing where separate files can't be loaded."""
import base64, json, re, sys
from pathlib import Path
G = Path(__file__).resolve().parent.parent / "logans-coloring-book"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logans-coloring-book-preview.html")
h = (G / "index.html").read_text()
logo = base64.b64encode((G / "logan.webp").read_bytes()).decode()
h = h.replace('src="logan.webp"', f'src="data:image/webp;base64,{logo}"')
h = re.sub(r'<link rel="(apple-touch-icon|icon|manifest)"[^>]*>\n', "", h)
packs = json.loads((G / "packs" / "packs.json").read_text())
svg = {f'{p["id"]}/{g["id"]}': (G / "packs" / p["id"] / f'{g["id"]}.svg').read_text() for p in packs for g in p["pages"]}
marker = "<script>\n/* ---------- small helpers"
assert marker in h
data = json.dumps({"packs": packs, "svg": svg}).replace("</", "<\\/")
h = h.replace(marker, f"<script>window.PACK_DATA={data};</script>\n" + marker, 1)
out.write_text(h)
print(out, len(h) // 1024, "KB")
