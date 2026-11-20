"""Match a new clip against the saved reference recordings (voices/references).

Use this when a model is retired or upgraded: generate the reference text with each candidate
voice on the new model, then pick the candidate whose speaker embedding is closest to the old reference.

  python3 tools/match_voice.py build                     # (re)compute embeddings in references.json
  python3 tools/match_voice.py match new_clip.wav [...]  # cosine similarity of each clip to every reference
  python3 tools/match_voice.py track [episodes/<ep> ...] # each published episode against its voice's reference -> voices/drift.json

Speaker embeddings come from Resemblyzer (English-trained d-vector, 256 dims). It needs torch, which is
heavy, so it is not in requirements.txt:
  python3 -m pip install --index-url https://download.pytorch.org/whl/cpu torch && python3 -m pip install resemblyzer
Scale observed on 2026-11-03 (Gemini, same sentence, 3 takes each):
  same model + same voice ~0.93, same voice one model generation apart ~0.87-0.90,
  different voice ~0.79-0.81. Treat it as a ranking signal, not an absolute threshold.
"""
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
REF_DIR = ROOT.parent / "voices" / "references"
REF_JSON = REF_DIR / "references.json"


def to_wav(path):
    """Decode any format (flac/mp3/wav) to 16 kHz mono wav via ffmpeg."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "16000", tmp], check=True)
    return tmp


def embed(path, enc=None):
    from resemblyzer import VoiceEncoder, preprocess_wav
    enc = enc or VoiceEncoder("cpu", verbose=False)
    e = enc.embed_utterance(preprocess_wav(to_wav(path)))
    return e / np.linalg.norm(e), enc


def f0_median(path):
    sys.path.insert(0, str(ROOT))
    from compare_voices import load, f0_track
    x, sr = load(to_wav(path))
    f0 = f0_track(x, sr)
    return round(float(np.median(f0)), 1) if len(f0) else None


def cmd_build():
    meta = json.loads(REF_JSON.read_text(encoding="utf-8"))
    enc = None
    for r in meta["references"]:
        p = REF_DIR / r["file"]
        e, enc = embed(p, enc)
        r["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        r["f0_median_hz"] = f0_median(p)
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                             capture_output=True, text=True).stdout.strip()
        r["duration_s"] = round(float(dur), 2)
        r["embedding_resemblyzer"] = [round(float(v), 5) for v in e]
        print(f"{r['file']:44s} F0={r['f0_median_hz']} dur={r['duration_s']}s")
    REF_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_match(files):
    meta = json.loads(REF_JSON.read_text(encoding="utf-8"))
    enc = None
    refs = [(r["file"], np.array(r["embedding_resemblyzer"])) for r in meta["references"]]
    for f in files:
        e, enc = embed(f, enc)
        scores = sorted(((float(np.dot(e, v)), name) for name, v in refs), reverse=True)
        print(f"\n{f}")
        for s, name in scores:
            print(f"  {s:.3f}  {name}")


DRIFT_JSON = ROOT.parent / "voices" / "drift.json"
DRIFT_DROP = 0.03   # flag an episode this far below the median of the episodes before it (2026-11-20 baseline: voices/drift.json)


def cmd_track(eps):
    """Speaker similarity of each published episode (mp3, ident skipped) to the reference of the voice it was made with.

    Catches a voice that changed without an error: a rerouted or updated TTS model, a recreated voice, a new style.
    Updates voices/drift.json in place; with no arguments it (re)measures every episode."""
    meta = json.loads(REF_JSON.read_text(encoding="utf-8"))
    refs = {r["voice"]: (r["file"], np.array(r["embedding_resemblyzer"])) for r in meta["references"]}
    drift = json.loads(DRIFT_JSON.read_text(encoding="utf-8")) if DRIFT_JSON.exists() else {"episodes": {}}
    drift["note"] = ("Resemblyzer similarity of each episode mp3 (from 4 s, after the ident) to voices/references for its voice_id. "
                     "The reference is one 19 s sentence, so absolute values sit lower than the 0.93 same-voice figure above; "
                     f"watch the trend: a drop of more than {DRIFT_DROP} below the median of earlier episodes is flagged.")
    paths = [Path(e) for e in eps] or sorted((ROOT.parent / "episodes").glob("ep*"))
    enc = None
    for ep in paths:
        mp = ep / "episode.json"
        if not mp.exists(): continue
        m = json.loads(mp.read_text(encoding="utf-8")); v = m.get("voice") or {}; mp3 = ep / (m.get("audio") or {}).get("file", "-")
        if not mp3.exists() or v.get("voice_id") not in refs: continue
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "4", "-i", str(mp3), "-ac", "1", "-ar", "16000", tmp], check=True)
        e, enc = embed(tmp, enc)
        ref_file, ref = refs[v["voice_id"]]
        drift["episodes"][ep.name] = {"number": m.get("number"), "voice_id": v["voice_id"], "model": v.get("model"),
                                      "model_served": v.get("model_served"), "style": v.get("style"), "reference": ref_file,
                                      "sim_reference": round(float(np.dot(e, ref)), 4), "audio_sha256": m["audio"].get("sha256")}
    rows = sorted(drift["episodes"].items(), key=lambda kv: (kv[1]["number"] is None, kv[1]["number"]))
    for k, (name, r) in enumerate(rows):
        before = [x["sim_reference"] for _, x in rows[max(0, k - 10):k] if x["voice_id"] == r["voice_id"]]
        base = float(np.median(before)) if len(before) >= 3 else None
        r["flag"] = bool(base is not None and r["sim_reference"] < base - DRIFT_DROP)
        print(f"{name:34s} {r['sim_reference']:.3f}" + (f"  median of previous {base:.3f}" if base else "") + ("  <-- voice changed?" if r["flag"] else ""))
    drift["episodes"] = dict(rows)
    DRIFT_JSON.write_text(json.dumps(drift, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("build", "match", "track"):
        sys.exit(__doc__)
    if sys.argv[1] == "build":
        cmd_build()
    elif sys.argv[1] == "track":
        cmd_track(sys.argv[2:])
    else:
        cmd_match(sys.argv[2:])
