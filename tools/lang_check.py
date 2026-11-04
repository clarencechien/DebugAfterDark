"""Check takes of a non-Chinese edition (en, ja): blind transcript error rate, pitch jitter, pace, and whether the
voice still sounds like the Chinese Ping (Resemblyzer similarity to a reference set of zh-TW segments).

  python3 tools/lang_check.py --script episodes/ep00-intro/en/script.json --segments out/segments/D1_ep00-en \
      --ref out/segments/D1_ep05-reef-chart --out episodes/ep00-intro/en/qa/lang_check.json

Pilot tool (2026-11-04) for the multilingual question; the zh-TW pipeline keeps using select_takes.py / stt_check.py.
- Transcripts come from Whisper large-v3-turbo with the script's "language". Error rate is word-level for en and
  character-level for ja (kana/kanji spelling differences count as errors, so compare takes, not absolute numbers).
- Jitter is the same measure as the zh pipeline (measures.wobble), but tones make Mandarin wobble more, so the
  0.23 target does not carry over; compare takes and languages, not against that number.
- "sim_zh" is cosine similarity to the mean voiceprint of the reference segments; "zh baseline" is how similar the
  reference segments are to their own mean, i.e. what "same speaker" looks like for this voice.
Picks per segment: clearest within a margin, then lowest jitter; copies the pick to <segment>.wav for mastering.
"""
import argparse, json, re, shutil, sys, wave
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measures import wobble  # noqa: E402


def norm_words(s):
    s = re.sub(r"<[^>]+>", " ", s).lower().replace("’", "'")
    return re.findall(r"[a-z0-9']+", s)


def norm_chars(s):
    s = re.sub(r"<[^>]+>", "", s)
    return [c for c in s.lower() if c.isalnum()]


def edit_rate(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i in range(1, len(ref) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(hyp) + 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ref[i - 1] != hyp[j - 1]))
    return d[len(hyp)] / max(len(ref), 1)


def duration(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def main(a):
    sc = json.loads(Path(a.script).read_text(encoding="utf-8")); lang = sc["language"]
    seg_dir = Path(a.segments)
    from faster_whisper import WhisperModel
    from resemblyzer import VoiceEncoder, preprocess_wav
    asr = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8"); enc = VoiceEncoder("cpu", verbose=False)
    emb = lambda p: (lambda e: e / np.linalg.norm(e))(enc.embed_utterance(preprocess_wav(p)))
    refs = [emb(p) for p in sorted(Path(a.ref).glob("s*_*.wav")) if ".take" not in p.name]
    ref_mean = np.mean(refs, axis=0); ref_mean /= np.linalg.norm(ref_mean)
    baseline = [round(float(r @ ref_mean), 3) for r in refs]
    norm = norm_words if lang == "en" else norm_chars
    report = {"language": lang, "ref": a.ref, "zh_baseline": baseline, "segments": []}
    for s in sc["segments"]:
        ref_units = norm(s["text"]); takes = []
        for p in sorted(seg_dir.glob(f"{s['id']}.take*.wav")):
            segs = list(asr.transcribe(str(p), language=lang, beam_size=5, vad_filter=True,
                                       condition_on_previous_text=False)[0])
            text = " ".join(x.text.strip() for x in segs) if lang == "en" else "".join(x.text for x in segs)
            dur = duration(p); w = wobble(p)
            takes.append({"file": p.name, "error": round(edit_rate(ref_units, norm(text)), 3), "jitter": w["jitter"],
                          "units_per_s": round(len(ref_units) / dur, 2), "seconds": round(dur, 1),
                          "sim_zh": round(float(emb(p) @ ref_mean), 3), "text": text})
            t = takes[-1]
            print(f"{p.stem:18s} err {t['error']:.3f}  jit {t['jitter']:.3f}  {t['units_per_s']:5.2f}/s  sim_zh {t['sim_zh']:.3f}")
        best_err = min(t["error"] for t in takes)
        pick = min((t for t in takes if t["error"] <= best_err + a.margin), key=lambda t: t["jitter"])
        shutil.copyfile(seg_dir / pick["file"], seg_dir / f"{s['id']}.wav")
        report["segments"].append({"id": s["id"], "chosen": pick["file"], "takes": takes})
        print(f"  -> {s['id']}: {pick['file']}")
    print("zh baseline (reference segments vs their mean):", baseline)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--script", required=True); ap.add_argument("--segments", required=True)
    ap.add_argument("--ref", required=True, help="folder of chosen zh-TW segment wavs from a finished episode")
    ap.add_argument("--margin", type=float, default=0.02, help="error-rate margin within which takes count as equally clear")
    ap.add_argument("--out")
    main(ap.parse_args())
