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


def page(show, eps):
    site = show["site_url"].rstrip("/")
    items = []
    for e in eps:
        d = datetime.fromisoformat(e["published"])
        items.append(f"""<article class="ep">
<h3>{html.escape(e['title'])}</h3>
<p class="meta">{d:%Y-%m-%d} · {e['audio']['duration']}{' · 預告' if e.get('type') == 'trailer' else ''}</p>
<audio controls preload="none" src="audio/{feed.audio_name(e)}"></audio>
{para(e['description'])}
</article>""")
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(show['title'])}</title>
<meta name="description" content="{html.escape(show['description'].split(chr(10))[0])}">
<link rel="alternate" type="application/rss+xml" title="{html.escape(show['title'])}" href="{site}/feed.xml">
<link rel="icon" href="cover-512.jpg">
<style>
:root {{ --bg:#0d1020; --panel:#151a30; --ink:#ecebe4; --muted:#a6acc4; --accent:#f2b45a; --red:#e5484d; --line:#262d4a; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg:#f5f3ee; --panel:#ffffff; --ink:#1b1e2e; --muted:#5b6078; --accent:#a0620f; --red:#c8313a; --line:#e2ded3; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:17px/1.75 -apple-system, "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif; }}
a {{ color:var(--accent); word-break:break-all; }}
.hero {{ color:#ecebe4; background:linear-gradient(90deg, rgba(13,16,32,.95) 0, rgba(13,16,32,.8) 45%, rgba(13,16,32,.15) 100%), #0d1020 url(banner-1920.jpg) right center / cover no-repeat; }}
.hero .in {{ max-width:760px; margin:0 auto; padding:88px 16px 80px; }}
@media (max-width: 600px) {{ .hero {{ background:linear-gradient(rgba(13,16,32,.55), rgba(13,16,32,.85)), #0d1020 url(banner-1920.jpg) 80% center / cover no-repeat; }} .hero .in {{ padding:64px 16px 56px; }} }}
.hero h1 {{ font-size:clamp(34px, 6vw, 56px); line-height:1.15; margin:0 0 8px; }}
.hero p {{ margin:0; color:#c9cde0; max-width:34em; }}
.dot {{ display:inline-block; width:.5em; height:.5em; border-radius:50%; background:var(--red); margin-right:.35em; vertical-align:.15em; }}
main {{ max-width:760px; margin:0 auto; padding:24px 16px 64px; }}
.sub {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 20px; margin:8px 0 32px; }}
.sub code {{ font-size:15px; word-break:break-all; }}
.ep {{ border-top:1px solid var(--line); padding:24px 0; }}
.ep h3 {{ margin:0; font-size:21px; line-height:1.4; }}
.meta {{ color:var(--muted); margin:4px 0 12px; font-size:15px; }}
audio {{ width:100%; margin:4px 0 8px; }}
footer {{ color:var(--muted); font-size:14px; border-top:1px solid var(--line); padding-top:16px; }}
</style>
</head>
<body>
<header class="hero"><div class="in">
<h1><span class="dot"></span>{html.escape(show['title'].split('｜')[0])}</h1>
<p>{html.escape(show['title'].split('｜')[-1])} · 主持人 {html.escape(show['host'])}</p>
</div></header>
<main>
{para(show['description'].split(chr(10)+chr(10))[0])}
<div class="sub"><strong>訂閱</strong>：把這個網址貼進你的 podcast app（Apple Podcasts、Spotify 等平台上架中）<br><code>{site}/feed.xml</code></div>
<h2>每一集</h2>
{''.join(items)}
<h2>關於節目</h2>
{para(chr(10).join(['']) + (chr(10)+chr(10)).join(show['description'].split(chr(10)+chr(10))[1:]))}
<footer><p>本節目的聲音由 AI 語音合成，不模仿任何真人；內容改寫自 <a href="https://imitator.ai-apps.work/">imitator</a> 上的文章，每一集都經過真人審稿與試聽。</p></footer>
</main>
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
    for name in ("cover-512.jpg", "banner-1920.jpg"):
        src = ROOT / "show" / "art" / name
        if src.exists(): shutil.copyfile(src, out / name)
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
