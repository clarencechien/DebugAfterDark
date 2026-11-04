"""Objective delivery measures that the EP00 trial (2026-11-04) showed line up with what a listener hears.

  python3 tools/measures.py wobble <file> [--skip 3.6 --tail 3.6 --win 20]   # pitch jitter, large jumps, short breaks
  python3 tools/measures.py pace   <file> [--skip ... --win 15]              # syllable rate and pause share per window
  python3 tools/measures.py drift  <file> [--skip ... --win 15]              # pitch, brightness, voiceprint per window
  python3 tools/measures.py seams  <segment wavs in order>                   # brightness of the last/first 6 s at each seam

What the numbers meant on EP00 (episodes/ep00-intro/review/README.md):
- jitter (median semitone jump between 10 ms voiced frames): 0.20 sounded steady, 0.26 sounded "shaky" (抖).
- a segment that read 27% faster than the one before it sounded like a different delivery, even after tonal matching.
- a seam where the brightness of the last 6 s and the next first 6 s differ by ~700 Hz was audible; ~280 Hz was not.
Files with intro/outro stings: pass --skip 3.6 --tail 3.6.
"""
import argparse, subprocess, sys
from pathlib import Path
import numpy as np

SR = 16000


def read(path, skip=0.0, tail=0.0, sr=SR, af=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-i", str(path)] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)
    return x[int(skip * sr): len(x) - int(tail * sr)]


def f0_frames(x, sr=SR):
    """F0 every 10 ms (0 = unvoiced or silent), autocorrelation, 60-300 Hz."""
    n, h = int(sr * 0.04), int(sr * 0.01); lo, hi = sr // 300, sr // 60
    rms_all = np.sqrt(np.mean(x ** 2)) + 1e-9; f0 = []
    for i in range(0, len(x) - n, h):
        fr = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt((fr ** 2).mean()) < rms_all * 0.3:
            f0.append(0.0); continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        lag = lo + int(np.argmax(ac[lo:hi]))
        f0.append(sr / lag if ac[0] > 0 and ac[lag] / ac[0] > 0.45 else 0.0)
    return np.array(f0)


def _runs(f0):
    v = f0 > 0; runs = []; i = 0
    while i < len(f0):
        if v[i]:
            j = i
            while j < len(f0) and v[j]: j += 1
            runs.append((i, j)); i = j
        else:
            i += 1
    return runs


def wobble_stats(f0, a0=0, a1=None):
    """jitter (median |semitone jump| inside voiced runs), share of jumps > 1 semitone, 0.15-0.6 s breaks per minute."""
    a1 = len(f0) if a1 is None else a1
    rs = [(s, e) for s, e in _runs(f0) if s >= a0 and e <= a1 and e - s >= 3]
    if not rs:
        return {"jitter": 0.0, "big_jumps": 0.0, "short_breaks_per_min": 0.0}
    j = np.concatenate([np.abs(np.diff(12 * np.log2(f0[s:e]))) for s, e in rs]); j = j[j < 4]   # drop octave errors
    gaps = [rs[k + 1][0] - rs[k][1] for k in range(len(rs) - 1)]
    return {"jitter": round(float(np.median(j)), 3), "big_jumps": round(float(np.mean(j > 1.0)), 3),
            "short_breaks_per_min": round(sum(1 for g in gaps if 15 <= g <= 60) / ((a1 - a0) / 6000), 1)}


def wobble(path, skip=0.0, tail=0.0):
    return wobble_stats(f0_frames(read(path, skip, tail)))


def centroid(x, sr=SR):
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))); f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((spec * f).sum() / spec.sum())


def edges(path, sec=6.0, sr=24000):
    """Brightness (spectral centroid) of the first and last `sec` seconds, at the TTS rate (24 kHz).
    The seam limits (~700 Hz audible, ~280 Hz not) were measured at 24 kHz; at 16 kHz the same seam reads about half."""
    x = read(path, sr=sr); n = int(sec * sr)
    return round(centroid(x[:n], sr)), round(centroid(x[-n:], sr))


