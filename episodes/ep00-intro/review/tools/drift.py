"""Windowed drift across one mastered episode: pitch, spectral centroid, speaker similarity to the episode mean.
  python drift.py file.mp3 [--skip 3.6] [--win 15]"""
import sys, subprocess, argparse
import numpy as np
sys.path.insert(0, "podcast")
from compare_voices import f0_track, centroid
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--skip", type=float, default=3.6); ap.add_argument("--tail", type=float, default=3.6); ap.add_argument("--win", type=float, default=15)
a = ap.parse_args(); sr = 16000
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.file, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32); x = x[int(a.skip*sr): len(x) - int(a.tail*sr)]
n = int(a.win * sr); W = [x[i:i+n] for i in range(0, len(x) - n // 2, n)]
try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    enc = VoiceEncoder("cpu", verbose=False)
    E = np.array([enc.embed_utterance(preprocess_wav(w, source_sr=sr)) for w in W])
except ImportError:
    E = np.ones((len(W), 2))
E /= np.linalg.norm(E, axis=1, keepdims=True)
m = E.mean(0); m /= np.linalg.norm(m)
P = [float(np.median(f0_track(w, sr))) for w in W]; C = [centroid(w, sr) for w in W]
nb = [float(E[i] @ E[i-1]) for i in range(1, len(E))]
for i, w in enumerate(W):
    t = a.skip + i * a.win
    print(f"{int(t//60)}:{int(t%60):02d}  pitch {P[i]:6.1f}  centroid {C[i]:5.0f}  sim_mean {float(E[i]@m):.3f}" + (f"  sim_prev {nb[i-1]:.3f}" if i else ""))
print(f"SUMMARY pitch_range {max(P)-min(P):.1f} Hz  centroid_range {max(C)-min(C):.0f} Hz  sim_prev mean {np.mean(nb):.3f} min {min(nb):.3f}  sim_mean min {float((E@m).min()):.3f}")
