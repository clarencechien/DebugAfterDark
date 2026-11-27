#!/usr/bin/env python3
"""Gemini 選的 take 跟 Clarence 選的一不一樣：每段 1（一樣）或 0（不一樣）。只記錄、不參與挑選（2026-11-27）。

為什麼：select_takes.py 的清楚、穩定、語速、聲紋量不到他聽得出的「太淡」「太激動」。
EmergentTTS-Eval（NeurIPS 2025, arXiv 2505.23009）用 Gemini 做兩兩比較，跟人的偏好高度相關。
這裡把同一段的幾次生成連同 D1 參考錄音一起給 Gemini 聽，只問「哪一個語氣最像參考」。
正序、倒序各問一次抵掉位置偏差，兩次選的不一樣就記「不一致」（算 0）。
11/27 先試過讓它標「太淡／剛好／太激動」：它從不說太激動，正倒序常不一致；只看選哪一個時 EP56 兩段都跟他一樣。
Clarence 11/27：先簡化成 0/1，過跟不過；再反過來，Gemini 先選，他當挑戰者，有反對就改，記下不一樣的。

    # 1) 讓 Gemini 選：每段寫進 <segments>/affect_judge.json
    python3 tools/affect_judge.py judge out/segments/D1_<ep> --sample 4 [--only s01,s11] [--script episodes/<ep>/script.json]
    # Clarence 11/27：每集先抽樣 4 段當實驗（--sample 4），其他段維持 select_takes 的選擇

    # 2) take_review.py 的頁面已預選 Gemini 選的，Clarence 不同意才改；結果存成 takes-tags.json
    # 3) 套用：每段用他改的，沒改就用 Gemini 選的（Gemini 不一致又沒改的段落維持 select_takes 的選擇）
    python3 tools/affect_judge.py apply out/segments/D1_<ep> --tags /mnt/project-files/episodes/epNN/takes-tags.json
    # 4) 逐段 0/1：他沒改 = 1，改了 = 0；不一樣的記在 <segments>/affect_picks.json
    python3 tools/affect_judge.py compare out/segments/D1_<ep> --tags /mnt/project-files/episodes/epNN/takes-tags.json

apply 寫進 select_log.json 的 chosen / manual_override 並覆蓋 <段>.wav，所以要在最後一次 select_takes.py / steady_pick.py 之後跑
（它們會蓋掉 manual_override），跑完再做後製。

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
    if a.sample and a.sample < len(groups):   # Clarence 11/27：每集先抽樣幾段當實驗；同一集每次抽到同樣幾段
        keys = sorted(groups); random.Random(Path(a.segments).resolve().name).shuffle(keys)
        groups = {k: groups[k] for k in sorted(keys[:a.sample])}
        print(f"抽樣 {a.sample} 段：{', '.join(groups)}")
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


def load_tags(path, judge):
    """回傳 (gemini 選的, Clarence 改的)。也收舊格式 {"picks": {...}}：跟 Gemini 不一樣的才算改。"""
    t = json.loads(Path(path).read_text(encoding="utf-8"))
    gem = {k: v.get("best") for k, v in judge["segments"].items()}
    if "overrides" in t:
        return gem, {k: v for k, v in t["overrides"].items() if v}
    return gem, {k: v for k, v in t.get("picks", {}).items() if v and v != gem.get(k)}


def read(d, name, default):
    f = Path(d) / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


def cmd_apply(a):
    import shutil
    d = Path(a.segments)
    judge = read(d, "affect_judge.json", {"segments": {}}); log = read(d, "select_log.json", None)
    if log is None:
        sys.exit("沒有 select_log.json：先跑 select_takes.py")
    gem, ov = load_tags(a.tags, judge)
    for seg in log["segments"]:
        sid, old = seg["id"], seg["chosen"]
        if sid in ov:
            new, why = ov[sid], f"Clarence 改（Gemini 選 {gem.get(sid) or '不一致'}）"
        elif gem.get(sid):
            new, why = gem[sid], "Gemini 選的，Clarence 沒反對"
        else:
            continue
        if not (d / new).exists():
            print(f"{sid}: 找不到 {new}，跳過"); continue
        seg["chosen"] = new; seg["manual_override"] = why; seg["select_takes_chosen"] = seg.get("select_takes_chosen", old)
        shutil.copyfile(d / new, d / f"{sid}.wav")
        print(f"{sid:14s} {old.split('.')[1] if '.' in old else old} -> {new}  {why}")
    (d / "select_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    record(d, gem, ov, {s["id"]: s.get("select_takes_chosen", s["chosen"]) for s in log["segments"]})


def record(d, gem, ov, sel):
    """不一樣的記下來：<segments>/affect_picks.json。"""
    rows = {seg: {"gemini": g, "clarence": ov.get(seg, g), "agree": int(seg not in ov), "select_takes": sel.get(seg)}
            for seg, g in sorted(gem.items()) if g or seg in ov}
    n = len(rows); k = sum(r["agree"] for r in rows.values())
    s_ok = sum(int(r["select_takes"] == r["clarence"]) for r in rows.values() if r["select_takes"])
    (Path(d) / "affect_picks.json").write_text(json.dumps({"agree": k, "segments_n": n, "select_takes_agree": s_ok, "segments": rows},
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
    for seg, r in rows.items():
        print(f"{seg:14s} Gemini {r['agree']}" + ("" if r["agree"] else f"  你改成 {r['clarence']}（Gemini {r['gemini'] or '不一致'}）")
              + (f"  select_takes {int(r['select_takes'] == r['clarence'])}" if r["select_takes"] else ""))
    if n:
        print(f"Gemini {k}/{n}（{100 * k / n:.0f}%）" + (f"；select_takes {s_ok}/{n}" if any(r["select_takes"] for r in rows.values()) else ""))
    print("門檻（docs/voice.md）：累積約 30 段再看 Gemini 和 select_takes 各對幾成。")


def cmd_compare(a):
    """逐段 0/1：他沒改 = 1、改了 = 0（Gemini 不一致的段落算 0）。"""
    d = Path(a.segments)
    judge = read(d, "affect_judge.json", {"segments": {}}); log = read(d, "select_log.json", {"segments": []})
    gem, ov = load_tags(a.tags, judge)
    record(d, gem, ov, {s["id"]: s.get("select_takes_chosen", s["chosen"]) for s in log["segments"]})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("judge", "apply", "compare"):
        p = sub.add_parser(name); p.add_argument("segments")
        p.add_argument("--pattern", default="*.take*.wav"); p.add_argument("--group-re", default=r"^(.+?)\.take\d+")
    j = sub.choices["judge"]
    j.add_argument("--reference", default=str(REFERENCE)); j.add_argument("--model", default="gemini-3.8-flash")
    j.add_argument("--sample", type=int, default=0, help="只抽 N 段（每集固定同樣幾段）；0 = 全部")
    j.add_argument("--only", default=""); j.add_argument("--script", default=""); j.add_argument("--seed", type=int, default=0)
    for name in ("apply", "compare"):
        sub.choices[name].add_argument("--tags", required=True)
    a = ap.parse_args()
    {"judge": cmd_judge, "apply": cmd_apply, "compare": cmd_compare}[a.cmd](a)
