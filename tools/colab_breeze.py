"""Breeze-ASR-25 on a Colab VM, for comparing against tools/modal_breeze.py (2026-11-18 trial, docs/colab-vs-modal.md).

Runs ON the Colab VM (uploaded with `colab upload`, started with `colab exec`):
  python colab_breeze.py --setup                      # pip install + convert Breeze to CTranslate2 int8 (same as the Modal image)
  python colab_breeze.py --in /content/takes --out /content/colab_breeze.json

Same model, conversion and decoding as modal_breeze.Breeze.transcribe: language zh, beam 5, VAD on, no prompt, and the
same retry when timestamps run past the end of the audio; compute_type int8_float16. Only the GPU (Colab T4) and the
place the model is converted differ. Writes per-file text, segments and seconds, plus load and setup times.
"""
import glob
import json
import os
import subprocess
import sys
import time
import wave

MODEL_DIR = "/content/breeze-asr-25-ct2-int8"


def setup():
    t0 = time.time()
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "faster-whisper==1.2.1", "ctranslate2==4.8.5", "av<14"], check=True)
    t1 = time.time()
    if not os.path.exists(os.path.join(MODEL_DIR, "model.bin")):
        subprocess.run(["ct2-transformers-converter", "--model", "MediaTek-Research/Breeze-ASR-25", "--output_dir", MODEL_DIR,
                        "--quantization", "int8", "--copy_files", "tokenizer.json", "preprocessor_config.json"], check=True)
    t2 = time.time()
    json.dump({"pip_s": round(t1 - t0, 1), "convert_s": round(t2 - t1, 1)}, open("/content/colab_setup.json", "w"))
    print(f"setup: pip {t1 - t0:.0f}s, convert {t2 - t1:.0f}s")


def cuda12_libs():
    """Colab's image is CUDA 13 (2026-11); ctranslate2 4.8.5 needs libcublas.so.12, which pip ships in nvidia-cublas-cu12.
    Same workaround as colabpoc's phase1: put the CUDA 12 cublas/cudnn wheels on LD_LIBRARY_PATH and restart."""
    if os.environ.get("CT2_LIBS_SET"):
        return
    want = ("libcublas.so.12", "libcudnn.so.9")
    found = subprocess.run(["bash", "-c", "find / -name 'libcublas.so.12' -o -name 'libcudnn.so.9' 2>/dev/null"],
                           capture_output=True, text=True).stdout.split()
    dirs = sorted({os.path.dirname(p) for p in found if os.path.basename(p) in want})
    env = dict(os.environ, CT2_LIBS_SET="1", LD_LIBRARY_PATH=":".join(dirs + [os.environ.get("LD_LIBRARY_PATH", "")]))
    os.execve(sys.executable, [sys.executable] + sys.argv, env)


def transcribe(indir, out, beam=5):
    cuda12_libs()
    from faster_whisper import WhisperModel
    t0 = time.time()
    m = WhisperModel(MODEL_DIR, device="cuda", compute_type="int8_float16")
    load_s = round(time.time() - t0, 1)
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    res, t1 = {}, time.perf_counter()
    files = sorted(glob.glob(os.path.join(indir, "**", "*.wav"), recursive=True))
    for path in files:
        name = os.path.splitext(os.path.relpath(path, indir))[0]   # keep the episode folder: s00_open.take0 is in every episode
        with wave.open(path) as w:
            dur = w.getnframes() / w.getframerate()
        kw = dict(language="zh", beam_size=beam, vad_filter=True)
        ts = time.perf_counter()
        segs = list(m.transcribe(path, **kw)[0])
        if segs and segs[-1].end > dur + 1.0:
            segs = list(m.transcribe(path, condition_on_previous_text=False, temperature=0.0, **kw)[0])
        res[name] = {"text": "".join(s.text for s in segs), "segments": [(round(s.start, 2), s.text) for s in segs],
                     "dur_s": round(dur, 2), "proc_s": round(time.perf_counter() - ts, 2)}
    meta = {"gpu": gpu, "load_s": load_s, "files": len(files), "gpu_s": round(time.perf_counter() - t1, 1)}
    if os.path.exists("/content/colab_setup.json"):
        meta.update(json.load(open("/content/colab_setup.json")))
    json.dump({"meta": meta, "results": res}, open(out, "w"), ensure_ascii=False)
    print(json.dumps(meta))


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup()
    else:
        transcribe(sys.argv[sys.argv.index("--in") + 1], sys.argv[sys.argv.index("--out") + 1])
