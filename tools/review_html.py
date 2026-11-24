#!/usr/bin/env python3
"""試聽稿套版：把 episodes/epNN/epNN-review.md 轉成同一個版型的 epNN-review.html，上面一個播放器，
稿子裡的時間（0:36、2:00 前後、說明欄的 00:43）都可以點，點了就跳到那裡播。

不花 token：只用 Python 標準函式庫，固定版型，Claude 不用手寫 HTML。

用法：
    python3 tools/review_html.py /mnt/project-files/episodes/ep52/ep52-review.md
    python3 tools/review_html.py /mnt/project-files/episodes/ep5*/ep*-review.md   # 一次轉好幾集

mp3 找同一個資料夾裡的 .mp3（只有一個時），播放器用相對路徑接上。
在工廠儀表板裡打開時，頁面在沒有權限的框裡讀不到 mp3，改由儀表板放播放器：
點時間會送 {type: "review-seek", t: 秒} 給上一層（window.parent）。
"""
import html
import re
import sys
from pathlib import Path

TIME_RE = re.compile(r"(?<![\d:.])(\d{1,2}):([0-5]\d)(?![\d:])")
# 這些是時鐘時間，不是音檔裡的位置：「2026-11-27 08:00 台北」「長度 8:32」
SKIP_BEFORE = re.compile(r"(\d{4}-\d\d-\d\d\s*|長度\s*|\d{1,2}/\d{1,2}[^\s]*\s*)$")
SKIP_AFTER = re.compile(r"^\s*(台北|前上架|上架)")


def seconds(m):
    return int(m.group(1)) * 60 + int(m.group(2))


CLOCK_LINE = re.compile(r"^\s*(排程|上架|排定)")   # 講上架時刻的行，裡面的時間都是時鐘


def inline(text):
    """一行文字：先跳脫，再處理粗體、行內程式碼、連結、時間。"""
    clock = bool(CLOCK_LINE.match(text))
    out, last = [], 0
    # 連結先挖出來，免得網址裡的冒號被當成時間
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)\)|(https?://[^\s）)，。]+)", text):
        out.append(("t", text[last:m.start()]))
        if m.group(3):
            out.append(("a", m.group(3), m.group(3)))
        else:
            out.append(("a", m.group(1), m.group(2)))
        last = m.end()
    out.append(("t", text[last:]))
    res = []
    for part in out:
        if part[0] == "a":
            res.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(part[2]), html.escape(part[1])))
            continue
        s = part[1]
        pieces, pos = [], 0
        for m in TIME_RE.finditer(s):
            if clock or SKIP_BEFORE.search(s[:m.start()]) or SKIP_AFTER.match(s[m.end():]):
                continue
            pieces.append(fmt(s[pos:m.start()]))
            pieces.append('<button type="button" class="ts" data-t="%d">%s</button>' % (seconds(m), m.group(0)))
            pos = m.end()
        pieces.append(fmt(s[pos:]))
        res.append("".join(pieces))
    return "".join(res)


def fmt(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_to_html(md):
    lines = md.replace("\r", "").split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush(); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            flush()
            n = min(len(m.group(1)) + 1, 4) if len(m.group(1)) > 1 else 1
            out.append("<h%d>%s</h%d>" % (n, inline(m.group(2)), n)); i += 1; continue
        if line.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith("|"):
                c = cells(lines[i])
                if not all(re.fullmatch(r":?-+:?", x) for x in c):
                    rows.append(c)
                i += 1
            if rows:
                head = "".join("<th>%s</th>" % inline(x) for x in rows[0])
                body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(x) for x in r) for r in rows[1:])
                out.append('<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body))
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            flush(); ordered = bool(re.match(r"^\s*\d+\.", line)); items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append("<li>%s</li>" % inline(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))); i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag)); continue
        if line.startswith(">"):
            flush(); q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(re.sub(r"^>\s?", "", lines[i])); i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(q))); continue
        if line.startswith("```"):
            flush(); code = []; i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            out.append("<pre>%s</pre>" % "\n".join(inline(c) for c in code)); continue
        if re.fullmatch(r"\s*(-{3,}|\*{3,})\s*", line):
            flush(); out.append("<hr>"); i += 1; continue
        # 「說明欄」的章節：一行一個「00:43 標題」，各自成一行
        if TIME_RE.match(line.strip()) and line.strip()[:5].count(":") == 1:
            flush(); out.append('<p class="chap">%s</p>' % inline(line.strip())); i += 1; continue
        # 逐段稿：「**s00_open**　內容」段落標記獨立出來
        m = re.match(r"^\*\*(s\d+[\w-]*)\*\*\s*(.*)", line.strip())
        if m:
            flush(); out.append('<p class="seg"><span class="sid">%s</span>%s</p>' % (html.escape(m.group(1)), inline(m.group(2)))); i += 1; continue
        para.append(line.strip()); i += 1
    flush()
    return "\n".join(out)


