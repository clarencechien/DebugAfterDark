"""Exact start time of each segment in the mastered episode, for show-notes chapters (docs/hooks.md, YouTube 說明欄).

Rebuilds the timeline the way `make_podcast.py master` assembles it: intro sting 3.2 s + lead 0.4 s, then the segments
in script order with a 0.6 s gap between them, and the fixed ident (plus a 0.6 s gap) right after the cold open.
qa/consistency.json's `start` leaves the ident out, so every segment after the cold open there is about 10 s early
(found 2026-11-20). The check at the end compares the rebuilt length with the mp3.

  python3 tools/chapters.py episodes/<ep>          # prints  id  mm:ss
"""
import json, subprocess, sys
from pathlib import Path

INTRO, LEAD, GAP, OUTRO = 3.2, 0.4, 0.6, 3.2


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def starts(ep_dir):
    ep_dir = Path(ep_dir); ep = ep_dir.name
    norm = Path("out/master") / f"norm_D1_{ep}"
    ids = [s["id"] for s in json.loads((ep_dir / "script.json").read_text(encoding="utf-8"))["segments"]]
    t, out = INTRO + LEAD, []
    for k, i in enumerate(ids):
        out.append((i, t)); t += dur(norm / f"{i}.wav")
        if k == 0 and (norm / "ident.wav").exists():
            t += GAP + dur(norm / "ident.wav")
        if k < len(ids) - 1: t += GAP
    total = t + LEAD + OUTRO
    mp3 = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8")).get("audio", {}).get("duration_s")
    return out, total, mp3


def mmss(s):
    s = int(s); return f"{s // 60:02d}:{s % 60:02d}"


if __name__ == "__main__":
    rows, total, mp3 = starts(sys.argv[1])
    for i, s in rows: print(f"{i:18s} {mmss(s)}  ({s:.1f})")
    print(f"rebuilt {total:.1f} s, mp3 {mp3} s")
