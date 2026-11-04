"""Assemble the GitHub Pages site: feed.xml, cover, audio, a listening page. Standard library only (runs on the
Actions runner without pip).

  python3 tools/build_site.py [--out site]

Checks before writing anything: every final episode's mp3 exists and matches episode.json byte for byte (size and
sha256), because the RSS <enclosure length> must equal the file. A mismatch means tools/package_episode.py was not rerun.
"""
import argparse, hashlib, html, json, re, shutil, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import feed

ROOT = feed.ROOT


def para(s):
    out = []
    for block in s.strip().split("\n\n"):
        t = html.escape(block).replace("\n", "<br>")
        t = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', t)
        out.append(f"<p>{t}</p>")
    return "\n".join(out)


def length(sec):
    """Episode length as 7 分 15 秒: next to a date, 7:15 read like a clock time (2026-11-04 feedback)."""
    m, s = divmod(int(round(sec)), 60)
    return f"{m} 分 {s:02d} 秒"


def split_notes(desc):
    """Show notes -> (lead paragraph, breakpoint lines, other blocks). Template: episodes/ep00-intro/script.md."""
    blocks = [b.strip() for b in desc.strip().split("\n\n") if b.strip()]
    lead, bps, rest = blocks[0] if blocks else "", [], []
    for b in blocks[1:]:
        if b.startswith("今晚的 breakpoint"):
            bps = [re.sub(r"^\d+\.\s*", "", l).strip() for l in b.split("\n")[1:] if l.strip()]
        else:
            rest.append(b)
    return lead, bps, rest


def page(show, eps):
    site = show["site_url"].rstrip("/")
    latest = next((e for e in eps if e.get("type") != "trailer"), eps[0] if eps else None)
    items = []
    for e in eps:
        d = datetime.fromisoformat(e["published"]); trailer = e.get("type") == "trailer"
        lead, bps, rest = split_notes(e["description"])
        num = "預告" if trailer else f"EP{e['number']:02d}"
        title = re.sub(r"^EP\d+\s*", "", e["title"])
        bp_html = ""
        if bps:
            rows = "".join(f'<li><span class="ln">{i}</span><span class="dot" aria-hidden="true"></span><span>{html.escape(t)}</span></li>'
                           for i, t in enumerate(bps, 1))
            bp_html = f'<section class="bp" aria-label="今晚的 breakpoint"><h4>今晚的 breakpoint</h4><ol>{rows}</ol></section>'
        items.append(f"""<details class="ep" id="{e['id']}">
<summary><span class="num">{num}</span><span class="t">{html.escape(title)}</span><span class="when"><time datetime="{e['published']}">{d:%Y-%m-%d}</time> · <span title="長度">{length(e['audio']['duration_s'])}</span></span></summary>
<div class="body">
<audio controls preload="none" src="audio/{feed.audio_name(e)}"></audio>
<p class="lead">{html.escape(lead)}</p>
{bp_html}
<div class="notes">{para((chr(10) * 2).join(rest))}</div>
</div>
</details>""")
    about = (chr(10) * 2).join(show["description"].split(chr(10) * 2)[1:])
    latest_num = re.match(r"EP\d+", latest["title"]).group(0) if latest else ""
    status = f"已暫停於 breakpoint · 共 {len(eps)} 集" + (f" · 最新 {latest_num}" if latest_num else "")
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>深夜 Debug</title>
<meta name="description" content="{html.escape(show['description'].split(chr(10))[0])}">
<meta name="theme-color" content="#0b0e1a">
<link rel="alternate" type="application/rss+xml" title="{html.escape(show['title'])}" href="{site}/feed.xml">
<link rel="icon" href="cover-512.jpg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{html.escape(show['title'])}">
<meta property="og:title" content="{html.escape(show['title'])}">
<meta property="og:description" content="{html.escape(show['description'].split(chr(10))[0])}">
<meta property="og:url" content="{site}/">
<meta property="og:image" content="{site}/og.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="深夜 Debug：凌晨的書桌，螢幕停在一個紅色中斷點">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{site}/og.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=LXGW+WenKai+TC:wght@400;700&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
/* Layout: a debugger paused at 2 a.m. The rain-lit banner opens the page, the episodes are collapsed frames you expand,
   and each episode's takeaways sit in a breakpoint panel. One deliberate dark theme: the show is about the night. */
:root {{
  --night:#0b0e1a; --panel:#121729; --line:#242b46; --ink:#ebe7dc; --muted:#9ba1ba;
  --lamp:#f0b45c; --bp:#e5484d; --hl:rgba(240,180,92,.13);
  --f-display:"LXGW WenKai TC", "Noto Serif TC", serif;
  --f-body:"Noto Sans TC", -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
  --f-mono:"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  color-scheme: dark;
}}
* {{ box-sizing:border-box; }}
html {{ background:var(--night); }}
body {{ margin:0; background:var(--night); color:var(--ink); font:16.5px/1.8 var(--f-body); }}
a {{ color:var(--lamp); text-underline-offset:3px; overflow-wrap:anywhere; }}
:focus-visible {{ outline:2px solid var(--lamp); outline-offset:3px; border-radius:4px; }}
.wrap {{ max-width:760px; margin:0 auto; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); }}

