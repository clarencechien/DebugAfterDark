"""Breeze-ASR-25 on a Colab GPU, driven from this machine: the first choice of `--asr breeze-cloud` (2026-11-22).

  python3 tools/select_takes.py ... --asr breeze-cloud     # Colab L4 -> Modal -> local CPU
  python3 tools/stt_check.py ... --asr breeze-cloud
  python3 tools/colab_remote.py out/segments/D1_<ep>/*.take*.wav   # transcribe on Colab only, print timings

What it does per call: `colab new` (L4, then A100 when no L4 is free), upload tools/colab_breeze.py and the wavs (tar in
40 MB pieces: one 123 MB upload returned HTTP 500 on 2026-11-18), pip install + convert Breeze to CTranslate2 int8 on the
VM (~1.5 min), transcribe with a few threads on the one GPU, download the JSON, and always `colab stop`.
Same model, conversion and decoding as tools/modal_breeze.py and the local path; see docs/colab-vs-modal.md.
Any failure raises ColabError; stt_check.whisper_transcribe then tries Modal, then the local CPU.

Credentials: the Colab CLI (`google-colab-cli`, installed here with `uv tool install` when missing) authenticates with
application-default credentials from the env var COLAB_ADC_JSON (never printed). Every command takes `--auth=adc`.
Balance and burn rate: `colab --auth=adc usage` (2026-11-22: 200 CU; L4 1.94 CU/h, A100 6.73 CU/h, H100 not allowed).
"""
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from pathlib import Path

# T4 picked a different take in 3 of 19 segments (docs/colab-vs-modal.md); Modal is the next fallback.
# 2026-11-26 pool (docs/cost.md): Colab CU are the Google AI Pro monthly grant and Modal has US$30/month credit, so both
# are free up to their quota. A100 burns 6.73 CU/h against L4's 1.94, and when two episode threads select at once
# Colab refuses the second L4 anyway, so with Modal configured go straight to Modal instead of taking an A100.
GPUS = ("L4",) if os.environ.get("modal") else ("L4", "A100")
CHUNK = 40 * 1024 * 1024
HERE = Path(__file__).resolve().parent


class ColabError(RuntimeError):
    pass


def _env():
    creds = Path.home() / ".config/gcloud/application_default_credentials.json"
    if not creds.exists():
        adc = os.environ.get("COLAB_ADC_JSON")
        if not adc:
            raise ColabError("COLAB_ADC_JSON is not set")
        creds.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(creds, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(adc)
    env = dict(os.environ, GOOGLE_APPLICATION_CREDENTIALS=str(creds))
    env["PATH"] = f"{Path.home() / '.local/bin'}:{env.get('PATH', '')}"
    return env


def _cli(env):
    exe = shutil.which("colab", path=env["PATH"])
    if exe:
        return exe
    print("  breeze-colab: installing the Colab CLI")
    if not shutil.which("uv", path=env["PATH"]):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True, env=env)
    uv = shutil.which("uv", path=env["PATH"]) or "uv"
    subprocess.run([uv, "tool", "install", "-q", "google-colab-cli"], check=True, env=env)
    exe = shutil.which("colab", path=env["PATH"])
    if not exe:
        raise ColabError("colab CLI not found after install")
    return exe


def _run(cmd, env, stdin=None, timeout=900):
    r = subprocess.run(cmd, input=stdin, capture_output=True, text=True, env=env, timeout=timeout)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def _clean(text, n=300):
    """Last lines of CLI output without URLs: error URLs carry the runtime's token (docs/colab-vs-modal.md)."""
    lines = [l for l in text.strip().splitlines() if "http" not in l and "token" not in l.lower()]
    return " | ".join(lines[-4:])[-n:]


def _shell(colab, env, s, cmd, timeout=900):
    """Run a shell command on the VM; ok only if it printed the sentinel (exec does not pass the exit status back)."""
    code, out = _run([colab, "--auth=adc", "exec", "-s", s, "--timeout", str(timeout)], env,
                     stdin=f"!{cmd} && echo __COLAB_OK__\n", timeout=timeout + 120)
    if "__COLAB_OK__" not in out:
        raise ColabError(f"`{cmd.split()[0]} …` failed on the VM: {_clean(out)}")
    return out


