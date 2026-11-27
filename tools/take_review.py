#!/usr/bin/env python3
"""每段幾次生成並排試聽，Gemini 選的先標好，Clarence 當挑戰者：不同意才改（2026-11-27）。

有 <segments>/affect_judge.json（tools/affect_judge.py judge）時，每段 Gemini 選的那次預先標「Gemini 選的」；
他改了的段落記在結果 JSON 的 overrides，沒改就算同意。之後 affect_judge.py apply 把結果套進這集（改了的用他的）。
沒有 affect_judge.json 或 Gemini 兩次不一致的段落，沒有預選，他選了也記在 overrides。
11/27 演變：先有「太淡／剛好／太激動」標籤 → 簡化成每段選一個 → 改成 Gemini 先選、他挑戰。
盲聽：頁面不顯示 select_takes 選了哪次，也不顯示任何數字。

    python3 tools/take_review.py out/segments/D1_<ep> /mnt/project-files/episodes/epNN/ \
        [--script episodes/<ep>/script.json] [--only s01,s11]

會在輸出資料夾寫 epNN-takes.html（資料夾名稱當檔名前綴）。音檔轉成 48 kbps 單聲道 mp3 直接嵌進頁面：
在 Library／儀表板的預覽框裡讀不到旁邊的 mp3（11/27 EP56 試用時播不出來），嵌進去才能在哪裡打開都播得出來。
30 次生成、每次 40 秒約 10 MB。
Library 的預覽框連內嵌音檔也播不了（11/27 播放鍵反白）：那就加 --linked（mp3 放 takes/），
把頁面連同 takes/*.mp3 發佈成 claude.ai Artifact 再開連結。
頁面不用任何瀏覽器儲存：標到一半關掉會不見。最下面的框即時顯示結果 JSON，按「複製」或手動全選複製，
貼回對話，存成 <輸出資料夾>/takes-tags.json。
其他命名（例如 EP56 的 s01-lite-take2.mp3）用 --pattern '*.mp3' --group-re '^(s\\d+)'。
"""
import argparse, base64, html, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from affect_judge import group

