#!/usr/bin/env python3
"""表現力（太淡／剛好／太激動）的兩種自動判斷，只記錄、不參與挑選（2026-11-27）。

為什麼：select_takes.py 的清楚、穩定、語速、聲紋都量不到 Clarence 聽得出的「太淡」「太激動」。
- measures.affect 的音高範圍只抓得到「太激動」（EP56 s01 Lite take2 9.8 半音，其他 6.3–7.7），
  「太淡」抓不到（s11 take0 7.9 比他選的 take2 7.3 還大）。
- EmergentTTS-Eval（NeurIPS 2025, arXiv 2505.23009）用 Gemini 2.5 Pro 兩兩比較，跟人的偏好高度相關。
  這裡照那個做法：同一段的幾次生成連同 D1 參考錄音一起給 Gemini 聽，正序、倒序各問一次抵掉位置偏差。

    # 1) 讓 Gemini 聽：每段寫進 <segments>/affect_judge.json
    python3 tools/affect_judge.py judge out/segments/D1_<ep> [--only s01,s11] [--script episodes/<ep>/script.json]

    # 2) Clarence 在 take_review.py 產生的頁面標好之後，把頁面上的 JSON 存成 tags.json，看兩種判斷跟他吻合多少
    python3 tools/affect_judge.py compare out/segments/D1_<ep> --tags /mnt/project-files/episodes/epNN/takes-tags.json

檔名預設是 <段>.take<N>.wav；其他命名（例如 EP56 的 s01-lite-take2.mp3）用 --pattern '*.mp3' --group-re '^(s\\d+)'。
花費記在 usage.jsonl（工具名 affect_judge）。Gemini 額度滿的時候不要跑，挑選不受影響。
"""
import argparse, json, os, random, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "voices/references/gemini-3.8-flash_d1-magnetic-night.flac"
LABELS = ("太淡", "剛好", "太激動")
MIME = {".wav": "audio/wav", ".mp3": "audio/mp3", ".flac": "audio/flac"}

PROMPT = """你是 podcast 的聲音導演。第一段音檔是主持人平常的語氣（參考），後面是同一段稿子的 {n} 個版本，依序叫 {names}。
主持人的設定：深夜科技 podcast 的台灣男主持人，低沉有磁性、慵懶放鬆，像半夜跟朋友聊天。
{text}只聽語氣和情緒的濃淡，不管念錯字、音質或長短：
- 太淡：平板、沒情緒、像在念稿，比參考還沒味道
- 剛好：跟參考的語氣濃度差不多，有起伏但放鬆
- 太激動：太亢奮、太用力、起伏太大，不像深夜聊天
每個版本給 label（太淡／剛好／太激動）和 closeness（1–5，5 = 語氣最像參考），再選出 best（最像參考的版本名）。
只回 JSON：{{"takes": {{"版本A": {{"label": "...", "closeness": 3, "why": "十個字以內"}}, ...}}, "best": "版本A"}}"""


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
            r = c.models.generate_content(model=model, contents=contents, config=cfg)
            j = json.loads(r.text)
            out = {}
            for nm, p in zip(names, files):
                t = j["takes"].get(nm, {})
                out[p.name] = {"label": t.get("label") if t.get("label") in LABELS else None,
                               "closeness": t.get("closeness"), "why": t.get("why", "")}
            return out, dict(zip(names, [p.name for p in files])).get(j.get("best"))
        except Exception as e:   # 空回覆、JSON 壞掉、網路斷：重試，三次都失敗就記空的
            print(f"    attempt {attempt + 1} failed: {type(e).__name__}: {str(e)[:120]}")
    return {p.name: {"label": None, "closeness": None, "why": ""} for p in files}, None


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
    res.update(model=a.model, reference=str(Path(a.reference).name)); res.setdefault("segments", {})
    c = client(); rnd = random.Random(a.seed)
    for seg, files in groups.items():
        order = files[:]; rnd.shuffle(order)
        runs = [ask(c, a.model, Path(a.reference), o, texts.get(seg, "")) for o in (order, order[::-1])]   # 正序、倒序
        takes = {}
        for p in files:
            labs = [r[0][p.name]["label"] for r in runs]; cl = [r[0][p.name]["closeness"] for r in runs if r[0][p.name]["closeness"]]
            takes[p.name] = {"label": labs[0] if labs[0] and labs[0] == labs[1] else "不確定", "labels": labs,
                             "closeness": round(sum(cl) / len(cl), 2) if cl else None, "why": [r[0][p.name]["why"] for r in runs]}
        bests = [r[1] for r in runs]
        scored = [t for t in takes if takes[t]["closeness"] is not None]
        best = bests[0] if bests[0] and bests[0] == bests[1] else (max(scored, key=lambda t: takes[t]["closeness"]) if scored else None)
        res["segments"][seg] = {"takes": takes, "best": best, "best_votes": bests}
        print(f"{seg:14s} " + "  ".join(f"{t}: {v['label']} {v['closeness']}" for t, v in takes.items()) + f"  -> {best}")
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"寫好 {out_path}")