def syllable_rate(x, sr=SR):
    """Envelope peaks per second (Mandarin is close to one peak per syllable) and the share of time below the voice threshold."""
    hop = sr // 100; env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
    k = np.hanning(9); env = np.convolve(env, k / k.sum(), "same"); db = 20 * np.log10(env + 1e-6); thr = np.percentile(db, 95) - 25
    peaks = [i for i in range(1, len(db) - 1) if db[i] > db[i - 1] and db[i] >= db[i + 1] and db[i] > thr and db[i] - min(db[max(0, i - 12):i + 12]) > 6]
    return peaks, db, thr


def cmd_wobble(a):
    f0 = f0_frames(read(a.file, a.skip, a.tail)); W = int(a.win * 100)
    for s in range(0, len(f0) - W // 2, W):
        st = wobble_stats(f0, s, min(s + W, len(f0))); t = s / 100 + a.skip
        print(f"{int(t // 60)}:{int(t % 60):02d}  jitter {st['jitter']:.3f}  big_jumps {st['big_jumps']:.3f}  short_breaks/min {st['short_breaks_per_min']:5.1f}")
    st = wobble_stats(f0); print(f"SUMMARY jitter {st['jitter']:.3f}  big_jumps {st['big_jumps']:.3f}  short_breaks/min {st['short_breaks_per_min']:.1f}")


def cmd_pace(a):
    x = read(a.file, a.skip, a.tail, af="highpass=f=300,lowpass=f=3000"); peaks, db, thr = syllable_rate(x)
    n = int(a.win * 100); R = []
    for s in range(0, len(db) - n // 2, n):
        seg = db[s:s + n]; cnt = sum(1 for p in peaks if s <= p < s + n); r = cnt / (len(seg) / 100); R.append(r); t = s / 100 + a.skip
        print(f"{int(t // 60)}:{int(t % 60):02d}  syl/s {r:4.2f}  pause_share {1 - np.mean(seg > thr):4.2f}")
    print(f"SUMMARY syl/s {min(R):.2f}-{max(R):.2f}  sd {np.std(R):.2f}")


def cmd_drift(a):
    x = read(a.file, a.skip, a.tail); n = int(a.win * SR); W = [x[i:i + n] for i in range(0, len(x) - n // 2, n)]
    from resemblyzer import VoiceEncoder, preprocess_wav
    enc = VoiceEncoder("cpu", verbose=False)
    E = np.array([enc.embed_utterance(preprocess_wav(w, source_sr=SR)) for w in W]); E /= np.linalg.norm(E, axis=1, keepdims=True)
    m = E.mean(0); m /= np.linalg.norm(m)
    P = [float(np.median(f[f > 0])) if (f := f0_frames(w)).any() else float("nan") for w in W]; C = [centroid(w) for w in W]
    for i in range(len(W)):
        t = a.skip + i * a.win
        print(f"{int(t // 60)}:{int(t % 60):02d}  pitch {P[i]:6.1f}  centroid {C[i]:5.0f}  sim_mean {float(E[i] @ m):.3f}" + (f"  sim_prev {float(E[i] @ E[i - 1]):.3f}" if i else ""))
    nb = [float(E[i] @ E[i - 1]) for i in range(1, len(E))]
    print(f"SUMMARY pitch_range {np.nanmax(P) - np.nanmin(P):.1f} Hz  centroid_range {max(C) - min(C):.0f} Hz  sim_prev mean {np.mean(nb):.3f} min {min(nb):.3f}"
          "  (a final window shorter than --win reads low)")


def cmd_seams(a):
    e = [edges(f) for f in a.files]
    for k in range(1, len(e)):
        print(f"{Path(a.files[k - 1]).stem} -> {Path(a.files[k]).stem}: {e[k - 1][1]} -> {e[k][0]} Hz ({e[k][0] - e[k - 1][1]:+d})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("wobble", "pace", "drift"):
        p = sub.add_parser(name); p.add_argument("file"); p.add_argument("--skip", type=float, default=0); p.add_argument("--tail", type=float, default=0)
        p.add_argument("--win", type=float, default=20 if name == "wobble" else 15)
    p = sub.add_parser("seams"); p.add_argument("files", nargs="+")
    a = ap.parse_args(); {"wobble": cmd_wobble, "pace": cmd_pace, "drift": cmd_drift, "seams": cmd_seams}[a.cmd](a)
