#!/usr/bin/env python3
"""每段幾次生成並排試聽，讓 Clarence 標「太淡／剛好／太激動」並選一次（2026-11-27）。

標完的結果給 tools/affect_judge.py compare 對照，看音高範圍旗標和 Gemini 判斷跟他吻合多少。
盲聽：頁面不顯示 select_takes 選了哪次，也不顯示任何數字。

    python3 tools/take_review.py out/segments/D1_<ep> /mnt/project-files/episodes/epNN/ \
        [--script episodes/<ep>/script.json] [--only s01,s11]

會在輸出資料夾寫 takes/<檔名>.mp3（64 kbps）和 epNN-takes.html（資料夾名稱當檔名前綴）。
頁面不用任何瀏覽器儲存：標到一半關掉會不見。最下面的框即時顯示結果 JSON，按「複製」或手動全選複製，
貼回對話，存成 <輸出資料夾>/takes-tags.json。
其他命名（例如 EP56 的 s01-lite-take2.mp3）用 --pattern '*.mp3' --group-re '^(s\\d+)'。
"""
import argparse, html, json, re, shutil, subprocess, sys
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
.opts button[aria-pressed=true]{{background:var(--on);border-color:var(--accent);color:var(--accent);font-weight:600}}
.opts .pick{{margin-left:auto}}
textarea{{width:100%;min-height:9em;font:13px/1.5 ui-monospace,monospace;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px}}
.row{{display:flex;gap:8px;align-items:center;margin:8px 0}}
.row button{{font:inherit;border:1px solid var(--accent);background:var(--accent);color:var(--card);border-radius:8px;padding:4px 14px;cursor:pointer}}
</style></head><body><main>
<h1>{title}</h1>
<p class="hint">每次生成點一個「太淡／剛好／太激動」，每段再點「選這個」。不用全部標完，標幾段都有用。頁面不會自己存，標完到最下面複製結果貼回對話。</p>
{body}
<h2 style="font-size:16px">結果</h2>
<div class="row"><button type="button" id="copy">複製</button><span class="hint" id="copied"></span></div>
<textarea id="out" readonly></textarea>
</main>
<script>
(function(){{
  var state = {{episode: {episode}, tags: {{}}, picks: {{}}}};
  var out = document.getElementById("out");
  function render(){{ out.value = JSON.stringify(state, null, 1); }}
  document.addEventListener("click", function(ev){{
    var b = ev.target.closest && ev.target.closest(".opts button"); if(!b) return;
    var f = b.getAttribute("data-file"), seg = b.getAttribute("data-seg");
    if(b.classList.contains("pick")){{
      var on = state.picks[seg] !== f;
      document.querySelectorAll('.pick[data-seg="' + seg + '"]').forEach(function(x){{ x.setAttribute("aria-pressed", "false"); }});
      if(on){{ state.picks[seg] = f; b.setAttribute("aria-pressed", "true"); }} else delete state.picks[seg];
    }} else {{
      var lab = b.getAttribute("data-label"), on2 = state.tags[f] !== lab;
      document.querySelectorAll('.opts button[data-file="' + f + '"]:not(.pick)').forEach(function(x){{ x.setAttribute("aria-pressed", "false"); }});
      if(on2){{ state.tags[f] = lab; b.setAttribute("aria-pressed", "true"); }} else delete state.tags[f];
    }}
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
    texts = {}
    if a.script:
        texts = {s["id"]: s["text"] for s in json.loads(Path(a.script).read_text(encoding="utf-8"))["segments"]}
    (out / "takes").mkdir(parents=True, exist_ok=True)
    sections = []
    for seg, files in groups.items():
        rows = []
        for p in files:
            mp3 = out / "takes" / (p.stem + ".mp3")
            if p.suffix == ".mp3":
                shutil.copyfile(p, mp3)
            elif not mp3.exists():
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(p), "-ac", "1", "-b:a", "64k", str(mp3)], check=True)
            e, s = html.escape(p.name), html.escape(seg)
            btns = "".join(f'<button type="button" data-seg="{s}" data-file="{e}" data-label="{lab}" aria-pressed="false">{lab}</button>'
                           for lab in ("太淡", "剛好", "太激動"))
            label = re.sub(r"^" + re.escape(seg) + r"[.\-_]?", "", p.stem) or p.stem
            rows.append(f'<div class="take"><strong>{html.escape(label)}</strong>'
                        f'<audio controls preload="none" src="takes/{html.escape(mp3.name)}"></audio>'
                        f'<div class="opts">{btns}<button type="button" class="pick" data-seg="{s}" data-file="{e}" aria-pressed="false">選這個</button></div></div>')
        text = f'<p class="text">{html.escape(texts[seg])}</p>' if seg in texts else ""
        sections.append(f'<section><h2>{html.escape(seg)}</h2>{text}{"".join(rows)}</section>')
    name = out.resolve().name
    page = out / f"{name}-takes.html"
    page.write_text(PAGE.format(title=html.escape(f"{name} 每次生成試聽"), episode=json.dumps(name),
                                body="\n".join(sections)), encoding="utf-8")
    print(f"寫好 {page}（{len(groups)} 段、{sum(len(v) for v in groups.values())} 次生成）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments"); ap.add_argument("out")
    ap.add_argument("--script", default=""); ap.add_argument("--only", default="")
    ap.add_argument("--pattern", default="*.take*.wav"); ap.add_argument("--group-re", default=r"^(.+?)\.take\d+")
    main(ap.parse_args())
