#!/usr/bin/env python3
"""工廠儀表板的 repo 區塊：把 main 上的現況算成一份 JSON，寫進專案資料夾給儀表板 Artifact 讀。

儀表板是專案裡的 Artifact（只有專案成員看得到），它打開時直接讀專案資料夾：
  factory/repo.json            這支腳本寫的：上架排程、製作中、下一批（推薦表）、重製池、實驗、待辦、開著的 PR
  research/                    自動研究的題庫、每週的稿、cost.log（Artifact 自己解析，永遠是最新的）
  yt-report/summary.json       每週 YouTube 報表的摘要（Artifact 只取自然流量的數字）

Artifact 讀不到 GitHub，所以 repo 的現況要有人寫進來：每集 thread 開 PR、合併後，或任何改了 main 的 thread，
最後跑一次就好（只用標準函式庫，不呼叫 LLM，幾秒鐘）：

  python3 tools/factory_status.py              # 讀 origin/main，寫 /mnt/project-files/factory/repo.json
  python3 tools/factory_status.py --print      # 只印出，不寫
  python3 tools/factory_status.py --worktree   # 讀目前的工作目錄（測試用；分支上還沒合併的集數也會算進去）

預設先 `git fetch origin main` 再讀 origin/main，所以在哪個分支上跑都一樣，還沒合併的集數不會被當成已排程。
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import progress  # noqa: E402  同一份「製作中」邏輯，跟 progress.py、yt_report 一致

TPE = dt.timezone(dt.timedelta(hours=8))
REPO = "clarencechien/debugafterdark"
OUT = "/mnt/project-files/factory/repo.json"
SCHEDULE_PAST_DAYS = 8   # 也列最近 8 天已上架的（儀表板「上線 7 天內」那格用）
PATHS = [":(glob)episodes/*/episode.json", ":(glob)episodes/*/progress.json", "docs", "youtube"]


def now_iso():
    return dt.datetime.now(TPE).isoformat(timespec="seconds")


def md_table_after(md, heading_re):
    """`heading_re` 標題底下第一張 Markdown 表 → (表頭, 列, 該節內文)。標題層級不限；heading_re 不要用跨行的 .*。"""
    m = re.search(rf"^#+ {heading_re}\s*$(.*?)(?=^#+ |\Z)", md, re.M | re.S)
    if not m:
        return [], [], ""
    body, lines = m.group(1), []
    for line in body.splitlines():
        if line.startswith("|"):
            lines.append(line)
        elif lines:
            break
    rows = [[c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))] for line in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    return (rows[0] if rows else []), rows[1:], body


def links(cell):
    """儲存格裡的 Markdown 連結 → [{text, url}]。"""
    return [{"text": t.strip("`* "), "url": u} for t, u in re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", cell)]


def plain(cell):
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell)
    s = re.sub(r"<br\s*/?>", "；", s)
    return re.sub(r"[`*]", "", s).strip()


def episodes(root, now):
    eps = progress.load(root)
    active = {r[0] for r in progress.active_rows(eps, now)}
    out = []
    for name, m, prog in eps:
        num = m.get("number")
        if num is None:
            continue
        ep = f"EP{num:02d}"
        pub = progress._published(m)
        recent = pub and m.get("status") == "final" and pub >= now - dt.timedelta(days=SCHEDULE_PAST_DAYS)
        if ep not in active and not recent:
            continue
        title = m.get("title", "")
        if title.startswith(ep + " "):
            title = title[len(ep) + 1:]
        out.append({
            "ep": ep, "title": title.removesuffix("｜" + ep),
            "report": (m.get("report_slug") or "").replace("_", "-"),
            "status": m.get("status", ""), "published": pub.isoformat() if pub else None,
            "audio": bool((m.get("audio") or {}).get("sha256")),
            "review": prog.get("review") or ("✅" if m.get("status") == "final" else "⬜"),
            "video": prog.get("video", "⬜"), "short": prog.get("short", "⬜"),
            "note": prog.get("note", ""), "active": ep in active,
        })
    return out


def next_batch(root, made):
    """docs/report-candidates.md 的推薦表：還沒開工的列，附預排集數（「#n → EPxx」）。"""
    md = (root / "docs" / "report-candidates.md").read_text(encoding="utf-8")
    head, rows, body = md_table_after(md, re.escape("推薦的下一批"))
    plan = {}
    for a, b, e1, _ in re.findall(r"#(\d+)(?:–(\d+))?\s*→\s*EP(\d+)(?:–EP(\d+))?", body):
        for k, n in enumerate(range(int(a), int(b or a) + 1)):
            plan[n] = int(e1) + k
    out = []
    for r in rows:
        if not r or not r[0].isdigit():
            continue
        col = dict(zip(head, r))
        ln = links(col.get("報告", ""))
        slug = re.search(r"/r/([\w-]+)", ln[0]["url"]).group(1) if ln else ""
        if slug in made:
            continue
        n = int(r[0])
        out.append({"n": n, "ep": f"EP{plan[n]}" if n in plan else None, "kind": plain(col.get("類別", "")),
                    "report": ln[0] if ln else None, "angle": plain(col.get("標題方向", "")),
                    "time": plain(col.get("製作時間（估）", ""))})
    return out


