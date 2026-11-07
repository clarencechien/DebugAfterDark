"""Pick, per segment, the take a blind recogniser understands best, then the steadiest and best-matched one.

Order of filters (each keeps the takes close enough to the best one, then hands them to the next):
  1. clarity      Breeze (or Whisper) CER against the script, within --tolerance of the clearest take
  2. terms        with --terms Ping,pong: the blind transcript must contain each term as often as the script does
                  (proxy for "said as the English word"; skipped for a segment where no take passes)
  3. steadiness   pitch jitter (tools/measures.py) within --jitter-margin of the steadiest take; EP00 showed 0.26
                  semitones sounds shaky where 0.20 does not
  4. pace         characters per second within --pace-margin (10%) of the episode median; a segment 27% faster than
                  the one before sounded like a different delivery on EP00 even after tonal matching
  5. consistency  (--consistency) voiceprint and brightness, as below
  6. long pauses  fewest per minute
Ported from ttspoc podcast/select_takes.py (799872e); steps 2-4 added 2026-11-04 from the EP00 trial.

make_podcast.py --takes N keeps the take with the fewest long pauses; that ignores intelligibility.
This re-ranks the saved takes by Breeze-ASR-25 (or Whisper) character error rate against the script: takes within
--tolerance of the clearest one count as equally clear, and among those the one with fewest long pauses wins.
With --neighbour (needs --consistency), a final pass swaps a segment's take for another clear-enough take that is
more similar to the takes chosen for the adjacent segments (by more than --neighbour-margin).
With --consistency, two more filters run before the pause rule so segments sound like the same take of the
same voice: speaker similarity to the episode's average voice (Resemblyzer, all takes of all segments) must be
within --sim-margin of the best candidate, and spectral centroid must be within --bright-margin Hz of the closest
candidate to the episode median (brightness jumps were the most audible drift).
The winner is copied to <segment>.wav and the choice recorded in select_log.json.

  python3 tools/select_takes.py --script episodes/<ep>/script.json --segments out/segments/D1_<ep> --asr breeze \
          --terms Ping,pong --consistency --neighbour
"""
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import stt_check as S
from make_podcast import long_pauses, wav_duration, spoken_chars
import measures

