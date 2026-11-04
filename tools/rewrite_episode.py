"""Rewrite every segment of an episode draft into Taiwanese spoken style (ported from ttspoc podcast/rewrite_episode.py, 799872e).

  python3 tools/rewrite_episode.py --episode episodes/<ep> [--n 3] [--resume]

Reads episodes/<ep>/draft.json (what each segment covers, its mood) and episodes/<ep>/sources/<segment_id>.txt (the
article excerpt; facts may only come from here). Writes episodes/<ep>/script.json and, per segment, every candidate,
lint result, prompt hash and the chosen index to episodes/<ep>/rewrites/<segment_id>.json. Manual fixes after review go
into that file's "manual_edits" list ({"from", "to", "reason"}) and into script.json.

Segments are rewritten in order; each prompt gets the previous segment's last two sentences so the episode flows, and its
position, so only the first segment is the cold open and only the last one carries the breakpoint and the sign-off.

Series: if draft.json has "previously" ({"episode": "EP01", "title": "...", "summary": "one or two sentences"}), the
recap segment (the one with "recap": true, else the first segment after the cold open) is told to open by linking back
to that episode, and candidates that never say 上一集 rank last. Without this the rewrite dropped "上一集聊過…" from EP02's
draft: the link is not in the sources, so the model treated it as filler (2026-11-04).
--resume reapplies each finished segment's manual_edits, so reviewed fixes survive a partial rerun.
"""
import argparse, hashlib, json, os, re, sys
from pathlib import Path
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from script_lint import lint

LEGACY_EP01_MOODS = {   # ep01's draft moods said 慵懶/壓低聲音, which made delivery timid; these replace them
   
    "s00_open": "開場，輕鬆，像剛按下錄音鍵跟朋友打招呼",
    "s01_copy": "講故事，帶點吐槽",
    "s02_speed": "輕鬆解說，條理清楚",
    "s03_altitude": "先覺得很帥，再恍然大悟",
    "s04_depth": "認真起來，但還是聊天的口氣",
    "s05_judge": "講到外部裁判時語氣認真一點，講到天文案例時興奮起來",
    "s06_range": "幽默，帶點吐槽",
    "s07_resolution": "工程師之間的共鳴，有點無奈",
    "s08_efficacy": "走心，慢一點但不拖",
    "s09_outro": "收尾，輕鬆溫暖",
}

# Signature phrases and how many times the whole episode may use each.
# Once a phrase reaches its cap, later segments are told not to use it, and candidates that do are ranked lower.
PHRASE_CAPS = {"你猜": 3, "重點來了": 2, "醬": 2, "應該說": 1, "有感": 2, "更扯的是": 1, "我看到這": 2, "超扯": 1, "很扯": 1,
               "真的假的": 1, "欸你知道嗎": 1,
               # self-corrections: rule 12 allows one per segment, which made nine of ten segments self-correct
               "我是說": 2, "我的意思是": 1, "呃不對": 1, "傻眼": 1}

def phrase_counts(text):
    return {k: text.count(k) for k in PHRASE_CAPS}

def last_sentences(text, k=2):
    parts = [x for x in re.split(r"(?<=[。？！])", re.sub(r"<[^>]+>", "", text).replace("\n", "")) if x.strip()]
    return "".join(parts[-k:])