PAGE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#f5f5f1;--card:#fff;--ink:#1d1d1b;--ink2:#55544f;--line:#e4e2dc;--accent:#2f5fd0;--chip:#efeee9;--on:#dfe7fb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--ink2:#b5b3ac;--line:#33322f;--accent:#8fb0ff;--chip:#2a2a27;--on:#26304a}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 system-ui,-apple-system,"Noto Sans TC","PingFang TC",sans-serif}}
main{{max-width:760px;margin:0 auto;padding:12px 16px 60px}}
h1{{font-size:21px;line-height:1.4}}
.hint{{color:var(--ink2);font-size:14px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin:16px 0}}
section h2{{font-size:16px;margin:0 0 4px}}
.text{{color:var(--ink2);font-size:14px;margin:0 0 8px;max-height:6.8em;overflow:auto}}
.take{{border-top:1px solid var(--line);padding:8px 0}}
.take audio{{width:100%;display:block;margin:4px 0}}
.opts{{display:flex;flex-wrap:wrap;gap:6px}}
.opts button{{font:inherit;font-size:14px;border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:999px;padding:2px 12px;cursor:pointer;min-height:32px}}
.badge{{display:inline-block;font-size:12px;font-weight:600;color:var(--accent);background:var(--on);border-radius:999px;padding:0 8px;margin-left:6px}}
.nogem{{color:var(--ink2);font-size:13px}}
.opts button[aria-pressed=true]{{background:var(--on);border-color:var(--accent);color:var(--accent);font-weight:600}}
textarea{{width:100%;min-height:9em;font:13px/1.5 ui-monospace,monospace;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px}}
.row{{display:flex;gap:8px;align-items:center;margin:8px 0}}
.row button{{font:inherit;border:1px solid var(--accent);background:var(--accent);color:var(--card);border-radius:8px;padding:4px 14px;cursor:pointer}}
</style></head><body><main>
<h1>{title}</h1>
<p class="hint">每段已經標好 Gemini 選的那一個。你不同意就點別的「改用這個」，同意就不用動。頁面不會自己存，聽完到最下面複製結果貼回對話。</p>
{body}
<h2 style="font-size:16px">結果</h2>
<div class="row"><button type="button" id="copy">複製</button><span class="hint" id="copied"></span></div>
<textarea id="out" readonly></textarea>
</main>
<script>
(function(){{
  var gemini = {gemini}, picks = {{}};
  Object.keys(gemini).forEach(function(k){{ if(gemini[k]) picks[k] = gemini[k]; }});
  var out = document.getElementById("out");
  function render(){{
    var ov = {{}};
    Object.keys(picks).forEach(function(k){{ if(picks[k] !== gemini[k]) ov[k] = picks[k]; }});
    document.querySelectorAll(".opts button.pick").forEach(function(x){{
      var on = picks[x.getAttribute("data-seg")] === x.getAttribute("data-file");
      x.setAttribute("aria-pressed", on ? "true" : "false"); x.textContent = on ? "用這個" : "改用這個";
    }});
    out.value = JSON.stringify({{episode: {episode}, gemini: gemini, overrides: ov}}, null, 1);
  }}
  document.addEventListener("click", function(ev){{
    var b = ev.target.closest && ev.target.closest(".opts button"); if(!b) return;
    var f = b.getAttribute("data-file"), seg = b.getAttribute("data-seg");
    if(picks[seg] === f && !gemini[seg]) delete picks[seg]; else picks[seg] = f;
    render();
  }});
  document.getElementById("copy").addEventListener("click", function(){{
    out.select();
    var done = function(){{ document.getElementById("copied").textContent = "複製好了，貼回對話"; }};
    try {{ navigator.clipboard.writeText(out.value).then(done, function(){{ document.execCommand("copy"); done(); }}); }}
    catch(e){{ document.execCommand("copy"); done(); }}
  }});
  render();
}})();
</script>
</body></html>
"""


def main(a):
    seg_dir, out = Path(a.segments), Path(a.out)
    groups = group(seg_dir, a.pattern, a.group_re)
    if a.only:
        keep = set(a.only.split(","))
        groups = {k: v for k, v in groups.items() if k in keep}
    judge = Path(a.segments) / "affect_judge.json"
    gem = {k: v.get("best") for k, v in json.loads(judge.read_text(encoding="utf-8"))["segments"].items()} if judge.exists() else {}
    if a.judged_only and judge.exists():   # 只放 Gemini 判過的段落（affect_judge.py judge --sample 抽到的）
        groups = {k: v for k, v in groups.items() if k in gem}
    gem = {k: gem.get(k) for k in groups}
    texts = {}
    if a.script:
        texts = {s["id"]: s["text"] for s in json.loads(Path(a.script).read_text(encoding="utf-8"))["segments"]}
    out.mkdir(parents=True, exist_ok=True)
    sections = []
    for seg, files in groups.items():
        rows = []
        for p in files:
            mp3 = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-ac", "1", "-b:a", "48k", "-f", "mp3", "-"],
                                 capture_output=True, check=True).stdout
            if a.linked:   # 檔案放旁邊的 takes/，發佈成 claude.ai Artifact（連同 takes/*.mp3）時用
                (out / "takes").mkdir(exist_ok=True); (out / "takes" / (p.stem + ".mp3")).write_bytes(mp3)
                src = "takes/" + html.escape(p.stem) + ".mp3"
            else:
                src = "data:audio/mpeg;base64," + base64.b64encode(mp3).decode()
            e, s = html.escape(p.name), html.escape(seg)
            label = re.sub(r"^" + re.escape(seg) + r"[.\-_]?", "", p.stem) or p.stem
            badge = '<span class="badge">Gemini 選的</span>' if gem.get(seg) == p.name else ""
            rows.append(f'<div class="take"><strong>{html.escape(label)}</strong>{badge}'
                        f'<audio controls preload="metadata" src="{src}"></audio>'
                        f'<div class="opts"><button type="button" class="pick" data-seg="{s}" data-file="{e}" aria-pressed="false">改用這個</button></div></div>')
        text = f'<p class="text">{html.escape(texts[seg])}</p>' if seg in texts else ""
        nog = '' if gem.get(seg) else '<p class="nogem">Gemini 這段沒有共識（或還沒跑），請你選一個。</p>'
        sections.append(f'<section><h2>{html.escape(seg)}</h2>{nog}{text}{"".join(rows)}</section>')
    name = out.resolve().name
    page = out / f"{name}-takes.html"
    page.write_text(PAGE.format(title=html.escape(f"{name} 每次生成試聽"), episode=json.dumps(name), gemini=json.dumps(gem, ensure_ascii=False),
                                body="\n".join(sections)), encoding="utf-8")
    print(f"寫好 {page}（{len(groups)} 段、{sum(len(v) for v in groups.values())} 次生成）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments"); ap.add_argument("out")
    ap.add_argument("--script", default=""); ap.add_argument("--only", default="")
    ap.add_argument("--judged-only", action="store_true", help="只放 affect_judge.json 裡有的段落（配合 judge --sample）")
    ap.add_argument("--linked", action="store_true", help="mp3 寫到 takes/ 用相對路徑（發佈成 Artifact 用），預設嵌進頁面")
    ap.add_argument("--pattern", default="*.take*.wav"); ap.add_argument("--group-re", default=r"^(.+?)\.take\d+")
    main(ap.parse_args())
