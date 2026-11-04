import sys, json, re, subprocess
from pathlib import Path
import numpy as np
sys.path.insert(0, "podcast")
from compare_voices import load, f0_track, centroid
from make_podcast import measure_lufs, spoken_chars, wav_duration
txt = {s["id"]: s["text"] for s in json.load(open("podcast/script/ep00_intro_nohint.json", encoding="utf-8"))["segments"]}
def edge(x, sr, sec, head):
    n = int(sec * sr); y = x[:n] if head else x[-n:]
    f = f0_track(y, sr); return float(np.median(f)) if len(f) else float("nan"), centroid(y, sr)
def row(p, seg):
    x, sr = load(p); f = f0_track(x, sr)
    hf, hc = edge(x, sr, 6, True); tf, tc = edge(x, sr, 6, False)
    return dict(file=str(p), pitch=round(float(np.median(f)),1), p10=round(float(np.percentile(f,10)),1), p90=round(float(np.percentile(f,90)),1),
                centroid=round(centroid(x, sr)), cps=round(spoken_chars(txt[seg]) / wav_duration(p), 2),
                head_pitch=round(hf,1), head_centroid=round(hc), tail_pitch=round(tf,1), tail_centroid=round(tc))
rows = []
for d in ["D1_ep00", "D1_ep00b"]:
    for p in sorted(Path("out/podcast/segments", d).glob("s*.take*.wav")):
        rows.append({"set": "hint" if d == "D1_ep00" else "nohint", "take": p.stem, **row(p, p.name.split(".")[0])})
for p in sorted(Path("out/podcast/master/norm_D1_ep00pick").glob("s*.wav")):
    rows.append({"set": "draft1-mastered", "take": p.stem, **row(p, p.stem)})
print(f"{'set':16s} {'take':16s} {'pitch':>6s} {'p10-p90':>12s} {'centr':>6s} {'字/秒':>5s} {'頭6s音高/重心':>14s} {'尾6s音高/重心':>14s}")
for r in rows:
    print(f"{r['set']:16s} {r['take']:16s} {r['pitch']:6.1f} {r['p10']:5.1f}-{r['p90']:5.1f} {r['centroid']:6d} {r['cps']:5.2f} {r['head_pitch']:6.1f}/{r['head_centroid']:5d} {r['tail_pitch']:6.1f}/{r['tail_centroid']:5d}")
json.dump(rows, open("measure.json", "w"), ensure_ascii=False, indent=1)
