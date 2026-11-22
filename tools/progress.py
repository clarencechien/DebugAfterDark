#!/usr/bin/env python3
"""製作進度：從每集自己的檔案彙整「製作中」與「已做」兩張表。

為什麼：兩集同時開工時，兩個 PR 都在共用檔（docs/report-candidates.md、voices/drift.json）
同一個位置加一行，後合的那個一定衝突。現在每集只寫自己資料夾裡的檔案，表格由這支腳本現算：

  episodes/<ep>/episode.json   集數、標題、報告、status、published、audio（feed 本來就要的）
  episodes/<ep>/progress.json  只放推不出來的欄位（選填）：
      {"review": "✅ 11/22",        # 試聽、定稿；沒寫時 final → ✅，否則 ⬜
       "video": "⬜", "short": "⬜",  # 影片版、Short
       "note": "一句備註",
       "done": false,               # true：不再列在「製作中」
       "also_reports": ["slug", …]} # 同一集還用了哪些報告（EP24–26）
  「音檔」看 audio.sha256，「進 feed」看 status 與 published（⏰ 排程／✅ 已上架），都可以在 progress.json 用
  "audio"、"feed" 覆寫。

「製作中」= 有 progress.json 而且 done 不是 true，或 status 還不是 final 的集數。

  python3 tools/progress.py            # 製作中（Markdown 表）
  python3 tools/progress.py --done     # 已做（依集數）
  python3 tools/progress.py --json     # 兩張表的資料（yt_report 用）
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPE = dt.timezone(dt.timedelta(hours=8))
REPORT_URL = "https://imitator.ai-apps.work/r/{}"

ACTIVE_HEAD = ["集數", "報告", "音檔（第 1–8 步）", "試聽、定稿", "進 feed", "影片版（第 9 步）", "Short", "備註"]
DONE_HEAD = ["集數", "節目標題", "報告", "狀態"]


def load(root=ROOT):
    """每集一筆：(資料夾名, episode.json, progress.json 或 {})，依集數排。"""
    eps = []
    for p in sorted((root / "episodes").glob("*/episode.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        pp = p.parent / "progress.json"
        prog = json.loads(pp.read_text(encoding="utf-8")) if pp.exists() else {}
        eps.append((p.parent.name, m, prog))
    eps.sort(key=lambda e: (e[1].get("number") is None, e[1].get("number") or 0, e[0]))
    return eps


def _published(m):
    s = m.get("published")
    return dt.datetime.fromisoformat(s).astimezone(TPE) if s else None


def _link(slug):
    slug = slug.replace("_", "-")   # imitator 把檔名的底線換成連字號
    return f"[`{slug}`]({REPORT_URL.format(slug)})"


def _reports(m, prog):
    slugs = [s for s in [m.get("report_slug")] + list(prog.get("also_reports", [])) if s]
    return "、".join(_link(s) for s in slugs) or "—"


def feed_cell(m, now):
    pub = _published(m)
    if m.get("status") != "final" or not pub:
        return "⬜"
    if pub > now:
        return f"⏰ {pub:%m/%d %H:%M} 排程"
    return f"✅ {pub:%m/%d}"


def active_rows(eps, now):
    rows = []
    for name, m, prog in eps:
        final = m.get("status") == "final"
        if prog.get("done") or (final and not prog):
            continue
        audio = prog.get("audio") or ("✅" if (m.get("audio") or {}).get("sha256") else "🔶")
        rows.append([f"EP{m.get('number', 0):02d}", _reports(m, prog), audio,
                     prog.get("review") or ("✅" if final else "⬜"), prog.get("feed") or feed_cell(m, now),
                     prog.get("video", "⬜"), prog.get("short", "⬜"), prog.get("note", "")])
    return rows


def done_rows(eps, now):
    rows = []
    for name, m, prog in eps:
        pub = _published(m)
        if m.get("status") != "final" or not pub:
            continue
        num = f"EP{m.get('number', 0):02d}"
        title = m.get("title", "")
        if title.startswith(num + " "):
            title = title[len(num) + 1:]
        title = title.removesuffix("｜" + num)   # EP01–23 改過的 YouTube 式標題把集數放在最後
        rows.append([num, title, _reports(m, prog), "上架" if pub <= now else f"排程 {pub:%m/%d}"])
    return rows


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(c.replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def tables(root=ROOT, now=None):
    now = now or dt.datetime.now(TPE)
    eps = load(root)
    return {"active": (ACTIVE_HEAD, active_rows(eps, now)), "done": (DONE_HEAD, done_rows(eps, now))}


if __name__ == "__main__":
    t = tables()
    if "--json" in sys.argv:
        print(json.dumps({k: {"head": h, "rows": r} for k, (h, r) in t.items()}, ensure_ascii=False, indent=1))
    elif "--done" in sys.argv:
        h, r = t["done"]
        print(md_table(h, r) + f"\n\n已做 {len(r)} 集（含排程）。")
    else:
        h, r = t["active"]
        print(md_table(h, r) + f"\n\n製作中 {len(r)} 集。✅ 完成、🔶 進行中、⬜ 還沒做、⏰ 已排程。")