def main(a):
    import opencc
    conv = opencc.OpenCC("s2twp"); S.ASR = a.asr; S.BEAM = a.beam
    sc = json.loads(Path(a.script).read_text(encoding="utf-8")); d = Path(a.segments)
    takes = {s["id"]: sorted(d.glob(f"{s['id']}.take*.wav")) for s in sc["segments"]}
    allc = [p for v in takes.values() for p in v]
    old = d / "select_log.json"
    T = {}
    if a.reuse and old.exists():   # transcription is the slow part; reuse it and only transcribe new takes
        T = {Path(r["file"]).stem: {"text": r["text"], "segments": r.get("segments", [])} for seg in json.loads(old.read_text(encoding="utf-8"))["segments"] for r in seg["takes"]}
    missing = [p for p in allc if p.stem not in T]
    if missing:
        T.update(S.whisper_transcribe(missing))
    import numpy as np
    feats = {}
    if a.consistency:
        from resemblyzer import VoiceEncoder, preprocess_wav
        from compare_voices import load, centroid
        enc = VoiceEncoder("cpu", verbose=False)
        for p in allc:
            e = enc.embed_utterance(preprocess_wav(p)); x, sr = load(p)
            feats[p.name] = {"emb": e / np.linalg.norm(e), "centroid": centroid(x, sr)}
        mean = np.mean([f["emb"] for f in feats.values()], axis=0); mean /= np.linalg.norm(mean)
        med_c = float(np.median([f["centroid"] for f in feats.values()]))
        for f in feats.values():
            f["sim"] = float(f["emb"] @ mean); f["bright_gap"] = abs(f["centroid"] - med_c)
    import re
    steady = {p.name: measures.wobble(p)["jitter"] for p in allc}
    cps = {p.name: spoken_chars(next(x["text"] for x in sc["segments"] if p.name.startswith(x["id"] + "."))) / wav_duration(p) for p in allc}
    med_cps = float(np.median(list(cps.values())))
    terms = [t for t in (a.terms or "").split(",") if t]
    log = []
    for s in sc["segments"]:
        ref = S.norm(s["text"], conv); rows = []
        for p in takes[s["id"]]:
            hyp = S.norm(T[p.stem]["text"], conv)
            row = {"file": p.name, "cer": round(S.cer(ref, hyp), 3), "unclear": len(S.real_misses(S.misses(ref, hyp))),
                   "long_pauses_per_min": round(long_pauses(p) / wav_duration(p) * 60, 1), "text": T[p.stem]["text"],
                   "segments": T[p.stem].get("segments", [])}
            row.update(jitter=steady[p.name], cps=round(cps[p.name], 2),
                       terms_ok=all(len(re.findall(re.escape(t), T[p.stem]["text"], re.I)) >= len(re.findall(re.escape(t), s["text"], re.I)) for t in terms))
            if feats:
                row.update(sim_to_episode=round(feats[p.name]["sim"], 3), centroid=round(feats[p.name]["centroid"]),
                           bright_gap=round(feats[p.name]["bright_gap"]))
            rows.append(row)
        # CER differences of ~0.01 (2-3 characters per segment) are within recogniser noise, so among takes that are
        # almost as clear as the clearest one, prefer the one with the fewest long pauses
        floor = min(r["cer"] for r in rows)
        cand = [r for r in rows if r["cer"] <= floor + a.tolerance]
        if terms and any(r["terms_ok"] for r in cand):
            cand = [r for r in cand if r["terms_ok"]]
        low = min(r["jitter"] for r in cand)
        cand = [r for r in cand if r["jitter"] <= low + a.jitter_margin]
        near = [r for r in cand if abs(r["cps"] / med_cps - 1) <= a.pace_margin]
        cand = near or [min(cand, key=lambda r: abs(r["cps"] / med_cps - 1))]
        if feats:
            top = max(r["sim_to_episode"] for r in cand)
            cand = [r for r in cand if r["sim_to_episode"] >= top - a.sim_margin]
            closest = min(r["bright_gap"] for r in cand)
            cand = [r for r in cand if r["bright_gap"] <= closest + a.bright_margin]
        best = min(cand, key=lambda r: (r["long_pauses_per_min"], r["cer"]))
        log.append({"id": s["id"], "chosen": best["file"], "takes": rows,
                    "clear_enough": [r["file"] for r in rows if r["cer"] <= floor + a.tolerance]})
        extra = (lambda r: f" jit {r['jitter']:.3f} cps {r['cps']}" + ("" if r["terms_ok"] else " TERMS?") + (f" sim {r['sim_to_episode']:.3f} bright {r['centroid']}" if feats else ""))
        print(f"{s['id']:16s} " + "  ".join(f"{r['file'].split('.')[1]}: CER {r['cer']:.3f} pauses/min {r['long_pauses_per_min']}{extra(r)}" for r in rows) + f"  -> {best['file'].split('.')[1]}")
    if a.neighbour and feats:
        # Neighbour pass: a jump between two adjacent segments is what listeners hear as "a different person".
        # Among takes that are clear enough, switch to one that matches the chosen neighbours better by > margin.
        for _ in range(2):
            for k, seg in enumerate(log):
                nb = [log[j]["chosen"] for j in (k - 1, k + 1) if 0 <= j < len(log)]
                score = lambda f: float(np.mean([feats[f]["emb"] @ feats[n]["emb"] for n in nb]))
                cur = score(seg["chosen"])
                alt = max(seg["clear_enough"], key=score)
                if score(alt) > cur + a.neighbour_margin:
                    print(f"  neighbour pass: {seg['id']} {seg['chosen'].split('.')[1]} -> {alt.split('.')[1]} (neighbour similarity {cur:.3f} -> {score(alt):.3f})")
                    seg["chosen"] = alt
    for seg in log:
        shutil.copyfile(d / seg["chosen"], d / f"{seg['id']}.wav")
    (d / "select_log.json").write_text(json.dumps({"asr": a.asr, "beam": a.beam, "tolerance": a.tolerance, "terms": terms, "jitter_margin": a.jitter_margin,
                                                   "pace_margin": a.pace_margin, "episode_median_cps": round(med_cps, 2), "consistency": a.consistency,
                                                   "sim_margin": a.sim_margin, "bright_margin": a.bright_margin, "segments": log}, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--script", required=True); ap.add_argument("--segments", required=True)
    ap.add_argument("--asr", default="breeze", choices=["breeze", "whisper", "breeze-modal"])
    ap.add_argument("--tolerance", type=float, default=0.012, help="CER margin within which takes count as equally clear")
    ap.add_argument("--reuse", action="store_true", help="reuse transcripts from an earlier select_log.json")
    ap.add_argument("--consistency", action="store_true", help="also require similar voice and brightness across segments")
    ap.add_argument("--sim-margin", type=float, default=0.015); ap.add_argument("--bright-margin", type=float, default=300)
    ap.add_argument("--neighbour", action="store_true", help="with --consistency: also prefer takes that match adjacent segments")
    ap.add_argument("--neighbour-margin", type=float, default=0.01)
    ap.add_argument("--beam", type=int, default=5, help="recogniser beam size; 1 = greedy (faster)")
    ap.add_argument("--terms", default="", help="comma-separated English terms that must appear in the blind transcript, e.g. Ping,pong")
    ap.add_argument("--jitter-margin", type=float, default=0.02, help="semitones above the steadiest take still accepted")
    ap.add_argument("--pace-margin", type=float, default=0.10, help="allowed deviation from the episode median characters per second")
    main(ap.parse_args())