.hero {{ position:relative; min-height:clamp(340px, 38vw, 600px); display:flex; align-items:flex-end;
        background:linear-gradient(90deg, var(--night) 0, rgba(11,14,26,.86) 30%, rgba(11,14,26,.25) 62%, rgba(11,14,26,0) 100%),
                   linear-gradient(0deg, var(--night) 0, rgba(11,14,26,0) 35%), var(--night) url(banner.jpg) right center / cover no-repeat; }}
.hero .wrap {{ width:100%; padding-block:48px 40px; }}
.hero h1 {{ font:700 clamp(44px, 7.5vw, 84px)/1.05 var(--f-display); margin:0; letter-spacing:.01em; text-wrap:balance; }}
.hero .sub {{ font:500 15px/1.6 var(--f-mono); color:var(--muted); margin:10px 0 0; }}
.status {{ display:inline-flex; align-items:center; gap:10px; margin-top:22px; padding:6px 12px; border:1px solid var(--line);
          border-radius:999px; background:rgba(18,23,41,.7); font:500 13px/1.4 var(--f-mono); color:var(--ink); }}
.status .dot {{ background:var(--bp); box-shadow:0 0 0 4px rgba(229,72,77,.18); }}
.dot {{ width:9px; height:9px; border-radius:50%; background:var(--bp); flex:none; }}

main.wrap {{ padding-block:28px 72px; }}
.intro {{ font-size:18px; margin:0 0 20px; max-width:34em; }}
.sub-box {{ display:flex; flex-wrap:wrap; align-items:center; gap:10px 14px; padding:14px 16px; border:1px solid var(--line); border-radius:10px; background:var(--panel); }}
.sub-box .label {{ font-weight:700; }}
.sub-box code {{ font:14px/1.5 var(--f-mono); color:var(--muted); min-width:0; overflow-wrap:anywhere; flex:1 1 260px; }}
button {{ font:500 13px/1 var(--f-mono); color:var(--ink); background:transparent; border:1px solid var(--line); border-radius:6px; padding:9px 12px; cursor:pointer; }}
button:hover {{ border-color:var(--lamp); color:var(--lamp); }}

.list-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin:44px 0 8px; }}
h2 {{ font:700 26px/1.3 var(--f-display); margin:0; }}
.ep {{ border-top:1px solid var(--line); }}
.ep:last-of-type {{ border-bottom:1px solid var(--line); }}
.ep summary {{ list-style:none; cursor:pointer; display:grid; grid-template-columns:4.2em 1fr auto 1.2em; align-items:baseline; gap:4px 14px; padding:16px 4px; }}
.ep summary::-webkit-details-marker {{ display:none; }}
.ep summary::after {{ content:"›"; color:var(--muted); font:400 20px/1 var(--f-mono); justify-self:end; transition:transform .2s ease; }}
.ep[open] summary::after {{ transform:rotate(90deg); color:var(--lamp); }}
.ep summary:hover .t {{ color:var(--lamp); }}
.num {{ font:500 13px/1.4 var(--f-mono); color:var(--lamp); letter-spacing:.04em; }}
.t {{ font:700 19px/1.45 var(--f-display); min-width:0; text-wrap:balance; }}
.when {{ font:13px/1.4 var(--f-mono); color:var(--muted); white-space:nowrap; font-variant-numeric:tabular-nums; }}
.ep .body {{ padding:0 4px 26px calc(4.2em + 18px); }}
.ep audio {{ width:100%; margin:4px 0 6px; }}
.lead {{ margin:8px 0 16px; }}
.bp {{ border:1px solid var(--line); border-radius:8px; background:var(--panel); overflow:hidden; margin:0 0 16px; }}
.bp h4 {{ margin:0; padding:8px 14px; font:500 12.5px/1.4 var(--f-mono); color:var(--muted); letter-spacing:.06em; border-bottom:1px solid var(--line); }}
.bp ol {{ list-style:none; margin:0; padding:6px 0; }}
.bp li {{ display:grid; grid-template-columns:2.2em 12px 1fr; align-items:baseline; gap:10px; padding:6px 14px 6px 0; }}
.bp li:first-child {{ background:var(--hl); }}
.bp .ln {{ font:13px/1 var(--f-mono); color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; }}
.bp .dot {{ transform:translateY(-1px); }}
.notes p {{ margin:0 0 10px; color:var(--muted); font-size:15px; }}
.about {{ margin-top:48px; }}
.about p {{ max-width:36em; }}
footer {{ margin-top:40px; padding-top:16px; border-top:1px solid var(--line); color:var(--muted); font-size:14px; }}

