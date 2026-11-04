"""Second opinion from Gemini 3.8 Flash on rendered takes (no Breeze needed). Rough screening only.

  python3 tools/gemini_check.py clarity --script episodes/<ep>/script.json --segments out/segments/D1_<ep> [--out f.json]
  python3 tools/gemini_check.py terms   --segments out/segments/D1_<ep> --terms Ping,pong [--out f.json]

clarity: blind transcription (the script is not shown), character error rate against the script.
terms:   for each take whose script contains one of the terms, asks whether each occurrence sounded like an English word
         (A, the way Taiwanese speakers say "double check") or like a Mandarin syllable (B, e.g. 平, 碰).
Gemini could not tell Taiwanese from mainland accents in the POC; do not use it for accent.
"""
import argparse, difflib, json, os, re
from pathlib import Path


def client():
    from google import genai
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ["gemini_key"])


def audio(p):
    from google.genai import types
    return types.Part.from_bytes(data=Path(p).read_bytes(), mime_type="audio/wav")


BLIND = "請逐字聽寫這段台灣華語音檔。只輸出聽到的文字，用繁體中文，英文照英文拼寫。聽不清楚的字用［?］代替，不要猜。不要加任何說明。"


def cmd_clarity(a):
    import opencc
    from google.genai import types
    conv = opencc.OpenCC("s2twp"); c = client()
    norm = lambda t: re.sub(r"<[^>]+>|[^\w]|_", "", conv.convert(t)).lower()
    ref = {s["id"]: s["text"] for s in json.loads(Path(a.script).read_text(encoding="utf-8"))["segments"]}; out = {}
    for p in sorted(Path(a.segments).glob("*.take*.wav")):
        seg = p.name.split(".")[0]
        hyp = c.models.generate_content(model="gemini-3.8-flash", contents=[audio(p), BLIND], config=types.GenerateContentConfig(temperature=0)).text.strip()
        x, y = norm(ref[seg]), norm(hyp); sm = difflib.SequenceMatcher(None, x, y, autojunk=False)
        ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
        out[p.stem] = {"cer": round(sum(max(i2 - i1, j2 - j1) for _, i1, i2, j1, j2 in ops) / len(x), 3),
                       "diffs": [(x[i1:i2], y[j1:j2]) for _, i1, i2, j1, j2 in ops], "hyp": hyp}
        print(f"{p.stem:20s} cer={out[p.stem]['cer']:.3f}  " + "  ".join(f"{u}→{v}" for u, v in out[p.stem]["diffs"]))
    if a.out: Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_terms(a):
    from google.genai import types
    c = client(); terms = a.terms.split(","); out = {}
    script = json.loads(Path(a.script).read_text(encoding="utf-8")) if a.script else None
    texts = {s["id"]: s["text"] for s in script["segments"]} if script else {}
    for p in sorted(Path(a.segments).glob("*.take*.wav")):
        seg = p.name.split(".")[0]; t = texts.get(seg, "")
        found = [w for w in terms if not t or re.search(re.escape(w), t, re.I)]
        if not found: continue
        prompt = ("這段是台灣華語，裡面有英文詞：" + "、".join(found) + "。只判斷發音，不評價口音好壞。每一次出現，回答比較像："
                  "A 英文單字（像台灣人講 double check 那樣的英文念法），或 B 中文的一個字（例如「平」「拼」「頻」「碰」，有明顯的中文聲調）。"
                  '只輸出 JSON：{"occurrences": [{"term": "…", "class": "A或B", "heard_as": "拼音或英文"}]}')
        r = c.models.generate_content(model="gemini-3.8-flash", contents=[audio(p), prompt],
                                      config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
        occ = json.loads(r.text).get("occurrences", []); out[p.stem] = occ
        print(f"{p.stem:20s} " + " ".join(f"{o.get('term')}={o.get('class')}({o.get('heard_as')})" for o in occ))
    if a.out: Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("clarity"); p.add_argument("--script", required=True); p.add_argument("--segments", required=True); p.add_argument("--out")
    p = sub.add_parser("terms"); p.add_argument("--segments", required=True); p.add_argument("--terms", required=True); p.add_argument("--script"); p.add_argument("--out")
    a = ap.parse_args(); {"clarity": cmd_clarity, "terms": cmd_terms}[a.cmd](a)
