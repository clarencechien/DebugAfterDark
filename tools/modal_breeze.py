"""Breeze-ASR-25 on a Modal GPU: the slow step of selection (20-25 min on this 4-core CPU) moved to a cloud GPU.

  modal deploy tools/modal_breeze.py          # once, and again after changing this file
  python3 tools/select_takes.py ... --asr breeze-modal
  python3 tools/stt_check.py ... --asr breeze-modal

Same model and same decoding as the local path in tools/stt_check.py: the CTranslate2 int8 conversion of
MediaTek-Research/Breeze-ASR-25, language zh, beam 5, VAD on, no prompt, and the same retry when timestamps run past the
end of the audio. Only the device differs (GPU, int8_float16), so picks should match the CPU run; compare before
relying on it (docs/recipe.md step 5).

Credentials: Modal reads MODAL_TOKEN_ID / MODAL_TOKEN_SECRET. In this cloud environment they are stored as `modal` and
`modal_secret`; transcribe_remote() maps them. The session reaches Modal through the HTTPS proxy, which needs
`pip install 'modal[api-proxy-support]'` (python-socks).
"""
import os

import modal

APP = "dad-breeze"
MODEL_DIR = "/model/breeze-asr-25-ct2-int8"

image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .pip_install("faster-whisper==1.2.1", "ctranslate2==4.8.5", "av<14", "transformers==4.57.6", "torch",
                 "huggingface_hub", "sentencepiece")
    .run_commands(
        f"ct2-transformers-converter --model MediaTek-Research/Breeze-ASR-25 --output_dir {MODEL_DIR} "
        "--quantization int8 --copy_files tokenizer.json preprocessor_config.json")
)
app = modal.App(APP, image=image)


# 2026-11-10: EP16's first batch waited 375 s for a container while the GPU worked 37 s. Fall back to other GPUs when
# L4 is scarce, start the container while the TTS takes are being made (warm_remote), and keep it 10 minutes so the
# retake rounds that follow selection find it running (idle L4 time is the cost of that).
@app.cls(gpu=["L4", "A10G", "T4"], timeout=1800, scaledown_window=600)
class Breeze:
    @modal.enter()
    def load(self):
        import time
        t0 = time.time()
        from faster_whisper import WhisperModel
        self.m = WhisperModel(MODEL_DIR, device="cuda", compute_type="int8_float16")
        self.started, self.load_s = t0, round(time.time() - t0, 1)

    @modal.method()
    def ping(self):
        """Warm-up: returns when the container is up and the model is loaded."""
        import subprocess, time
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
        return {"gpu": gpu, "load_s": self.load_s, "up_s": round(time.time() - self.started, 1)}


    @modal.method()
    def transcribe(self, items, beam=5):
        """items: [(name, wav_bytes)] -> {name: {"text", "segments"}}"""
        import io, time, wave
        t0 = time.perf_counter()
        out = {}
        for name, data in items:
            with wave.open(io.BytesIO(data)) as w:
                dur = w.getnframes() / w.getframerate()
            kw = dict(language="zh", beam_size=beam, vad_filter=True)
            segs = list(self.m.transcribe(io.BytesIO(data), **kw)[0])
            if segs and segs[-1].end > dur + 1.0:
                segs = list(self.m.transcribe(io.BytesIO(data), condition_on_previous_text=False, temperature=0.0, **kw)[0])
            out[name] = {"text": "".join(s.text for s in segs), "segments": [(round(s.start, 2), s.text) for s in segs]}
        out["__gpu_s"] = round(time.perf_counter() - t0, 1)   # inference only; the caller subtracts it from wall time
        out["__load_s"] = self.load_s                           # model load when this container started
        return out


def warm_remote():
    """Start a container without waiting for it (make_podcast.py episode calls this before the TTS takes). Never raises."""
    try:
        os.environ.setdefault("MODAL_TOKEN_ID", os.environ.get("modal", ""))
        os.environ.setdefault("MODAL_TOKEN_SECRET", os.environ.get("modal_secret", ""))
        return modal.Cls.from_name(APP, "Breeze")().ping.spawn()
    except Exception as e:
        print(f"  breeze-modal warm-up skipped ({type(e).__name__})")


def transcribe_remote(paths, beam=5, batch=12, timeout=600):
    """Called by stt_check.whisper_transcribe when ASR == 'breeze-modal'. Sends the wavs in batches, in parallel."""
    import time
    from pathlib import Path
    t_start = time.perf_counter()
    os.environ.setdefault("MODAL_TOKEN_ID", os.environ.get("modal", ""))
    os.environ.setdefault("MODAL_TOKEN_SECRET", os.environ.get("modal_secret", ""))
    paths = [Path(p) for p in paths]
    groups = [[(p.stem, p.read_bytes()) for p in paths[i:i + batch]] for i in range(0, len(paths), batch)]
    cls = modal.Cls.from_name(APP, "Breeze")
    res, failed = {}, []
    calls = [(g, cls().transcribe.spawn(g, beam)) for g in groups]
    for g, call in calls:
        for attempt in range(2):   # 2026-11-07: one run hung with nothing sent; bound each batch and retry it once
            try:
                r = call.get(timeout=timeout); gpu = r.pop("__gpu_s", None); r.pop("__load_s", None); res.update(r)
                # 2026-11-10: selection took 2 to 10 minutes on Modal while local features took 44 s; log where it goes
                print(f"  breeze-modal batch of {len(g)}: done {time.perf_counter() - t_start:.0f}s after start, GPU {gpu}s")
                break
            except Exception as e:
                print(f"  breeze-modal batch of {len(g)} failed ({type(e).__name__}); " + ("retrying" if attempt == 0 else "falling back to the local CPU"))
                if attempt == 0:
                    call = cls().transcribe.spawn(g, beam)
                else:
                    failed += [n for n, _ in g]
    if failed:   # never lose a run to the network: transcribe what Modal could not on this machine, same model and settings
        import stt_check as S
        S.ASR = "breeze"
        res.update(S.whisper_transcribe([p for p in paths if p.stem in failed]))
    for k in sorted(res):
        print(f"  breeze-modal {k}: {res[k]['text'][:40]}…")
    return res
