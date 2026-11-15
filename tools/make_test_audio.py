#!/usr/bin/env python3
"""Generate a small test batch of reading-game audio with WaveSpeed.

Makes letter sounds (two attempts each), short words and a few phrases,
then writes a listen.html page so you can play and compare them.

Usage:
    export WAVESPEED_API_KEY="your key"
    python3 tools/make_test_audio.py

Optional:
    WAVESPEED_VOICE   voice name or ElevenLabs voice ID (default: Alicia)
    WAVESPEED_MODEL   model path (default: elevenlabs/turbo-v2)

Nothing here ships in a game. The key is read from your shell only.
"""
import html
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.wavespeed.ai/api/v3"
KEY = os.environ.get("WAVESPEED_API_KEY", "").strip()
VOICE = os.environ.get("WAVESPEED_VOICE", "Alicia")
MODEL = os.environ.get("WAVESPEED_MODEL", "elevenlabs/turbo-v2")
OUT = Path(__file__).resolve().parent.parent / "audio-test"


def ipa(symbol, letter):
    return f'<phoneme alphabet="ipa" ph="{symbol}">{letter}</phoneme>'


# (file name, label shown on the listening page, text sent to the model)
SOUNDS = [
    ("sound-s-spelled", "s, spelled out", "Sssss."),
    ("sound-s-ipa", "s, phoneme tag", ipa("s", "s")),
    ("sound-a-spelled", "a (as in at), spelled out", "Aaa."),
    ("sound-a-ipa", "a (as in at), phoneme tag", ipa("æ", "a")),
    ("sound-t-spelled", "t, spelled out", "T."),
    ("sound-t-ipa", "t, phoneme tag", ipa("t", "t")),
    ("sound-p-spelled", "p, spelled out", "P."),
    ("sound-p-ipa", "p, phoneme tag", ipa("p", "p")),
    ("sound-i-spelled", "i (as in it), spelled out", "Ih."),
    ("sound-i-ipa", "i (as in it), phoneme tag", ipa("ɪ", "i")),
    ("sound-n-spelled", "n, spelled out", "Nnnn."),
    ("sound-n-ipa", "n, phoneme tag", ipa("n", "n")),
]
WORDS = ["sat", "pin", "tap", "nap", "sit", "tin", "pan", "pat", "tip", "ant"]
PHRASES = [
    ("phrase-praise", "You read it! Great job, Jack!"),
    ("phrase-slide", "Slide your finger to read the word."),
    ("phrase-retry", "Almost! Try it one more time."),
]
CLIPS = (
    [("Letter sounds", n, label, text) for n, label, text in SOUNDS]
    + [("Words", f"word-{w}", w, f"{w.capitalize()}.") for w in WORDS]
    + [("Phrases", n, text, text) for n, text in PHRASES]
)


def call(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "User-Agent": "jacks-games-audio-test",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.load(r)
    return payload.get("data", payload)


def generate(text):
    """Submit once (never retried, so nothing is billed twice), then poll."""
    task = call(f"{API}/{MODEL}", {"text": text, "voice_id": VOICE})
    task_id = task.get("id")
    if not task_id:
        raise RuntimeError(f"no task id in response: {task}")
    for _ in range(90):
        status = task.get("status")
        if status == "completed" and task.get("outputs"):
            return task["outputs"][0]
        if status in ("failed", "cancelled", "timeout", "deleted"):
            raise RuntimeError(task.get("error") or status)
        time.sleep(2)
        try:
            task = call(f"{API}/predictions/{task_id}/result")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
    raise RuntimeError("timed out waiting for audio")


def download(url, dest_stem):
    ext = Path(url.split("?")[0]).suffix or ".mp3"
    dest = OUT / f"{dest_stem}{ext}"
    req = urllib.request.Request(url, headers={"User-Agent": "jacks-games-audio-test"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dest.write_bytes(r.read())
    return dest.name


def write_page(done):
    rows, section = [], None
    for group, label, fname in done:
        if group != section:
            rows.append(f"<h2>{html.escape(group)}</h2>")
            section = group
        rows.append(
            f'<p><b>{html.escape(label)}</b><br>'
            f'<audio controls preload="none" src="{html.escape(fname)}"></audio></p>'
        )
    (OUT / "listen.html").write_text(
        "<!DOCTYPE html><meta charset='utf-8'><title>Audio test</title>"
        "<style>body{font:17px system-ui;max-width:560px;margin:32px auto;padding:0 16px}"
        "audio{width:100%}</style>"
        f"<h1>Audio test</h1><p>Model {html.escape(MODEL)}, voice {html.escape(VOICE)}. "
        "For each letter sound, listen for a pure sound: no letter name and no "
        "extra 'uh' on the end.</p>" + "\n".join(rows),
        encoding="utf-8",
    )


def main():
    if not KEY:
        sys.exit('Set your key first:  export WAVESPEED_API_KEY="your key"')
    OUT.mkdir(exist_ok=True)
    done, failed = [], []
    for i, (group, name, label, text) in enumerate(CLIPS, 1):
        print(f"[{i}/{len(CLIPS)}] {name} ... ", end="", flush=True)
        try:
            fname = download(generate(text), name)
            done.append((group, label, fname))
            print("ok")
        except Exception as e:  # keep going so one bad clip doesn't stop the batch
            failed.append(name)
            print(f"FAILED ({e})")
    write_page(done)
    print(f"\n{len(done)} clips saved in {OUT}")
    if failed:
        print("Failed:", ", ".join(failed))
    print(f"Listen:  open '{OUT / 'listen.html'}'")


if __name__ == "__main__":
    main()