def cmd_compare(a):
    """Clarence 的標註對照：音高範圍旗標、Gemini 標籤、Gemini 選的、select_takes 選的。"""
    import measures
    tags = json.loads(Path(a.tags).read_text(encoding="utf-8"))
    d = Path(a.segments)
    judge = json.loads((d / "affect_judge.json").read_text(encoding="utf-8")) if (d / "affect_judge.json").exists() else {"segments": {}}
    sel = json.loads((d / "select_log.json").read_text(encoding="utf-8")) if (d / "select_log.json").exists() else {"segments": []}
    flags = {r["file"]: bool(r.get("affect_flag")) for s in sel["segments"] for r in s["takes"] if "affect_flag" in r}
    chosen = {s["id"]: s["chosen"] for s in sel["segments"]}
    groups = group(d, a.pattern, a.group_re)
    if not flags:   # 沒有新版 select_log：直接量，門檻同 select_takes（整集中位數 + margin）
        aff = {p.name: measures.affect(p)["f0_range_st"] for v in groups.values() for p in v}
        med = sorted(aff.values())[len(aff) // 2] if aff else 0
        flags = {f: v > med + a.excited_margin for f, v in aff.items()}
    gem = {f: v["label"] for s in judge["segments"].values() for f, v in s["takes"].items()}
    T = tags.get("tags", {})
    rows = Counter()
    for f, lab in T.items():
        if lab not in LABELS:
            continue
        if f in flags:
            rows["flag_n"] += 1
            rows["flag_ok"] += (flags[f] == (lab == "太激動"))
            rows["excited_n"] += lab == "太激動"; rows["excited_hit"] += lab == "太激動" and flags[f]
            rows["false_flag"] += lab != "太激動" and flags[f]
        if gem.get(f) in LABELS:
            rows["gem_n"] += 1; rows["gem_ok"] += gem[f] == lab
        elif f in gem:
            rows["gem_unsure"] += 1
    P = tags.get("picks", {})
    for seg, pick in P.items():
        if not pick:
            continue
        rows["pick_n"] += 1
        rows["gem_best_ok"] += judge["segments"].get(seg, {}).get("best") == pick
        rows["sel_ok"] += chosen.get(seg) == pick
    pct = lambda x, n: f"{x}/{n} ({100 * x / n:.0f}%)" if n else "—"
    print(f"標註 {len([1 for v in T.values() if v in LABELS])} 個 take、{rows['pick_n']} 段有選")
    print(f"音高範圍旗標  整體一致 {pct(rows['flag_ok'], rows['flag_n'])}；他說太激動的抓到 {pct(rows['excited_hit'], rows['excited_n'])}；誤標 {rows['false_flag']}")
    print(f"Gemini 標籤   一致 {pct(rows['gem_ok'], rows['gem_n'])}（正倒序不一致、記成不確定 {rows['gem_unsure']}）")
    print(f"他選的那次    Gemini 也選 {pct(rows['gem_best_ok'], rows['pick_n'])}；select_takes 也選 {pct(rows['sel_ok'], rows['pick_n'])}")
    print("門檻（docs/voice.md）：吻合 75% 以上、且比 select_takes 現在的選擇更接近他，才考慮讓它參與挑選。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("judge", "compare"):
        p = sub.add_parser(name); p.add_argument("segments")
        p.add_argument("--pattern", default="*.take*.wav"); p.add_argument("--group-re", default=r"^(.+?)\.take\d+")
    j = sub.choices["judge"]
    j.add_argument("--reference", default=str(REFERENCE)); j.add_argument("--model", default="gemini-3.8-flash")
    j.add_argument("--only", default=""); j.add_argument("--script", default=""); j.add_argument("--seed", type=int, default=0)
    c = sub.choices["compare"]
    c.add_argument("--tags", required=True); c.add_argument("--excited-margin", type=float, default=2.0)
    a = ap.parse_args()
    {"judge": cmd_judge, "compare": cmd_compare}[a.cmd](a)
