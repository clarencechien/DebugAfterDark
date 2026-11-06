"""Build the podcast RSS feed from show/show.json and episodes/*/episode.json (standard library only).

  python3 tools/feed.py [--out site/feed.xml]

Only episodes with "status": "final" and a "published" timestamp go in, newest first. The output is deterministic:
the same inputs give a byte-identical feed (lastBuildDate is the newest pubDate, not the build time).
Audio URLs carry the first 8 hex digits of the file's sha256 (<id>-<sha8>.mp3), so a re-cut episode gets a new URL and
podcast apps never keep a stale cached copy; the episode guid never changes (PIPELINE.md section 5.2).
show.json "enclosure_prefix" (optional) is prepended to every enclosure URL for download analytics (SoundOn Prefix).
Covers Apple's required tags (RSS 2.0, itunes namespace, title, description, itunes:image, language, itunes:category,
itunes:explicit; per item title, enclosure with length and type, guid, pubDate) plus podcast:guid, and podcast:locked
once an owner email is set. Requirements change; check https://podcasters.apple.com/support/823-podcast-requirements.
"""
import argparse, json, re, sys, uuid
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
PODCAST_NS_UUID = uuid.UUID("ead4c236-bf58-58c6-a2c6-a6b28d128cb6")   # Podcasting 2.0 podcast:guid namespace


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def final_episodes():
    eps = []
    for p in sorted((ROOT / "episodes").glob("*/episode.json")):
        e = load(p)
        if e.get("status") == "final" and e.get("published"):
            e["_dir"] = p.parent; eps.append(e)
    return sorted(eps, key=lambda e: e["published"], reverse=True)


def audio_name(e):
    return f"{e['id']}-{e['audio']['sha256'][:8]}.mp3"


def text(s):
    return escape(s, {'"': "&quot;", "'": "&apos;"})


def notes_html(s):
    """Show notes (plain text, blank-line paragraphs) -> the small HTML subset Apple and Spotify render: <p>, <br>,
    <ol>/<li>, <a>. Plain newlines collapse to spaces in their players, so every note ran together (2026-11-06);
    SoundOn showed them right only because it keeps raw newlines. The breakpoint block becomes a numbered list."""
    link = lambda t: re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', escape(t))
    out = []
    for block in [b.strip() for b in s.strip().split("\n\n") if b.strip()]:
        lines = block.split("\n")
        items = [re.sub(r"^\d+\.\s*", "", l).strip() for l in lines[1:]]
        if len(lines) > 1 and all(re.match(r"^\d+\.\s", l) for l in lines[1:]):
            out.append(f"<p>{link(lines[0])}</p><ol>" + "".join(f"<li>{link(i)}</li>" for i in items) + "</ol>")
        else:
            out.append("<p>" + "<br>".join(link(l) for l in lines) + "</p>")
    return "".join(out)


def cdata(html_text):
    return "<![CDATA[" + html_text.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def with_support(show, text):
    """Append the support link (show.json support_url) so every app that reads the feed shows it (Apple, Spotify, SoundOn)."""
    return f"{text}\n\n{show['support_text']}：{show['support_url']}" if show.get("support_url") else text