def remake_pool(root):
    """docs/remake-candidates.md 的「首選」兩張表（AI／硬、錢）。"""
    path = root / "docs" / "remake-candidates.md"
    if not path.exists():
        return []
    md = path.read_text(encoding="utf-8")
    out = []
    for heading in (r"首選：AI 與硬題目[^\n]*", r"首選：錢[^\n]*"):
        head, rows, _ = md_table_after(md, heading)
        for r in rows:
            col = dict(zip(head, r))
            out.append({"n": plain(col.get("#", "")), "kind": plain(col.get("類別", "")),
                        "angle": plain(col.get("標題方向", "")), "sources": links(col.get("原報告", ""))[:3]})
    return out


def open_prs():
    """公開 repo，不用 token；抓不到就回 None（儀表板顯示「這次沒抓到」），不讓整支失敗。"""
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/pulls?state=open&per_page=50",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "factory-status"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            prs = json.load(r)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"PR 清單抓不到（{e}），這次不放", file=sys.stderr)
        return None
    return [{"n": p["number"], "title": p["title"], "url": p["html_url"], "draft": p.get("draft", False),
             "branch": p["head"]["ref"], "updated": p["updated_at"]} for p in prs]


def load_json(root, rel, key):
    p = root / rel
    return json.loads(p.read_text(encoding="utf-8")).get(key, []) if p.exists() else []


def repo_section(root, source, with_prs=True):
    now = dt.datetime.now(TPE)
    all_eps = progress.load(root)
    made = {(m.get("report_slug") or "").replace("_", "-") for _, m, _ in all_eps}
    for _, _, prog in all_eps:
        made.update(prog.get("also_reports", []))
    exps = [{k: x.get(k) for k in ("id", "name", "status", "change_date", "next_review")}
            for x in load_json(root, "youtube/experiments.json", "experiments")]
    todo = [{k: t.get(k) for k in ("text", "owner", "due", "status", "done_on")}
            for t in load_json(root, "youtube/todo.json", "todo")]
    return {"generated": now_iso(), "source": source, "episodes": episodes(root, now), "next": next_batch(root, made),
            "remake": remake_pool(root), "experiments": exps, "todo": todo, "prs": open_prs() if with_prs else None}


def main_snapshot(tmp):
    """origin/main 上儀表板要的檔案 → tmp，回傳 (路徑, 'main@<sha>')。"""
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", "main"], check=True)
    sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "origin/main"],
                         check=True, capture_output=True, text=True).stdout.strip()
    tar = subprocess.run(["git", "-C", str(ROOT), "archive", "origin/main", "--", *PATHS], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", tmp], input=tar, check=True)
    return Path(tmp), f"main@{sha}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT, help=f"寫到哪裡（預設 {OUT}）")
    ap.add_argument("--print", action="store_true", help="只印出，不寫檔")
    ap.add_argument("--worktree", action="store_true", help="讀目前的工作目錄，不讀 origin/main")
    ap.add_argument("--no-prs", action="store_true", help="不抓 GitHub 的 PR 清單")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        if a.worktree:
            branch = subprocess.run(["git", "-C", str(ROOT), "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
            root, source = ROOT, f"worktree {branch}"
        else:
            root, source = main_snapshot(tmp)
        data = repo_section(root, source, with_prs=not a.no_prs)
    text = json.dumps(data, ensure_ascii=False, indent=1)
    if a.print:
        print(text)
        return
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out.with_suffix(".tmp")
    tmp_out.write_text(text, encoding="utf-8")
    os.replace(tmp_out, out)   # 先寫暫存再換名，儀表板不會讀到寫一半的檔
    print(f"寫好 {out}（{source}，{len(data['episodes'])} 集、推薦 {len(data['next'])} 份、PR {len(data['prs'] or [])} 個）")


if __name__ == "__main__":
    main()