def transcribe_remote(paths, beam=5, workers=3):
    """paths -> {stem: {"text", "segments"}}, like modal_breeze.transcribe_remote. Raises ColabError on any failure."""
    if beam != 5:
        raise ColabError("colab_breeze.py decodes with beam 5 only")
    t0 = time.perf_counter()
    paths = [Path(p) for p in paths]
    stems = [p.stem for p in paths]
    if len(set(stems)) != len(stems):
        raise ColabError("duplicate file names; results are keyed by name")
    env = _env()
    colab = _cli(env)
    s = f"dad-breeze-{uuid.uuid4().hex[:6]}"
    created, gpu = False, None
    try:
        for gpu in GPUS:
            code, out = _run([colab, "--auth=adc", "new", "-s", s, "--gpu", gpu], env, timeout=300)
            if "READY" in out:
                created = True
                break
            print(f"  breeze-colab: no {gpu} ({_clean(out, 120)})")
            _run([colab, "--auth=adc", "stop", "-s", s], env, timeout=120)
        if not created:
            raise ColabError("no Colab GPU available")
        # 2026-11-22: the first exec on a session that came up in 4 s hung for 7 minutes; wait for the kernel first
        for attempt in range(4):
            try:
                _shell(colab, env, s, "true", timeout=60)
                break
            except (ColabError, subprocess.TimeoutExpired):
                if attempt == 3:
                    raise ColabError("the Colab kernel never answered")
                time.sleep(10)
        print(f"  breeze-colab: {gpu} ready {time.perf_counter() - t0:.0f}s after start")
        with tempfile.TemporaryDirectory() as tmp:
            tar = Path(tmp) / "takes.tar"
            with tarfile.open(tar, "w") as t:
                for p in paths:
                    t.add(p, arcname=f"takes/{p.name}")
            data = tar.read_bytes()
            parts = []
            for i in range(0, len(data), CHUNK):
                part = Path(tmp) / f"takes.tar.{i // CHUNK:02d}"
                part.write_bytes(data[i:i + CHUNK])
                parts.append(part)
            for f in [HERE / "colab_breeze.py", *parts]:
                code, out = _run([colab, "--auth=adc", "upload", "-s", s, str(f), f"/content/{f.name}"], env, timeout=600)
                if code != 0:
                    raise ColabError(f"upload of {f.name} failed: {_clean(out)}")
            _shell(colab, env, s, "cd /content && cat takes.tar.* > takes.tar && tar xf takes.tar", timeout=300)
            print(f"  breeze-colab: uploaded {len(paths)} wavs ({len(data) / 1e6:.0f} MB) {time.perf_counter() - t0:.0f}s after start")
            _shell(colab, env, s, "cd /content && python colab_breeze.py --setup", timeout=900)
            print(f"  breeze-colab: model ready {time.perf_counter() - t0:.0f}s after start")
            _shell(colab, env, s, f"cd /content && python colab_breeze.py --in /content/takes --out /content/out.json "
                                  f"--workers {workers}", timeout=1800)
            local = Path(tmp) / "out.json"
            code, out = _run([colab, "--auth=adc", "download", "-s", s, "/content/out.json", str(local)], env, timeout=300)
            if not local.exists():
                raise ColabError(f"download failed: {_clean(out)}")
            got = json.loads(local.read_text(encoding="utf-8"))
    finally:
        if created:
            _run([colab, "--auth=adc", "stop", "-s", s], env, timeout=120)
            try:   # 用完記下 Colab 餘額（compute units），給工廠儀表板
                import usage_log
                usage_log.colab_snapshot(colab, env, gpu=gpu, wall_s=round(time.perf_counter() - t0))
            except Exception:
                pass
    res = {k: {"text": v["text"], "segments": [tuple(x) for x in v["segments"]]} for k, v in got["results"].items()}
    missing = set(stems) - set(res)
    if missing:
        raise ColabError(f"{len(missing)} files missing from the Colab result")
    m = got["meta"]
    print(f"  breeze-colab: {m['gpu']}, {m['files']} files, GPU {m['gpu_s']}s ({m.get('workers')} threads), "
          f"setup pip {m.get('pip_s')}s + convert {m.get('convert_s')}s, total {time.perf_counter() - t0:.0f}s")
    for k in sorted(res):
        print(f"  breeze-colab {k}: {res[k]['text'][:40]}…")
    return res


if __name__ == "__main__":
    out = transcribe_remote(sys.argv[1:])
    print(json.dumps({k: v["text"] for k, v in out.items()}, ensure_ascii=False, indent=1))
