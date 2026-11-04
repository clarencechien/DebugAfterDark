"""Blind Gemini transcription of every take, character error rate against the script (punctuation, tags, case ignored)."""
import json, os, re, sys, difflib
from pathlib import Path
from google import genai
from google.genai import types
import opencc
conv = opencc.OpenCC("s2twp")
c = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ["gemini_key"])
P = "請逐字聽寫這段台灣華語音檔。只輸出聽到的文字，用繁體中文，英文照英文拼寫。聽不清楚的字用［?］代替，不要猜。不要加任何說明。"
def norm(t): return re.sub(r"<[^>]+>|[^\w]|_", "", conv.convert(t)).lower()
sc = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")); ref = {s["id"]: s["text"] for s in sc["segments"]}
out = {}
for p in sorted(Path(sys.argv[1]).glob("*.take*.wav")):
    seg = p.name.split(".")[0]
    hyp = c.models.generate_content(model="gemini-3.8-flash", contents=[types.Part.from_bytes(data=p.read_bytes(), mime_type="audio/wav"), P],
                                    config=types.GenerateContentConfig(temperature=0)).text.strip()
    a, b = norm(ref[seg]), norm(hyp)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    diffs = [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    err = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    out[p.stem] = {"cer": round(err / len(a), 3), "diffs": diffs, "hyp": hyp}
    print(f"{p.stem:18s} cer={err/len(a):.3f}  " + "  ".join(f"{x}→{y}" for x, y in diffs))
Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1))