PAGE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#f5f5f1;--card:#fff;--ink:#1d1d1b;--ink2:#55544f;--line:#e4e2dc;--accent:#2f5fd0;--chip:#efeee9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--ink2:#b5b3ac;--line:#33322f;--accent:#8fb0ff;--chip:#2a2a27}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 system-ui,-apple-system,"Noto Sans TC","PingFang TC",sans-serif}}
.bar{{position:sticky;top:0;z-index:2;background:var(--card);border-bottom:1px solid var(--line);padding:8px 16px}}
.bar audio{{width:100%;display:block}}
.bar .hint{{font-size:13px;color:var(--ink2)}}
main{{max-width:760px;margin:0 auto;padding:12px 16px 60px}}
h1{{font-size:21px;line-height:1.4;margin:12px 0}}h2{{font-size:18px;margin:28px 0 8px;padding-top:8px;border-top:1px solid var(--line)}}h3{{font-size:16px}}
a{{color:var(--accent)}}
code{{background:var(--chip);padding:0 4px;border-radius:4px;font-size:.92em}}
blockquote{{margin:8px 0;padding-left:12px;border-left:3px solid var(--line);color:var(--ink2)}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;font-size:14px}}th,td{{border-top:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}}
button.ts{{font:inherit;font-variant-numeric:tabular-nums;color:var(--accent);background:var(--chip);border:0;border-radius:6px;padding:0 6px;margin:0 1px;cursor:pointer}}
button.ts:hover,button.ts:focus-visible{{outline:2px solid var(--accent)}}
p.chap{{margin:2px 0}}
p.seg{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}}
.sid{{display:inline-block;font-size:12px;font-weight:600;color:var(--ink2);background:var(--chip);border-radius:999px;padding:0 8px;margin-right:6px}}
</style></head><body>
<div class="bar" id="bar">{player}</div>
<main>
{body}
</main>
<script>
(function(){{
  var a = document.getElementById("player");
  var embedded = window.parent !== window;
  // 在儀表板的框裡讀不到 mp3：播放器收起來，交給儀表板
  var drop = function(){{ var bar = document.getElementById("bar"); if(bar) bar.parentNode.removeChild(bar); a = null; }};
  if(a) a.addEventListener("error", function(){{ if(embedded) drop(); }});
  if(embedded && a && a.networkState === 3) drop();
  document.addEventListener("click", function(ev){{
    var b = ev.target.closest && ev.target.closest("button.ts"); if(!b) return;
    var t = Number(b.getAttribute("data-t"));
    if(a && a.readyState > 0){{ a.currentTime = t; a.play(); }}
    else if(embedded) window.parent.postMessage({{type: "review-seek", t: t}}, "*");
  }});
}})();
</script>
</body></html>
"""


def build(md_path):
    md_path = Path(md_path)
    md = md_path.read_text(encoding="utf-8")
    m = re.search(r"^#\s+(.+)$", md, re.M)
    title = m.group(1).strip() if m else md_path.stem
    mp3s = sorted(md_path.parent.glob("*.mp3"))
    if len(mp3s) == 1:
        player = ('<audio id="player" controls preload="metadata" src="%s"></audio>'
                  '<div class="hint">點稿子裡的時間就會跳到那裡播</div>') % html.escape(mp3s[0].name)
    else:
        player = '<div class="hint">這個資料夾%s，沒接播放器</div>' % ("沒有 mp3" if not mp3s else "有好幾個 mp3")
    out = md_path.with_suffix(".html")
    out.write_text(PAGE.format(title=html.escape(title), player=player, body=md_to_html(md)), encoding="utf-8")
    return out, len(mp3s) == 1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        out, ok = build(p)
        print("寫好 %s%s" % (out, "" if ok else "（沒接播放器）"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