@media (max-width: 640px) {{
  .hero {{ background:linear-gradient(0deg, var(--night) 0, rgba(11,14,26,.78) 45%, rgba(11,14,26,.35) 100%), var(--night) url(banner.jpg) 78% center / cover no-repeat; }}
  .ep summary {{ grid-template-columns:1fr 1.2em; }}
  .ep summary .num {{ grid-column:1; }}
  .ep summary .t {{ grid-column:1; }}
  .ep summary .when {{ grid-column:1; }}
  .ep summary::after {{ grid-column:2; grid-row:1 / span 3; align-self:center; }}
  .ep .body {{ padding-left:4px; }}
}}
@media (prefers-reduced-motion: reduce) {{ .ep summary::after {{ transition:none; }} }}
</style>
</head>
<body>
<header class="hero"><div class="wrap">
<h1>深夜 Debug</h1>
<p class="sub">Debug After Dark · 主持人 {html.escape(show['host'])}</p>
<p class="status"><span class="dot" aria-hidden="true"></span>{html.escape(status)}</p>
</div></header>
<main class="wrap">
<p class="intro">{html.escape(show['description'].split(chr(10))[0])}</p>
<div class="sub-box"><span class="label">訂閱</span><code id="feed-url">{site}/feed.xml</code><button type="button" id="copy-feed">複製網址</button></div>
<div class="list-head"><h2>每一集</h2><button type="button" id="toggle-all" aria-pressed="false">全部展開</button></div>
{''.join(items)}
<section class="about"><h2>關於節目</h2>{para(about)}</section>
<footer><p>本節目的聲音由 AI 語音合成，不模仿任何真人；內容改寫自 <a href="https://imitator.ai-apps.work/">imitator</a> 上的文章，每一集都經過真人審稿與試聽。Apple Podcasts、Spotify 上架中，先用上面的網址訂閱。</p></footer>
</main>
<script>
(function () {{
  var copy = document.getElementById("copy-feed"), url = document.getElementById("feed-url");
  copy.addEventListener("click", function () {{
    var done = function () {{ copy.textContent = "已複製"; setTimeout(function () {{ copy.textContent = "複製網址"; }}, 1600); }};
    var select = function () {{ var r = document.createRange(); r.selectNodeContents(url); var s = getSelection(); s.removeAllRanges(); s.addRange(r); copy.textContent = "已選取，按 Ctrl+C"; }};
    if (navigator.clipboard) navigator.clipboard.writeText(url.textContent).then(done, select); else select();
  }});
  var toggle = document.getElementById("toggle-all"), eps = document.querySelectorAll("details.ep");
  toggle.addEventListener("click", function () {{
    var open = toggle.getAttribute("aria-pressed") !== "true";
    eps.forEach(function (d) {{ d.open = open; }});
    toggle.setAttribute("aria-pressed", String(open)); toggle.textContent = open ? "全部收起" : "全部展開";
  }});
  if (location.hash) {{ var d = document.getElementById(location.hash.slice(1)); if (d && d.tagName === "DETAILS") d.open = true; }}
}})();
</script>
</body>
</html>
"""


def main(out):
    show, eps = feed.load(ROOT / "show" / "show.json"), feed.final_episodes()
    problems = []
    for e in eps:
        mp3 = e["_dir"] / e["audio"]["file"]
        if not mp3.exists():
            problems.append(f"{e['id']}: {mp3} missing"); continue
        data = mp3.read_bytes()
        if len(data) != e["audio"].get("bytes") or hashlib.sha256(data).hexdigest() != e["audio"].get("sha256"):
            problems.append(f"{e['id']}: mp3 does not match episode.json (rerun tools/package_episode.py)")
    if problems:
        sys.exit("\n".join(problems))
    out = Path(out); shutil.rmtree(out, ignore_errors=True); (out / "audio").mkdir(parents=True)
    for e in eps:
        shutil.copyfile(e["_dir"] / e["audio"]["file"], out / "audio" / feed.audio_name(e))
    shutil.copyfile(ROOT / show["cover"], out / "cover.jpg")
    shutil.copyfile(ROOT / show["banner"], out / "banner.jpg")
    shutil.copyfile(ROOT / "show" / "og" / "og-1200x630.jpg", out / "og.jpg")   # link previews, tools/make_og.py
    shutil.copyfile(ROOT / "show" / "art" / "cover-512.jpg", out / "cover-512.jpg")
    (out / "feed.xml").write_text(feed.build(show, eps), encoding="utf-8")
    (out / "index.html").write_text(page(show, eps), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    if show.get("custom_domain"):
        (out / "CNAME").write_text(show["custom_domain"] + "\n")
    for m in feed.warnings(show, eps):
        print("warning:", m, file=sys.stderr)
    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"{out}: {len(eps)} episodes, {total / 1e6:.1f} MB (GitHub Pages limit 1 GB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT / "site")); main(ap.parse_args().out)
