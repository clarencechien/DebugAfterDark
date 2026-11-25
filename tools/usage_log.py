"""外部服務用量記錄：Gemini API（估算）和 Colab compute units（真實餘額），給工廠儀表板讀。

每呼叫一次就在專案檔案 /mnt/project-files/factory/usage.jsonl 追加一列 JSON（沒有專案檔案的機器寫 out/usage.jsonl）。
不花 token、不連網（Colab 餘額除外，是 `colab usage` 的真實數字）。記錄失敗絕不影響本來的工作。

- Gemini：Google 沒有給 API key 查帳單的介面，所以是「回應裡的 token 數 × 價目表」估出來的，儀表板標「估算」。
  價目表 PRICES 照 https://ai.google.dev/gemini-api/docs/pricing（2026-11-25 查，2026 年底前是優惠價，2027-01-01 起約兩倍）。
  真正的帳單和花費上限在 AI Studio／Google Cloud Billing 看。
- Colab：每次用完 GPU 跑 `colab --auth=adc usage` 記下餘額（compute units），儀表板用餘額的變化算用量。

用法（工具裡）：
    import usage_log
    usage_log.patch_gemini("rewrite_episode")      # 之後所有 generate_content 自動記
    usage_log.log_gemini("make_podcast", model, input_tokens=..., output_tokens=...)   # 不經 generate_content 的（TTS）
    usage_log.colab_snapshot(colab_exe, env, gpu="L4", gpu_s=123)

手動補一筆 Colab 餘額：python3 tools/usage_log.py colab
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_LOG = Path("/mnt/project-files/factory/usage.jsonl")
LOCAL_LOG = Path(__file__).resolve().parent.parent / "out" / "usage.jsonl"

# 每 100 萬 token 的美元價（輸入, 輸出）。圖片模型的輸出是圖片 token。查不到的模型用 DEFAULT。
PRICES = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.8-flash-tts": (0.75, 9.00),       # 輸出是音訊 token（約 25 token/秒）
    "gemini-3.8-flash-lite-tts": (0.75, 6.00),
    "gemini-3-pro-image": (2.00, 120.00),       # 一張 1K/2K 圖約 1,120 token ≈ US$0.134
}
DEFAULT = (1.50, 7.50)
# Gemini 每月花費上限（AI Studio 裡設的 spend limit）。儀表板拿來算剩多少；不知道就留 None。
GEMINI_MONTHLY_CAP_USD = None


def _path():
    return PROJECT_LOG if PROJECT_LOG.parent.parent.is_dir() else LOCAL_LOG


def _write(row):
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        row = {"time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **row}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:   # 記錄壞掉不能讓製作停下來
        print(f"  usage_log: skipped ({e})", file=sys.stderr)


def price(model, input_tokens, output_tokens):
    m = (model or "").removeprefix("models/")
    pin, pout = PRICES.get(m) or next((v for k, v in PRICES.items() if m.startswith(k)), DEFAULT)
    return (input_tokens or 0) / 1e6 * pin + (output_tokens or 0) / 1e6 * pout


def log_gemini(tool, model, input_tokens=0, output_tokens=0, calls=1):
    usd = price(model, input_tokens, output_tokens)
    _write({"service": "gemini", "tool": tool, "model": (model or "").removeprefix("models/"), "calls": calls,
            "input_tokens": input_tokens or 0, "output_tokens": output_tokens or 0, "usd_est": round(usd, 6)})


def patch_gemini(tool):
    """讓這個程式裡所有 client.models.generate_content 呼叫都記一列（用回應的 usage_metadata）。"""
    try:
        from google.genai import models
    except Exception:
        return
    if getattr(models.Models.generate_content, "_usage_logged", False):
        return
    orig = models.Models.generate_content

    def wrapped(self, *a, **kw):
        r = orig(self, *a, **kw)
        try:
            u = getattr(r, "usage_metadata", None)
            if u is not None:
                out = (getattr(u, "candidates_token_count", 0) or 0) + (getattr(u, "thoughts_token_count", 0) or 0)
                log_gemini(tool, kw.get("model") or (a[0] if a else ""), getattr(u, "prompt_token_count", 0) or 0, out)
        except Exception:
            pass
        return r
    wrapped._usage_logged = True
    models.Models.generate_content = wrapped


def colab_balance(exe, env):
    r = subprocess.run([exe, "--auth=adc", "usage"], env=env, capture_output=True, text=True, timeout=120)
    m = re.search(r"balance:\s*([\d.]+)", r.stdout)
    return float(m.group(1)) if m else None


def colab_snapshot(exe, env, **extra):
    try:
        bal = colab_balance(exe, env)
        if bal is not None:
            _write({"service": "colab", "balance_cu": bal, **extra})
    except Exception as e:
        print(f"  usage_log: colab balance skipped ({e})", file=sys.stderr)


if __name__ == "__main__":
    if sys.argv[1:] == ["colab"]:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import colab_remote
        env = colab_remote._env()
        colab_snapshot(colab_remote._cli(env), env, note="manual")
        print(f"寫好 {_path()}")
    else:
        print(__doc__)
