"""Syllable-rate estimate per window from the energy envelope (Mandarin ~ one envelope peak per syllable), plus pause share."""
import sys, subprocess, argparse
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--skip", type=float, default=0); ap.add_argument("--tail", type=float, default=0); ap.add_argument("--win", type=float, default=15)
a = ap.parse_args(); sr = 16000
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.file, "-af", "highpass=f=300,lowpass=f=3000", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32); x = x[int(a.skip*sr): len(x) - int(a.tail*sr)]
hop = sr // 100; env = np.sqrt(np.convolve(x**2, np.ones(hop)/hop, "same"))[::hop]
k = np.hanning(9); env = np.convolve(env, k/k.sum(), "same"); db = 20*np.log10(env + 1e-6); thr = np.percentile(db, 95) - 25
peaks = [i for i in range(1, len(db)-1) if db[i] > db[i-1] and db[i] >= db[i+1] and db[i] > thr and db[i] - min(db[max(0,i-12):i+12]) > 6]
n = int(a.win * 100); res = []
for s in range(0, len(db) - n // 2, n):
    seg = db[s:s+n]; voiced = np.mean(seg > thr); cnt = sum(1 for p in peaks if s <= p < s+n)
    res.append((s/100 + a.skip, cnt / (len(seg)/100), cnt / max(voiced*len(seg)/100, 1e-6), 1 - voiced))
for t, r, ar, ps in res: print(f"{int(t//60)}:{int(t%60):02d}  syl/s {r:4.2f}  articulation {ar:4.2f}  pause_share {ps:4.2f}")
R = [r[1] for r in res]; print(f"SUMMARY syl/s range {min(R):.2f}-{max(R):.2f}  sd {np.std(R):.2f}")
