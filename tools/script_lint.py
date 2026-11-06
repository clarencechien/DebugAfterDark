"""Measure how 'spoken' a script segment is, against the rules in prompts/spoken_script_zh-TW.md.

  python3 tools/script_lint.py episodes/<ep>/script.json [segment_id ...]
  python3 tools/script_lint.py some_file.txt

Reports: precise numbers (decimals, percentages, multi-digit counts), enumeration markers,
sentence length, particles per 100 chars, written-style words, tags.
"""
import json, re, sys
from pathlib import Path

DIGIT = "零一二兩三四五六七八九十百千萬"
# A "precise number" is one a listener must hold in memory: decimals, percentages, or values >= 10.
PRECISE = re.compile(rf"百分之[{DIGIT}點]+|[{DIGIT}]+點[{DIGIT}]+|[0-9]+(?:\.[0-9]+)?%?|[{DIGIT}]*十[{DIGIT}]*|[{DIGIT}]*[百千萬][{DIGIT}]*")
ENUM = re.compile(r"第[一二三四五六七八九十]+")
PARTICLES = re.compile(r"[欸齁啦喔吧嘛耶捏咧哦蛤]")
WRITTEN = ["推估", "因此", "此外", "然而", "其中", "對應", "處方", "藉由", "透過", "進行", "以及", "並且"]
TAG = re.compile(r"<[^>]+>")
# Written finance/academic terms and English jargon that made EP06's first cut unsteady and mainland-leaning (prompt rule 18).
JARGON = ["超額報酬", "過擬合", "樣本外", "樣本內", "套利", "投顧", "部位", "平倉", "多重測試", "真名"]
JARGON_EN = re.compile(r"\b(?:edge|alpha|beta|Sharpe|PF)\b", re.I)
# Bare 「報告」 opening a sentence or clause is heard as 「包括」 (EP06, EP09); say 「這份報告」「報告裡」 (prompt rule 19).
MISHEARD = re.compile(r"(?:^|[。！？，；：])\s*報告(?!裡|中|上)")
SELF_FIX = re.compile(r"呃我是說|我是說|呃不對|換個說法|應該說|——|……")
# Mainland-flavoured words a Taiwanese listener flags (keep in sync with rule 13 of the prompt)
# Not mainland usage, but Taiwanese listeners say people around them rarely talk like this (2026-11-04: 超有感).
AVOID = {"有感": r"有感(?!觸|情|應|而)"}
MAINLAND = ["更狠的是", "盲猜", "坑",  # 坑: flagged by a Taiwanese listener on EP01 (ttspoc RESULTS)
             "咱們", "挺", "這事兒", "視頻", "質量", "信息", "軟件", "靠譜", "牛逼", "絕了", "立馬",
            "整活", "老鐵", "點贊", "回頭再說", "兒", "啥"]

def lint(text):
    clean = TAG.sub("", text)
    sentences = [s for s in re.split(r"[。？！?!]", clean) if s.strip()]
    lens = [len(re.sub(r"\s", "", s)) for s in sentences]
    # skip idioms that only look like numbers: 千萬不要 / 千萬別 (= "by no means")
    nums = [m.group(0) for m in PRECISE.finditer(clean)
            if m.group(0) not in ("十",) and not (m.group(0) == "千萬" and clean[m.end():m.end() + 1] in "不別")]
    chars = len(re.sub(r"\s", "", clean))
    return {
        "chars": chars,
        "precise_numbers": nums,
        "enumerations": ENUM.findall(clean),
        "sentences": len(lens),
        "avg_sentence_len": round(sum(lens) / len(lens), 1) if lens else 0,
        "max_sentence_len": max(lens) if lens else 0,
        "sentences_over_20": sum(1 for l in lens if l > 20),
        "particles_per_100": round(len(PARTICLES.findall(clean)) / chars * 100, 1) if chars else 0,
        "written_words": [w for w in WRITTEN if w in clean],
        "jargon": [w for w in JARGON if w in clean] + JARGON_EN.findall(clean),
        "self_corrections": len(SELF_FIX.findall(clean)),
        "bare_report": len(MISHEARD.findall(clean)),
        "mainland_words": [w for w in MAINLAND if w in clean and not (w == "兒" and ("兒子" in clean or "女兒" in clean))],
        "avoid_words": [w for w, rx in AVOID.items() if re.search(rx, clean)],
        "questions": clean.count("？") + clean.count("?"),
        "tags": len(TAG.findall(text)),
    }

def show(name, r):
    print(f"\n== {name}")
    for k, v in r.items():
        print(f"  {k:18s} {v}")

if __name__ == "__main__":
    src = Path(sys.argv[1])
    if src.suffix == ".json":
        sc = json.loads(src.read_text(encoding="utf-8"))
        ids = set(sys.argv[2:])
        for s in sc["segments"]:
            if not ids or s["id"] in ids:
                show(s["id"], lint(s["text"]))
    else:
        show(src.name, lint(src.read_text(encoding="utf-8")))
