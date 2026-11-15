#!/usr/bin/env python3
"""Pack reading-adventures into one self-contained HTML file (sounds, font and
picture embedded) for previewing where separate files can't be loaded."""
import base64, json, re, sys
from pathlib import Path
G = Path(__file__).resolve().parent.parent / "reading-adventures"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reading-adventures-preview.html")
b = lambda p: base64.b64encode((G / p).read_bytes()).decode()
h = (G / "index.html").read_text()
ids = [f.stem for f in sorted((G / "sounds").glob("*.mp3"))]
h = h.replace('url("andika-700.woff2")', f'url("data:font/woff2;base64,{b("andika-700.woff2")}")')
h = h.replace('src="jack.webp"', f'src="data:image/webp;base64,{b("jack.webp")}"')
h = re.sub(r'<link rel="(apple-touch-icon|icon|manifest)"[^>]*>\n', "", h)
data = json.dumps({i: b(f"sounds/{i}.mp3") for i in ids})
marker = "<script>\n/* ---------- the pals"
assert marker in h
h = h.replace(marker, f"<script>window.SOUND_DATA={data};</script>\n" + marker, 1)
out.write_text(h)
print(out, len(h) // 1024, "KB")