def main(a):
    ep = Path(a.episode); draft = ep / "draft.json"; sc = json.loads(draft.read_text(encoding="utf-8"))
    out_path = ep / "script.json"; src_dir = ep / "sources"
    mood_of = lambda seg: (LEGACY_EP01_MOODS.get(seg["id"]) if ep.name.startswith("ep01") else None) or seg["mood"]
    body = (ROOT / "prompts/spoken_script_zh-TW.md").read_text(encoding="utf-8").split("\n---\n", 1)[1]
    c = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ["gemini_key"])
    outdir = ep / "rewrites"; outdir.mkdir(parents=True, exist_ok=True)
    segs = sc["segments"]; new_segments = []; previous = "（這是第一段，沒有上一段）"
    prev_ep = sc.get("previously")
    recap_i = next((k for k, x in enumerate(segs) if x.get("recap")), 1 if prev_ep and len(segs) > 2 else None)
    def recap_text(i):
        if not prev_ep or i != recap_i:
            return "（這段不用提上一集）"
        return f"{prev_ep['episode']}〈{prev_ep['title']}〉：{prev_ep['summary']}"
    used = {k: 0 for k in PHRASE_CAPS}
    for i, seg in enumerate(segs):
        done = outdir / f"{seg['id']}.json"
        if a.resume and done.exists():
            # container restarts kill long runs: reuse finished segments and rebuild budget + context from them
            rec = json.loads(done.read_text(encoding="utf-8"))
            text = rec["candidates"][rec["chosen"]]["text"].replace("\n", "")
            for e in rec.get("manual_edits", []):        # reviewed fixes live here, not in the candidate text
                if e["from"] in text:
                    text = text.replace(e["from"], e["to"])
                else:
                    print(f"  warning: {seg['id']} manual edit no longer applies: {e['from'][:30]}…")
            for k, v in phrase_counts(text).items():
                used[k] += v
            new_segments.append({"id": seg["id"], "mood": mood_of(seg), "text": text})
            previous = last_sentences(text)
            print(f"{seg['id']:16s} resumed (chose {rec['chosen']})")
            continue
        n = lint(seg["text"])["chars"]
        pos = f"第 {i + 1} 段，共 {len(segs)} 段" + ("（第一段）" if i == 0 else "（最後一段）" if i == len(segs) - 1 else "")
        prompt = (body.replace("{{show}}", sc["show"]).replace("{{audience}}", sc["audience"])
                  .replace("{{source}}", (src_dir / f"{seg['id']}.txt").read_text(encoding="utf-8").strip())
                  .replace("{{current}}", seg["text"]).replace("{{position}}", pos).replace("{{previous}}", previous)
                  .replace("{{min_chars}}", str(int(n * 0.8))).replace("{{max_chars}}", str(int(n * 1.2)))
                  .replace("{{previously}}", recap_text(i)))
        avoid = [k for k, cap in PHRASE_CAPS.items() if used[k] >= cap]
        prompt = prompt.replace("{{avoid}}", "、".join(f"「{k}」" for k in avoid) if avoid else "（無）")
        cands = []
        for _ in range(a.n):
            t = c.models.generate_content(model=a.model, contents=prompt,
                                          config=types.GenerateContentConfig(temperature=a.temperature)).text.strip()
            cands.append({"text": t, "lint": lint(t)})
        def over_budget(t):
            pc = phrase_counts(t)
            return sum(max(0, used[k] + pc[k] - PHRASE_CAPS[k]) for k in PHRASE_CAPS) + sum(max(0, v - 1) for v in pc.values())
        needs_recap = i == recap_i and prev_ep is not None
        key = lambda j: (needs_recap and "上一集" not in cands[j]["text"], len(cands[j]["lint"]["mainland_words"]), over_budget(cands[j]["text"]),
                         len(cands[j]["lint"]["precise_numbers"]), cands[j]["lint"]["sentences_over_20"],
                         cands[j]["lint"]["avg_sentence_len"])
        best = min(range(len(cands)), key=key)
        for k, v in phrase_counts(cands[best]["text"]).items():
            used[k] += v
        if needs_recap and "上一集" not in cands[best]["text"]:
            print(f"  warning: {seg['id']} should link back to {prev_ep['episode']} but no candidate says 上一集; fix by hand")
        rec = {"segment": seg["id"], "position": pos, "avoid": avoid, "recap": recap_text(i) if needs_recap else None, "model": a.model, "temperature": a.temperature,
               "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "previous_context": previous,
               "original": {"text": seg["text"], "lint": lint(seg["text"])}, "candidates": cands, "chosen": best}
        (outdir / f"{seg['id']}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        text = cands[best]["text"].replace("\n", "")
        new_segments.append({"id": seg["id"], "mood": mood_of(seg), "text": text})
        previous = last_sentences(text)
        L = cands[best]["lint"]
        print(f"{seg['id']:16s} chose {best}  chars {n}->{L['chars']}  avg_sent {L['avg_sentence_len']}  nums {L['precise_numbers']}  mainland {L['mainland_words']}  avoid {avoid}")
    out = {k: v for k, v in sc.items() if k != "segments"}
    out["note"] = "由 tools/rewrite_episode.py 依 prompts/spoken_script_zh-TW.md 改寫；人工修正記在 rewrites/<id>.json 的 manual_edits"
    out["segments"] = new_segments
    out["phrase_usage"] = used
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", out_path)
    print("phrase usage:", {k: v for k, v in used.items() if v})

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--episode", required=True, help="episodes/<ep>")
    ap.add_argument("--model", default="gemini-3.8-flash"); ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--resume", action="store_true", help="reuse segments already written to episodes/<ep>/rewrites/")
    main(ap.parse_args())
