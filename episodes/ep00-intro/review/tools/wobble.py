"""Short-scale instability per window: pitch jitter (median semitone jump between 10 ms voiced frames inside a voiced run),
short breaks (0.15-0.6 s unvoiced gaps between voiced runs) per minute, and median voiced-run length.
  python wobble.py file [--skip 3.6 --tail 3.6 --win 20]"""
import sys, subprocess, argparse
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--skip", type=float, default=0); ap.add_argument("--tail", type=float, default=0)
ap.add_argument("--win", type=float, default=20); ap.add_argument("--quiet", action="store_true")
a = ap.parse_args(); sr = 16000
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.file, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32); x = x[int(a.skip*sr): len(x) - int(a.tail*sr)]
n, h = int(sr*0.04), int(sr*0.01); lo, hi = sr // 300, sr // 60
rms_all = np.sqrt(np.mean(x**2)); f0 = []
for i in range(0, len(x) - n, h):
    fr = x[i:i+n] - x[i:i+n].mean(); e = np.sqrt((fr**2).mean())
    if e < rms_all * 0.3: f0.append(0); continue
    ac = np.correlate(fr, fr, "full")[n-1:]
    lag = lo + int(np.argmax(ac[lo:hi])); f0.append(sr/lag if ac[0] > 0 and ac[lag]/ac[0] > 0.45 else 0)
f0 = np.array(f0); voiced = f0 > 0
runs = []; i = 0
while i < len(f0):
    if voiced[i]:
        j = i
        while j < len(f0) and voiced[j]: j += 1
        runs.append((i, j)); i = j
    else: i += 1
def stats(a0, a1):
    rs = [(s, e) for s, e in runs if s >= a0 and e <= a1 and e - s >= 3]
    jumps = np.concatenate([np.abs(np.diff(12*np.log2(f0[s:e]))) for s, e in rs]) if rs else np.array([0])
    jumps = jumps[jumps < 4]   # octave errors out
    gaps = [rs[k+1][0] - rs[k][1] for k in range(len(rs)-1)]
    short = sum(1 for g in gaps if 15 <= g <= 60)
    return float(np.median(jumps)), float(np.mean(jumps > 1.0)), short / ((a1-a0)/6000), float(np.median([e-s for s, e in rs]))*10 if rs else 0
W = int(a.win*100); rows = []
for s in range(0, len(f0) - W//2, W):
    rows.append((s/100 + a.skip, *stats(s, min(s+W, len(f0)))))
if not a.quiet:
    for t, j, jb, sb, vr in rows: print(f"{int(t//60)}:{int(t%60):02d}  jitter {j:.3f} st  big_jumps {jb:.3f}  short_breaks/min {sb:5.1f}  voiced_run {vr:4.0f} ms")
j, jb, sb, vr = stats(0, len(f0))
print(f"SUMMARY jitter {j:.3f} st  big_jumps {jb:.3f}  short_breaks/min {sb:.1f}  voiced_run {vr:.0f} ms")