def build(show, eps):
    site = show["site_url"].rstrip("/"); feed_url = f"{site}/feed.xml"
    guid = uuid.uuid5(PODCAST_NS_UUID, feed_url.split("://", 1)[1].rstrip("/"))
    newest = max((datetime.fromisoformat(e["published"]) for e in eps), default=None)
    yes_no = lambda b: "true" if b else "false"
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom"'
         ' xmlns:podcast="https://podcastindex.org/namespace/1.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:imitator="https://imitator.ai-apps.work/ns/podcast">',
         "<channel>",
         f"<title>{text(show['title'])}</title>",
         f"<link>{text(site)}/</link>",
         f'<atom:link href="{text(feed_url)}" rel="self" type="application/rss+xml"/>',
         f"<description>{cdata(notes_html(with_support(show, show['description'])))}</description>",
         f"<language>{text(show['language'])}</language>",
         f"<copyright>{text(show['copyright'])}</copyright>",
         f"<itunes:author>{text(show['author'])}</itunes:author>",
         f'<itunes:image href="{text(site)}/cover.jpg"/>',
         f"<image><url>{text(site)}/cover.jpg</url><title>{text(show['title'])}</title><link>{text(site)}/</link></image>",
         f'<itunes:category text="{text(show["category"])}"/>',
         f"<itunes:explicit>{yes_no(show['explicit'])}</itunes:explicit>",
         f"<itunes:type>{text(show['type'])}</itunes:type>",
         f"<podcast:guid>{guid}</podcast:guid>"]
    if show.get("owner_email"):
        L += [f"<itunes:owner><itunes:name>{text(show['owner_name'])}</itunes:name><itunes:email>{text(show['owner_email'])}</itunes:email></itunes:owner>",
              f'<podcast:locked owner="{text(show["owner_email"])}">yes</podcast:locked>']
    if newest:
        L.append(f"<lastBuildDate>{format_datetime(newest)}</lastBuildDate>")
    for e in eps:
        a = e["audio"]; url = f"{site}/audio/{audio_name(e)}"
        if show.get("enclosure_prefix"):
            # Analytics prefix (SoundOn): the app requests prefix + host/path, the service logs it and 302s to our file.
            # Only the feed carries it; the site's own players use the direct URL so page plays are not counted.
            url = show["enclosure_prefix"].rstrip("/") + "/" + url.split("://", 1)[1]
        L += ["<item>",
              f"<title>{text(e['title'])}</title>",
              f"<description>{cdata(notes_html(with_support(show, e['description'])))}</description>",
              f"<content:encoded>{cdata(notes_html(with_support(show, e['description'])))}</content:encoded>",
              f'<enclosure url="{text(url)}" length="{a["bytes"]}" type="audio/mpeg"/>',
              f'<guid isPermaLink="false">{text(e["guid"])}</guid>',
              f"<pubDate>{format_datetime(datetime.fromisoformat(e['published']))}</pubDate>",
              f"<itunes:duration>{int(round(a['duration_s']))}</itunes:duration>",
              f"<itunes:episodeType>{'trailer' if e.get('type') == 'trailer' else 'full'}</itunes:episodeType>",
              f"<itunes:explicit>{yes_no(show['explicit'])}</itunes:explicit>"]
        if e.get("type") != "trailer":
            L.append(f"<itunes:episode>{e['number']}</itunes:episode>")
        if e.get("source_url"):
            L.append(f"<link>{text(e['source_url'])}</link>")
        if e.get("report_slug"):
            L.append(f"<imitator:report>{text(e['report_slug'])}</imitator:report>")
        L.append("</item>")
    L += ["</channel>", "</rss>", ""]
    return "\n".join(L)


def warnings(show, eps):
    w = []
    if not show.get("owner_email"):
        w.append("show.owner_email is empty: no itunes:owner (Spotify sends its claim code there) and no podcast:locked")
    if not eps:
        w.append("no final episodes with a published timestamp")
    now = datetime.now().astimezone()
    for e in eps:
        if datetime.fromisoformat(e["published"]) > now:   # apps treat future pubDates as scheduled and may hide the episode
            w.append(f"{e['id']}: published {e['published']} is in the future")
        desc = e.get("description", "")
        need = ["回 Ping 一個 pong", "AI 語音合成"] + ([] if e.get("type") == "trailer" else ["今晚的 breakpoint", "原文："])
        for n in need:   # show-notes template: episodes/ep00-intro/script.md (EP01's POC-era notes lacked these, 2026-11-04)
            if n not in desc:
                w.append(f"{e['id']}: description is missing 「{n}」 (show-notes template)")
        for k in ("bytes", "sha256", "duration_s"):
            if k not in e["audio"]:
                w.append(f"{e['id']}: audio.{k} missing, run tools/package_episode.py")
    return w


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT / "site" / "feed.xml")); a = ap.parse_args()
    show, eps = load(ROOT / "show" / "show.json"), final_episodes()
    xml = build(show, eps); ET.fromstring(xml.encode("utf-8"))           # must be well-formed
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(xml, encoding="utf-8")
    for m in warnings(show, eps):
        print("warning:", m, file=sys.stderr)
    print(f"{a.out}: {len(eps)} episodes")
