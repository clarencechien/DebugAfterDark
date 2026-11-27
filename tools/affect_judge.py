#!/usr/bin/env python3
"""Gemini 選的 take 跟 Clarence 選的一不一樣：每段 1（一樣）或 0（不一樣）。只記錄、不參與挑選（2026-11-27）。

為什麼：select_takes.py 的清楚、穩定、語速、聲紋量不到他聽得出的「太淡」「太激動」。
EmergentTTS-Eval（NeurIPS 2025, arXiv 2505.23009）用 Gemini 做兩兩比較，跟人的偏好高度相關。
這裡把同一段的幾次生成連同 D1 參考錄音一起給 Gemini 聽，只問「哪一個語氣最像參考」。
正序、倒序各問一次抵掉位置偏差，兩次選的不一樣就記「不一致」（算 0）。
11/27 先試過讓它標「太淡／剛好／太激動」：它從不說太激動，正倒序常不一致；只看選哪一個時 EP56 兩段都跟他一樣。
Clarence 11/27：先簡化成 0/1，過跟不過。

    # 1) 讓 Gemini 選：每段寫進 <segments>/affect_judge.json
    python3 tools/affect_judge.py judge out/segments/D1_<ep> [--only s01,s11] [--script episodes/<ep>/script.json]

    # 2) Clarence 在 take_review.py 的頁面選好、結果存成 takes-tags.json 之後，逐段 0/1
    python3 tools/affect_judge.py compare out/segments/D1_<ep> --tags /mnt/project-files/episodes/epNN/takes-tags.json

檔名預設是 <段>.take<N>.wav；其他命名（例如 EP56 的 s01-lite-take2.mp3）用 --pattern '*.mp3' --group-re '^(s\\d+)'。
花費記在 usage.jsonl（工具名 affect_judge），每段約 US$0.014。Gemini 額度滿的時候不要跑，挑選不受影響。
"""
import argparse, json, os, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "voices/references/gemini-3.8-flash_d1-magnetic-night.flac"
MIME = {".wav": "audio/wav", ".mp3": "audio/mp3", ".flac": "audio/flac"}

PROMPT = """你是 podcast 的聲音導演。第一段音檔是主持人平常的語氣（參考），後面是同一段稿子的 {n} 個版本，依序叫 {names}。
主持人的設定：深夜科技 podcast 的台灣男主持人，低沉有磁性、慵懶放鬆，像半夜跟朋友聊天。
{text}只聽語氣：不要太淡（平板、像念稿），也不要太激動（太亢奮、起伏太大、太趕）。不管念錯字、音質或長短。
選出語氣最像參考、你會拿去上架的那一個。只回 JSON：{{"best": "版本A", "why": "十五個字以內"}}"""


def group(d, pattern, group_re):
    g = {}
    for p in sorted(Path(d).glob(pattern)):
        m = re.match(group_re, p.name)
        if m:
            g.setdefault(m.group(1), []).append(p)
    return {k: v for k, v in g.items() if len(v) >= 2}


def client():
    from google import genai
    try:   # 用量記錄給工廠儀表板
        import usage_log
        usage_log.patch_gemini("affect_judge")
    except ImportError:
        pass
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ["gemini_key"])


def ask(c, model, ref, files, text):
    """回傳 (選中的檔名或 None, 理由)。"""
    from google.genai import types
    names = ["版本" + chr(65 + i) for i in range(len(files))]
    part = lambda p: types.Part.from_bytes(data=p.read_bytes(), mime_type=MIME.get(p.suffix, "audio/wav"))
    contents = ["參考：", part(ref)]
    for nm, p in zip(names, files):
        contents += [nm + "：", part(p)]
    contents.append(PROMPT.format(n=len(files), names="、".join(names), text=f"稿子：{text}\n" if text else ""))
    cfg = types.GenerateContentConfig(temperature=0, response_mime_type="application/json")
    for attempt in range(3):
        try:
            j = json.loads(c.models.generate_content(model=model, contents=contents, config=cfg).text)
            pick = dict(zip(names, [p.name for p in files])).get(j.get("best"))
            if pick:
                return pick, j.get("why", "")
        except Exception as e:   # 空回覆、JSON 壞掉、網路斷：重試
            print(f"    attempt {attempt + 1} failed: {type(e).__name__}: {str(e)[:120]}")
    return None, ""


def cmd_judge(a):
    groups = group(a.segments, a.pattern, a.group_re)
    if a.only:
        keep = set(a.only.split(","))
        groups = {k: v for k, v in groups.items() if k in keep}
    texts = {}
    if a.script:
        texts = {s["id"]: s["text"] for s in json.loads(Path(a.script).read_text(encoding="utf-8"))["segments"]}
    out_path = Path(a.segments) / "affect_judge.json"
    res = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    res.update(model=a.model, reference=Path(a.reference).name); res.setdefault("segments", {})
    c = client(); rnd = random.Random(a.seed)
    for seg, files in groups.items():
        order = files[:]; rnd.shuffle(order)
        votes = [ask(c, a.model, Path(a.reference), o, texts.get(seg, "")) for o in (order, order[::-1])]   # 正序、倒序
        best = votes[0][0] if votes[0][0] and votes[0][0] == votes[1][0] else None
        res["segments"][seg] = {"best": best, "votes": [v[0] for v in votes], "why": [v[1] for v in votes]}
        print(f"{seg:14s} -> {best or '不一致 ' + str([v[0] for v in votes])}")
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"寫好 {out_path}")


def cmd_compare(a):
    """逐段 0/1：Gemini 選的、select_takes 選的，跟 Clarence 選的一不一樣。"""
    picks = json.loads(Path(a.tags).read_text(encoding="utf-8")).get("picks", {})
    d = Path(a.segments)
    judge = json.loads((d / "affect_judge.json").read_text(encoding="utf-8")) if (d / "affect_judge.json").exists() else {"segments": {}}
    sel = json.loads((d / "select_log.json").read_text(encoding="utf-8")) if (d / "select_log.json").exists() else {"segments": []}
    chosen = {s["id"]: s["chosen"] for s in sel["segments"]}
    g = s = n = 0
    for seg, pick in sorted(picks.items()):
        if not pick:
            continue
        gb = judge["segments"].get(seg, {}).get("best")
        gi, si = int(gb == pick), int(chosen.get(seg) == pick)
        g += gi; s += si; n += 1
        print(f"{seg:14s} 你選 {pick:28s} Gemini {gi}" + ("（不一致）" if seg in judge["segments"] and gb is None else "") +
              (f"  select_takes {si}" if chosen else ""))
    if n:
        print(f"Gemini {g}/{n}（{100 * g / n:.0f}%）" + (f"；select_takes {s}/{n}（{100 * s / n:.0f}%）" if chosen else ""))
    print("門檻（docs/voice.md）：累積約 30 段、Gemini 75% 以上且高過 select_takes，才考慮讓它參與挑選，接之前先問 Clarence。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("judge", "compare"):
        p = sub.add_parser(name); p.add_argument("segments")
        p.add_argument("--pattern", default="*.take*.wav"); p.add_argument("--group-re", default=r"^(.+?)\.take\d+")
    j = sub.choices["judge"]
    j.add_argument("--reference", default=str(REFERENCE)); j.add_argument("--model", default="gemini-3.8-flash")
    j.add_argument("--only", default=""); j.add_argument("--script", default=""); j.add_argument("--seed", type=int, default=0)
    sub.choices["compare"].add_argument("--tags", required=True)
    a = ap.parse_args()
    {"judge": cmd_judge, "compare": cmd_compare}[a.cmd](a)
