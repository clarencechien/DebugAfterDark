import json, os, sys
from pathlib import Path
from google import genai
from google.genai import types
c = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ["gemini_key"])
keys = ["ping_verb", "ping_name", "ping_explain", "pong"]
prompt = ("這段台灣華語裡，英文詞出現在：「我先 ping 你一下」「我是 Ping」「就是那個 ping」「回我一個 pong」。只判斷發音，不評價口音好壞。"
          "對每一個，回答比較像：A 英文單字（像台灣人講 double check 那樣的英文念法），或 B 中文的一個字（例如「平」「拼」「頻」「碰」，有明顯的中文聲調）。"
          "只輸出 JSON，鍵是 " + "、".join(keys) + '，值是 {"class": "A或B", "heard_as": "拼音或英文"}')
out = {}
for p in sorted(Path(sys.argv[1]).glob("*.take*.wav")):
    r = c.models.generate_content(model="gemini-3.8-flash", contents=[types.Part.from_bytes(data=p.read_bytes(), mime_type="audio/wav"), prompt],
          config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
    j = json.loads(r.text); out[p.stem] = j
    print(p.stem, " ".join(f"{k}={j[k]['class']}({j[k]['heard_as']})" for k in keys if k in j))
Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1))
