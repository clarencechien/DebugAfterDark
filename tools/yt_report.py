#!/usr/bin/env python3
"""深夜 Debug YouTube 成效報表：抓 Analytics + Reporting API，產生一份 HTML。

  python3 tools/yt_report.py --data-dir /mnt/project-files/yt-report --out report.html

需要環境變數 YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN（OAuth，綁定 深夜 Debug 頻道，
scope 含 youtube.readonly 或 youtube、yt-analytics.readonly）。只用標準函式庫。

原則（專案規則）：
- 所有比較只看自然流量。廣告 = Analytics 的 ADVERTISING 流量來源；留存用 audienceType==ORGANIC。
- 曝光與點閱率只有 Reporting API 有（channel_reach_basic_a1），縮圖曝光本來就不含廣告。
- Reporting 的報表只保留一段時間，所以下載過的 CSV 存在 data-dir/reach/，每次重算。

輸出：
- <out>：單一 HTML 報表（內嵌 SVG，深淺色模式）。
- <data-dir>/snapshot.json：這次抓到的原始資料。
- <data-dir>/summary.json：重點數字與建議動作，給每週摘要用。
"""
import argparse, csv, datetime as dt, glob, html, io, json, os, re, statistics, sys, urllib.error, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
DATA = "https://www.googleapis.com/youtube/v3"
REPORTING = "https://youtubereporting.googleapis.com/v1"
REACH_JOB = "f76d4b75-ee4b-4047-a38a-afac0836d6de"  # channel_reach_basic_a1，2026-11-20 建立，不要重建
HOOK_TITLES_FROM = 24      # EP24 起標題照 docs/hooks.md（數字、問句、可搜尋）
FIRST_DAYS = 3            # 「上架後前 N 天自然觀看」的 N；11/07–11/20 每天上架兩集，7 天會讓新標題組幾乎沒有樣本
EP07_CHANGE = "2026-11-20"  # EP07 換標題與縮圖、停廣告
EP07_BASELINE_CTR = 1.23    # % ，1,627 次曝光（Studio，換標題前）
STUDIO_BASELINE = ("2026-11-04 到 11-18（Studio 匯出）：曝光 21,736、點閱率 0.71%；"
                   "EP00–23 舊標題 0.64%（20.3k 曝光），EP24 起新標題 1.71%（1.3k 曝光）。")
TZ = ZoneInfo("Asia/Taipei")
SOURCE_ZH = {"RELATED_VIDEO": "推薦影片", "SUBSCRIBER": "訂閱內容／首頁動態", "YT_CHANNEL": "頻道頁",
             "YT_SEARCH": "YouTube 搜尋", "YT_OTHER_PAGE": "其他 YouTube 頁面", "NO_LINK_OTHER": "直接或不明",
             "PLAYLIST": "播放清單", "EXT_URL": "外部網站", "NOTIFICATION": "通知", "SHORTS": "Shorts 動態",
             "END_SCREEN": "片尾畫面", "HASHTAGS": "主題標籤", "ANNOTATION": "資訊卡", "CAMPAIGN_CARD": "活動卡",
             "VIDEO_REMIXES": "混剪", "SOUND_PAGE": "音訊頁", "IMMERSIVE_LIVE": "直播", "PRODUCT_PAGE": "產品頁"}


# ───────────────────────────── API ─────────────────────────────

class API:
    def __init__(self):
        body = urllib.parse.urlencode(dict(
            client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
            refresh_token=os.environ["YT_REFRESH_TOKEN"], grant_type="refresh_token")).encode()
        self.token = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", body))["access_token"]

    def raw(self, url, **params):
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + self.token})
        try:
            return urllib.request.urlopen(req, timeout=60).read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{e.code} {url.split('?')[0]}: {e.read().decode()[:300]}") from None

    def get(self, url, **params):
        return json.loads(self.raw(url, **params))

    def analytics(self, start, end, metrics, dimensions="", filters="", **kw):
        p = dict(ids="channel==MINE", startDate=start, endDate=end, metrics=metrics, **kw)
        if dimensions: p["dimensions"] = dimensions
        if filters: p["filters"] = filters
        r = self.get(ANALYTICS, **p)
        cols = [c["name"] for c in r["columnHeaders"]]
        return [dict(zip(cols, row)) for row in r.get("rows", [])]


def iso_seconds(d):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m: return 0
    dd, h, mi, s = (int(x or 0) for x in m.groups())
    return dd * 86400 + h * 3600 + mi * 60 + s


def repo_episodes():
    eps = []
    for f in sorted(glob.glob(os.path.join(ROOT, "episodes/*/episode.json"))):
        e = json.load(open(f, encoding="utf-8"))
        eps.append(dict(number=e["number"], id=e["id"], title=e["title"], type=e.get("type"),
                        source_url=e.get("source_url") or "", yt_title=(e.get("youtube") or {}).get("title")))
    return eps


def match_episode(v, eps):
    m = re.search(r"EP\s?(\d{1,3})", v["title"])
    if m:
        return int(m.group(1))
    for e in eps:  # 標題改掉 EPxx 的（例如 EP07 A/B），用說明欄裡的原文網址對回去
        if e["source_url"] and e["source_url"] in v["description"]:
            return e["number"]
    return None


def fetch(api, data_dir, today):
    start = "2026-01-01"
    end = today.isoformat()
    snap = dict(generated=dt.datetime.now(TZ).isoformat(timespec="minutes"), end=end)

    ch = api.get(DATA + "/channels", part="snippet,contentDetails,statistics", mine="true")["items"][0]
    snap["channel"] = dict(id=ch["id"], title=ch["snippet"]["title"], stats=ch["statistics"])
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, page = [], None
    while True:
        p = dict(part="contentDetails", playlistId=uploads, maxResults=50)
        if page: p["pageToken"] = page
        r = api.get(DATA + "/playlistItems", **p)
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        page = r.get("nextPageToken")
        if not page: break
    eps = repo_episodes()
    videos = []
    for i in range(0, len(ids), 50):
        r = api.get(DATA + "/videos", part="snippet,contentDetails,statistics,status", id=",".join(ids[i:i + 50]))
        for it in r["items"]:
            v = dict(id=it["id"], title=it["snippet"]["title"], description=it["snippet"].get("description", ""),
                     published=it["snippet"]["publishedAt"][:10], duration=iso_seconds(it["contentDetails"]["duration"]),
                     privacy=it["status"]["privacyStatus"], stats=it.get("statistics", {}))
            v["ep"] = match_episode(v, eps)
            v["short"] = v["duration"] <= 180
            videos.append(v)
    snap["videos"] = videos

    # 頻道每日，依流量來源（自然 vs 廣告）
    # 觀看時間用 views × averageViewDuration 算：estimatedMinutesWatched 在依來源、依日拆開後誤差很大（實測少一半以上）
    snap["daily_sources"] = api.analytics(start, end, "views,averageViewDuration", "day,insightTrafficSourceType", sort="day")
    snap["video_totals"] = api.analytics(start, end, "views,estimatedMinutesWatched,subscribersGained,likes,comments",
                                         "video", maxResults=200, sort="-views")
    per_video, retention = {}, {}
    for v in videos:
        if v["privacy"] != "public":
            continue
        per_video[v["id"]] = api.analytics(start, end, "views,averageViewDuration", "day,insightTrafficSourceType",
                                           f"video=={v['id']}", sort="day")
        try:
            retention[v["id"]] = [[r["elapsedVideoTimeRatio"], r["audienceWatchRatio"]] for r in api.analytics(
                start, end, "audienceWatchRatio", "elapsedVideoTimeRatio", f"video=={v['id']};audienceType==ORGANIC")]
        except RuntimeError:
            retention[v["id"]] = []
    snap["video_daily_sources"] = per_video
    snap["retention_organic"] = retention

    # Reporting API：曝光與點閱率。下載新的 CSV 存起來（報表會過期）
    reach_dir = os.path.join(data_dir, "reach")
    os.makedirs(reach_dir, exist_ok=True)
    reports, page = [], None
    while True:
        p = {"pageToken": page} if page else {}
        r = api.get(f"{REPORTING}/jobs/{REACH_JOB}/reports", **p)
        reports += r.get("reports", [])
        page = r.get("nextPageToken")
        if not page: break
    for rep in reports:
        name = f"{rep['startTime'][:10]}_{rep['id']}.csv"
        path = os.path.join(reach_dir, name)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(api.raw(rep["downloadUrl"]))
    snap["reach_reports_listed"] = len(reports)
    return snap


def load_reach(data_dir):
    """{(video_id, date): [impressions, clicks]}；同一天有重算版本時取最新下載的檔。"""
    out = {}
    for path in sorted(glob.glob(os.path.join(data_dir, "reach", "*.csv"))):
        rows = list(csv.DictReader(io.StringIO(open(path, encoding="utf-8").read())))
        if not rows: continue
        cols = rows[0].keys()
        imp = next((c for c in cols if "impressions" in c and "ctr" not in c), None)
        ctr = next((c for c in cols if "ctr" in c), None)
        if not imp: continue
        day = {}
        for r in rows:
            d = r.get("date", "")
            d = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else d
            k = (r.get("video_id", ""), d)
            n = float(r[imp] or 0)
            c = n * float(r[ctr] or 0) if ctr else 0
            a = day.setdefault(k, [0.0, 0.0]); a[0] += n; a[1] += c
        out.update(day)
    return out


# ───────────────────────────── 分析 ─────────────────────────────

def d(s): return dt.date.fromisoformat(s)


def analyse(snap, reach):
    vids = {v["id"]: v for v in snap["videos"] if v["privacy"] == "public"}
    totals = {r["video"]: r for r in snap["video_totals"]}
    # 每日（頻道）
    days = {}
    for r in snap["daily_sources"]:
        a = days.setdefault(r["day"], dict(org=0, ad=0, org_min=0, ad_min=0))
        k = "ad" if r["insightTrafficSourceType"] == "ADVERTISING" else "org"
        a[k] += r["views"]; a[k + "_min"] += r["views"] * r["averageViewDuration"] / 60
    last_data = max(days) if days else snap["end"]

    rows = []
    for vid, v in vids.items():
        daily = snap["video_daily_sources"].get(vid, [])
        org = [r for r in daily if r["insightTrafficSourceType"] != "ADVERTISING"]
        ad = [r for r in daily if r["insightTrafficSourceType"] == "ADVERTISING"]
        ov = sum(r["views"] for r in org); om = sum(r["views"] * r["averageViewDuration"] for r in org) / 60
        src = {}
        for r in org: src[r["insightTrafficSourceType"]] = src.get(r["insightTrafficSourceType"], 0) + r["views"]
        pub = d(v["published"])
        first7_end = pub + dt.timedelta(days=FIRST_DAYS - 1)
        first7 = sum(r["views"] for r in org if d(r["day"]) <= first7_end) if first7_end.isoformat() <= last_data else None
        ret = snap["retention_organic"].get(vid) or []
        r30 = None
        if ret and v["duration"] and ov >= 10:
            x = 30 / v["duration"]
            r30 = min(ret, key=lambda p: abs(p[0] - x))[1]
        imp = sum(a[0] for (i, _), a in reach.items() if i == vid)
        clk = sum(a[1] for (i, _), a in reach.items() if i == vid)
        live_days = max(1, (d(last_data) - pub).days + 1)
        ep = v["ep"]
        style = "trailer" if ep == 0 else ("short" if v["short"] else ("hook" if ep is not None and ep >= HOOK_TITLES_FROM else "poetic"))
        rows.append(dict(
            id=vid, ep=ep, title=v["title"], published=v["published"], duration=v["duration"], style=style,
            org_views=ov, ad_views=sum(r["views"] for r in ad), org_min=om,
            org_avd=(om * 60 / ov) if ov else None,
            org_avp=(om * 60 / ov / v["duration"] * 100) if ov and v["duration"] else None,
            org_per_day=ov / live_days, first7=first7, ret30=r30, sources=src,
            subs=totals.get(vid, {}).get("subscribersGained", 0),
            impressions=imp or None, ctr=(clk / imp * 100) if imp else None, retention=ret))
    rows.sort(key=lambda r: (r["ep"] is None, -(r["ep"] or 0)))
    return dict(days=days, last_data=last_data, rows=rows)


def median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def window(days, end, n):
    e = d(end); s = e - dt.timedelta(days=n - 1)
    sel = [v for k, v in days.items() if s <= d(k) <= e]
    return {k: sum(x[k] for x in sel) for k in ("org", "ad", "org_min", "ad_min")}


def actions(A, reach):
    """規則產生的候選動作，最多三個；每週摘要以這裡為起點再判斷。"""
    out, rows = [], [r for r in A["rows"] if r["style"] in ("hook", "poetic")]
    with_imp = [r for r in rows if r["impressions"] and r["impressions"] >= 100]
    if with_imp:
        tot_i = sum(r["impressions"] for r in with_imp)
        tot_c = sum(r["impressions"] * r["ctr"] / 100 for r in with_imp)
        avg = tot_c / tot_i * 100
        lost = sorted(((r["impressions"] * (avg - r["ctr"]) / 100, r) for r in with_imp if r["ctr"] < avg and r["ep"] != 7),
                      key=lambda t: -t[0])[:3]
        if lost:
            out.append(dict(kind="包裝", text="改標題與縮圖（照 hooks.md）：曝光多、點閱率低於頻道平均 "
                            f"{avg:.2f}% 的影片 " + "、".join(f"EP{r['ep']:02d}（{r['impressions']:,.0f} 曝光，{r['ctr']:.2f}%）" for _, r in lost)
                            + "。一次改一支，記下改的日期，兩週後看點閱率。"))
    else:
        cand = sorted((r for r in rows if r["style"] == "poetic" and r["ep"] != 7),
                      key=lambda r: -r["sources"].get("RELATED_VIDEO", 0))[:3]
        if cand:
            out.append(dict(kind="包裝", text="還沒有逐支的曝光數（Reporting API 第一份報表約 11/21 下午）。先用推薦影片帶來最多觀看的舊標題影片當候選："
                            + "、".join(f"EP{r['ep']:02d}" for r in cand) + "。Studio 上 EP00–23 的舊標題點閱率 0.64%，新標題 1.71%。"))
    recent = [r for r in rows if r["ret30"] is not None and r["org_views"] >= 20]
    if recent:
        worst = min(recent, key=lambda r: r["ret30"])
        med = median([r["ret30"] for r in recent])
        out.append(dict(kind="開場", text=f"EP{worst['ep']:02d} 的自然流量在 30 秒還留著 {worst['ret30']*100:.0f}%（中位數 {med*100:.0f}%），"
                        "是開場最弱的一支。下一集寫 cold open 時對照 hooks.md 的三拍，並在影片版拿掉開頭 3.6 秒。"))
    if not any(r["style"] == "short" for r in A["rows"]):
        out.append(dict(kind="Shorts", text="頻道還沒有 Shorts。EP37 的 Short 已經做好（project files 的 shorts/ep37/），上傳後這份報表會自動多一節。"))
    wk = window(A["days"], A["last_data"], 7)
    if wk["org"] + wk["ad"] and wk["ad"] / (wk["org"] + wk["ad"]) > 0.3:
        out.append(dict(kind="資料", text=f"最近 7 天有 {wk['ad']/(wk['org']+wk['ad'])*100:.0f}% 的觀看來自廣告。報表的比較都已排除廣告，但頻道總數會被拉高，看 Studio 時記得篩掉。"))
    return out[:3]


# ───────────────────────────── 實驗總覽 ─────────────────────────────

STATUS_ZH = {"running": ("●", "進行中"), "pending": ("○", "待開始"), "not_started": ("○", "未開始"),
             "done": ("✓", "已結束"), "stopped": ("✕", "停止")}


def load_experiments():
    path = os.path.join(ROOT, "youtube", "experiments.json")
    if not os.path.exists(path):
        return []
    return json.load(open(path, encoding="utf-8")).get("experiments", [])


def reach_window(reach, vid, start=None, end=None):
    """(曝光, 點閱率%)，日期區間 [start, end)，None 表示不限。"""
    i = c = 0.0
    for (v, day), (n, k) in reach.items():
        if v != vid or (start and day < start) or (end and day >= end):
            continue
        i += n; c += k
    return (i, c / i * 100) if i else (0, None)


def organic_per_day(snap, vid, start=None, end=None):
    per = {}
    for r in snap["video_daily_sources"].get(vid, []):
        if r["insightTrafficSourceType"] == "ADVERTISING": continue
        if (start and r["day"] < start) or (end and r["day"] >= end): continue
        per[r["day"]] = per.get(r["day"], 0) + r["views"]
    return (sum(per.values()) / len(per), len(per)) if per else (None, 0)


def ctr_txt(imp, ctr):
    return f"{ctr:.2f}%（{imp:,.0f} 曝光）" if ctr is not None else "—"


def experiment_metrics(x, snap, A, reach):
    """回傳 [(標籤, 值)] 與可選的表格 HTML。"""
    by_ep = {r["ep"]: r for r in A["rows"] if r["ep"] is not None and r["style"] != "short"}
    by_id = {r["id"]: r for r in A["rows"]}
    ch = x.get("change_date")
    m, extra = [], ""
    if x["kind"] == "ab_single":
        r = by_ep.get(x["ep"])
        if r:
            m.append(("基準點閱率", f"{x['baseline_ctr']:.2f}%"))
            m.append(("改後點閱率", ctr_txt(*reach_window(reach, r["id"], ch)) if ch else "—"))
            b, nb = organic_per_day(snap, r["id"], (d(ch) - dt.timedelta(days=14)).isoformat() if ch else None, ch)
            a, na = organic_per_day(snap, r["id"], ch) if ch else (None, 0)
            m.append(("每天自然觀看 改前 14 天", fmt(b, 1)))
            m.append(("每天自然觀看 改後", f"{a:.1f}（{na} 天）" if a is not None else "還沒有資料"))
    elif x["kind"] == "title_batch":
        trs = []
        for ep in x["eps"]:
            r = by_ep.get(ep)
            if not r: continue
            before = reach_window(reach, r["id"], None, ch) if ch else reach_window(reach, r["id"])
            after = reach_window(reach, r["id"], ch) if ch else (0, None)
            trs.append([f"EP{ep:02d}", E(r["title"]), ctr_txt(*before), ctr_txt(*after), fmt(r["org_views"])])
        m.append(("集數", "、".join(f"EP{e:02d}" for e in x["eps"])))
        m.append(("改標題日期", ch or "還沒改"))
        extra = table(["集", "目前標題", "改前點閱率", "改後點閱率", "自然觀看（累計）"], trs)
    elif x["kind"] == "shorts":
        r = by_id.get(x["video"])
        lr = by_ep.get(x.get("long_ep"))
        if r:
            m.append(("Short 自然觀看", fmt(r["org_views"])))
            m.append(("平均觀看比例", f"{r['org_avp']:.0f}%" if r["org_avp"] else "—"))
        else:
            m.append(("Short 自然觀看", "還沒有資料（上架後約 2–3 天才進 Analytics）"))
        if lr:
            m.append((f"EP{x['long_ep']:02d} 長片從 Shorts 來的觀看", fmt(lr["sources"].get("SHORTS", 0))))
        if x.get("studio_only"):
            m.append(("滑走率", x["studio_only"]))
    elif x["kind"] == "video_version":
        lo, hi = x["baseline_eps"]
        base = [by_ep[e] for e in range(lo, hi + 1) if e in by_ep and e not in x.get("exclude", [])]
        med30 = median([r["ret30"] for r in base])
        medp = median([r["org_avp"] for r in base if r["org_views"] >= 10])
        ex = "".join(f"，不含 EP{e}" for e in x.get("exclude", []))
        lo_hi = f"EP{lo}–EP{hi}{ex}"
        m.append((f"基準 {lo_hi} 30 秒留存（中位數）", f"{med30*100:.0f}%" if med30 is not None else "樣本不足"))
        m.append((f"基準 {lo_hi} 平均觀看比例（中位數）", f"{medp:.0f}%" if medp is not None else "樣本不足"))
        t = by_id.get(x.get("video")) or by_ep.get(x["ep"])
        m.append((f"EP{x['ep']} 影片版", (f"30 秒 {t['ret30']*100:.0f}%、觀看比例 {t['org_avp']:.0f}%"
                                       if t and t["ret30"] is not None and t["org_avp"] else "還沒上架")))
    return m, extra


def experiments_section(exps, snap, A, reach):
    if not exps:
        return "", []
    blocks, summ = [], []
    for x in exps:
        icon, label = STATUS_ZH.get(x.get("status"), ("○", x.get("status", "")))
        m, extra = experiment_metrics(x, snap, A, reach)
        dl = "".join(f"<div class='xm'><span>{E(k)}</span><b>{E(str(v))}</b></div>" for k, v in m)
        nxt = x.get("next_review") or "—"
        blocks.append(f"<div class='xp'><div class='xh'><h3>{E(x['name'])}</h3><span class='pill'>{icon} {E(label)}</span></div>"
                      f"<p class='sub'>測：{E(x['tests'])}<br>比：{E(x['baseline'])}<br>下次檢查：{E(nxt)}</p>{dl}{extra}</div>")
        summ.append(dict(id=x["id"], name=x["name"], status=x.get("status"), next_review=x.get("next_review"),
                         metrics=[[k, str(v)] for k, v in m]))
    body = "<div class='xps'>" + "".join(blocks) + "</div>"
    return card("實驗總覽", "共同規則：一次只改一個變數；只看自然流量。設定在 <code>youtube/experiments.json</code>，改了 YouTube 上的東西就更新那裡的日期與狀態。", body), summ


# ───────────────────────────── 待辦 ─────────────────────────────

def load_todo():
    path = os.path.join(ROOT, "youtube", "todo.json")
    if not os.path.exists(path):
        return []
    return json.load(open(path, encoding="utf-8")).get("todo", [])


def todo_section(items, today):
    if not items:
        return "", []
    open_ = [t for t in items if t.get("status") != "done"]
    done = [t for t in items if t.get("status") == "done"
            and (not t.get("done_on") or (today - d(t["done_on"])).days <= 14)]
    open_.sort(key=lambda t: (t.get("due") is None, t.get("due") or "", t.get("status") == "waiting"))
    lis = []
    for t in open_:
        due = t.get("due")
        tag = ""
        if due:
            left = (d(due) - today).days
            tag = (f"<span class='pill late'>⚠ 過期 {-left} 天（{due[5:].replace('-', '/')}）</span>" if left < 0 else
                   f"<span class='pill'>{'今天' if left == 0 else f'{left} 天後'}（{due[5:].replace('-', '/')}）</span>")
        if t.get("status") == "waiting":
            tag += "<span class='pill'>⏳ 等回覆</span>"
        lis.append(f"<li><span class='who'>{E(t.get('owner', ''))}</span><span class='tx'>{E(t['text'])}</span>{tag}</li>")
    dl = "".join(f"<li class='done'><span class='who'>{E(t.get('owner', ''))}</span><span class='tx'>✓ {E(t['text'])}</span></li>" for t in done)
    body = f"<ul class='todo'>{''.join(lis)}{dl}</ul>"
    n_late = sum(1 for t in open_ if t.get("due") and d(t["due"]) < today)
    sub = f"{len(open_)} 項待辦" + (f"，{n_late} 項過期" if n_late else "") + "。有日期的排前面。清單在 <code>youtube/todo.json</code>，做完把 status 改成 done。"
    summ = [dict(text=t["text"], owner=t.get("owner"), due=t.get("due"), status=t.get("status")) for t in open_]
    return card("待辦", sub, body), summ


# ───────────────────────────── 繪圖 ─────────────────────────────

E = html.escape


def fmt(n, digits=0):
    if n is None: return "—"
    return f"{n:,.{digits}f}"


def axis_ticks(vmax, n=4):
    if vmax <= 0: return [0, 1]
    raw = vmax / n
    mag = 10 ** len(str(int(raw))) / 10 if raw >= 1 else 1
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw: break
    top = step * (int(vmax / step) + (vmax % step > 0))
    k = 0; out = []
    while k * step <= top + 1e-9:
        out.append(k * step); k += 1
    return out


def tick_label(v):
    return f"{v/1000:g}K" if v >= 10000 else f"{v:,.0f}" if v >= 1 or v == 0 else f"{v:g}"


def svg_frame(w, h, ml, mt, mr, mb, ticks, ymax, ylabel_fmt=tick_label):
    ph = h - mt - mb
    parts = []
    for t in ticks:
        y = mt + ph - t / ymax * ph
        parts.append(f'<line x1="{ml}" x2="{w-mr}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                     f'<text x="{ml-6}" y="{y+4:.1f}" class="tick" text-anchor="end">{ylabel_fmt(t)}</text>')
    return "".join(parts)


def stacked_columns(days, keys, labels, colors, width=880, height=260):
    """每日堆疊柱狀（自然在下、廣告在上），每柱一個 hover 目標。"""
    ds = sorted(days)
    if not ds: return '<p class="empty">還沒有資料</p>'
    ml, mt, mr, mb = 44, 12, 8, 28
    pw, ph = width - ml - mr, height - mt - mb
    vmax = max(sum(days[x][k] for k in keys) for x in ds) or 1
    ticks = axis_ticks(vmax); ymax = ticks[-1]
    slot = pw / len(ds); bw = min(24, max(2, slot - 2))
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">',
           svg_frame(width, height, ml, mt, mr, mb, ticks, ymax)]
    for i, x in enumerate(ds):
        cx = ml + i * slot + (slot - bw) / 2
        y0 = mt + ph; segs = []
        tip = x + "｜" + "｜".join(f"{labels[j]} {days[x][k]:,}" for j, k in enumerate(keys))
        for j, k in enumerate(keys):
            v = days[x][k]
            if v <= 0: continue
            hgt = v / ymax * ph
            top = j == len(keys) - 1 or all(days[x][kk] <= 0 for kk in keys[j + 1:])
            gap = 2 if j > 0 else 0
            y = y0 - hgt
            if top and hgt > 4:
                r = min(4, bw / 2)
                segs.append(f'<path d="M{cx:.1f},{y0-gap:.1f} V{y+r:.1f} Q{cx:.1f},{y:.1f} {cx+r:.1f},{y:.1f} H{cx+bw-r:.1f} '
                            f'Q{cx+bw:.1f},{y:.1f} {cx+bw:.1f},{y+r:.1f} V{y0-gap:.1f} Z" fill="var({colors[j]})"/>')
            else:
                segs.append(f'<rect x="{cx:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(0.5, hgt-gap):.1f}" fill="var({colors[j]})"/>')
            y0 = y
        out.append(f'<g class="hit" tabindex="0" data-tip="{E(tip)}"><rect x="{ml+i*slot:.1f}" y="{mt}" width="{slot:.1f}" height="{ph}" fill="transparent"/>{"".join(segs)}</g>')
    step = max(1, len(ds) // 6)
    for i in range(0, len(ds), step):
        out.append(f'<text x="{ml+i*slot+slot/2:.1f}" y="{height-8}" class="tick" text-anchor="middle">{ds[i][5:].replace("-", "/")}</text>')
    out.append(f'<line x1="{ml}" x2="{width-mr}" y1="{mt+ph}" y2="{mt+ph}" class="axis"/></svg>')
    return "".join(out)


def hbars(items, width=880, value_fmt=lambda v: f"{v:,.0f}"):
    """排序後的水平長條（單一序列）。items = [(label, value)]"""
    if not items: return '<p class="empty">還沒有資料</p>'
    lw, rh = 150, 28
    h = rh * len(items) + 8
    vmax = max(v for _, v in items) or 1
    pw = width - lw - 70
    out = [f'<svg viewBox="0 0 {width} {h}" class="chart" role="img">']
    for i, (lab, v) in enumerate(items):
        y = 4 + i * rh; bw = max(1, v / vmax * pw); bh = 16
        r = min(4, bw / 2)
        out.append(f'<g class="hit" tabindex="0" data-tip="{E(lab)}｜{value_fmt(v)}"><rect x="0" y="{y}" width="{width}" height="{rh}" fill="transparent"/>'
                   f'<text x="{lw-8}" y="{y+rh/2+4}" class="lab" text-anchor="end">{E(lab)}</text>'
                   f'<path d="M{lw},{y+6} H{lw+bw-r:.1f} Q{lw+bw:.1f},{y+6} {lw+bw:.1f},{y+6+r} V{y+6+bh-r} Q{lw+bw:.1f},{y+6+bh} {lw+bw-r:.1f},{y+6+bh} H{lw} Z" fill="var(--s1)"/>'
                   f'<text x="{lw+bw+6:.1f}" y="{y+rh/2+4}" class="val">{value_fmt(v)}</text></g>')
    out.append("</svg>")
    return "".join(out)


def dot_plot(points, ylab, width=880, height=280, yfmt=tick_label, series=(("poetic", "--s2"), ("hook", "--s1"))):
    """x = 集數，y = 數值，顏色 = 標題風格。points = [(ep, value, style, tip)]"""
    pts = [p for p in points if p[1] is not None]
    if not pts: return '<p class="empty">還沒有資料</p>'
    ml, mt, mr, mb = 48, 12, 12, 30
    pw, ph = width - ml - mr, height - mt - mb
    xmin, xmax = 0, max(p[0] for p in pts) + 1
    ticks = axis_ticks(max(p[1] for p in pts)); ymax = ticks[-1] or 1
    X = lambda e: ml + (e - xmin) / (xmax - xmin) * pw
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">', svg_frame(width, height, ml, mt, mr, mb, ticks, ymax, yfmt)]
    xb = X(HOOK_TITLES_FROM - 0.5)
    out.append(f'<line x1="{xb:.1f}" x2="{xb:.1f}" y1="{mt}" y2="{mt+ph}" class="axis"/>'
               f'<text x="{xb+6:.1f}" y="{mt+12}" class="tick">EP24 起新標題</text>')
    color = dict(series)
    for ep, val, style, tip in pts:
        x = X(ep); y = mt + ph - val / ymax * ph
        out.append(f'<g class="hit" tabindex="0" data-tip="{E(tip)}"><circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="transparent"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var({color.get(style, "--muted")})" stroke="var(--surface)" stroke-width="2"/></g>')
    for e in range(0, xmax + 1, 5):
        out.append(f'<text x="{X(e):.1f}" y="{height-10}" class="tick" text-anchor="middle">EP{e:02d}</text>')
    out.append(f'<line x1="{ml}" x2="{width-mr}" y1="{mt+ph}" y2="{mt+ph}" class="axis"/></svg>')
    return "".join(out)


def lines(series, width=880, height=240, ymax=None, xfmt=None, yfmt=tick_label, xs_are_dates=False, marker_x=None, marker_label=""):
    """多條線，同一個 y 軸。series = [(name, color_var, [(x, y)])]，x 為數字或日期字串。"""
    allp = [p for _, _, s in series for p in s if p[1] is not None]
    if not allp: return '<p class="empty">還沒有資料</p>'
    ml, mt, mr, mb = 48, 12, 16, 28
    pw, ph = width - ml - mr, height - mt - mb
    conv = (lambda x: d(x).toordinal()) if xs_are_dates else (lambda x: x)
    xs = [conv(p[0]) for p in allp]
    x0, x1 = min(xs), max(xs)
    if marker_x is not None:
        x0 = min(x0, conv(marker_x)); x1 = max(x1, conv(marker_x))
    if x1 == x0: x1 = x0 + 1
    ticks = axis_ticks(ymax or max(p[1] for p in allp)); top = ticks[-1] or 1
    X = lambda x: ml + (conv(x) - x0) / (x1 - x0) * pw
    Y = lambda y: mt + ph - y / top * ph
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">', svg_frame(width, height, ml, mt, mr, mb, ticks, top, yfmt)]
    if marker_x is not None:
        mx = X(marker_x)
        out.append(f'<line x1="{mx:.1f}" x2="{mx:.1f}" y1="{mt}" y2="{mt+ph}" class="axis"/><text x="{mx+6:.1f}" y="{mt+12}" class="tick">{E(marker_label)}</text>')
    for name, col, pts in series:
        pts = [p for p in pts if p[1] is not None]
        if not pts: continue
        dpath = " ".join(f"{'M' if i == 0 else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y) in enumerate(pts))
        out.append(f'<path d="{dpath}" fill="none" stroke="var({col})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        lx, ly = pts[-1]
        out.append(f'<circle cx="{X(lx):.1f}" cy="{Y(ly):.1f}" r="4" fill="var({col})" stroke="var(--surface)" stroke-width="2"/>')
    # hover：每個 x 一條透明欄，列出所有序列
    xset = sorted({p[0] for _, _, s in series for p in s}, key=conv)
    for i, x in enumerate(xset):
        xl = X(xset[i - 1]) if i else X(x)
        xr = X(xset[i + 1]) if i + 1 < len(xset) else X(x)
        a, b = (xl + X(x)) / 2, (xr + X(x)) / 2
        vals = []
        for name, _, pts in series:
            v = dict(pts).get(x)
            if v is not None: vals.append(f"{name} {yfmt(v) if not isinstance(v, float) or v >= 1 else f'{v:.2f}'}")
        lab = xfmt(x) if xfmt else str(x)
        out.append(f'<g class="hit xhair" tabindex="-1" data-tip="{E(lab + "｜" + "｜".join(vals))}" data-x="{X(x):.1f}">'
                   f'<rect x="{a:.1f}" y="{mt}" width="{max(1, b-a):.1f}" height="{ph}" fill="transparent"/></g>')
    n = len(xset); step = max(1, n // 6)
    for i in range(0, n, step):
        x = xset[i]
        out.append(f'<text x="{X(x):.1f}" y="{height-8}" class="tick" text-anchor="middle">{E(xfmt(x) if xfmt else str(x))}</text>')
    out.append(f'<line x1="{ml}" x2="{width-mr}" y1="{mt+ph}" y2="{mt+ph}" class="axis"/></svg>')
    return "".join(out)


def legend(items, kind="rect"):
    sw = (lambda c: f'<span class="sw" style="background:var({c})"></span>') if kind == "rect" else \
         (lambda c: f'<span class="lk" style="background:var({c})"></span>')
    return '<div class="legend">' + "".join(f'<span>{sw(c)}{E(n)}</span>' for n, c in items) + "</div>"


def table(head, rows, cls=""):
    th = "".join(f"<th>{E(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def card(title, sub, body, tbl=None):
    t = f'<details class="tv"><summary>表格</summary>{tbl}</details>' if tbl else ""
    return f'<section class="card"><h2>{E(title)}</h2><p class="sub">{sub}</p>{body}{t}</section>'


def tile(label, value, delta=None, good_up=True, note=""):
    dl = ""
    if delta is not None:
        up = delta >= 0
        cls = "up" if up == good_up else "down"
        dl = f'<div class="delta {cls}">{"▲" if up else "▼"} {abs(delta):.0f}%<span> vs 前 7 天</span></div>'
    return f'<div class="tile"><div class="tl">{E(label)}</div><div class="tv2">{value}</div>{dl}<div class="tn">{note}</div></div>'


def pct_change(a, b):
    return (a - b) / b * 100 if b else None


def render(snap, A, reach, acts, xsec="", tsec=""):
    rows, days, last = A["rows"], A["days"], A["last_data"]
    wk, prev = window(days, last, 7), window(days, (d(last) - dt.timedelta(days=7)).isoformat(), 7)
    org_avd = wk["org_min"] * 60 / wk["org"] if wk["org"] else None
    prev_avd = prev["org_min"] * 60 / prev["org"] if prev["org"] else None
    reach_days = sorted({k[1] for k in reach})
    imp7 = clk7 = 0; imp_prev = clk_prev = 0
    if reach_days:
        rl = d(reach_days[-1])
        for (vid, day), (i, c) in reach.items():
            age = (rl - d(day)).days
            if 0 <= age < 7: imp7 += i; clk7 += c
            elif 7 <= age < 14: imp_prev += i; clk_prev += c
    ctr7 = clk7 / imp7 * 100 if imp7 else None
    ctr_prev = clk_prev / imp_prev * 100 if imp_prev else None

    tiles = "".join([
        tile("自然觀看（7 天）", fmt(wk["org"]), pct_change(wk["org"], prev["org"])),
        tile("自然觀看時間（分鐘）", fmt(wk["org_min"]), pct_change(wk["org_min"], prev["org_min"])),
        tile("自然平均觀看時長", f"{org_avd:.0f} 秒" if org_avd else "—", pct_change(org_avd or 0, prev_avd or 0) if prev_avd else None),
        tile("縮圖曝光（7 天）", fmt(imp7) if imp7 else "—", pct_change(imp7, imp_prev) if imp_prev else None,
             note="" if imp7 else "等 Reporting API 第一份報表"),
        tile("點閱率（7 天）", f"{ctr7:.2f}%" if ctr7 is not None else "—",
             pct_change(ctr7, ctr_prev) if ctr_prev else None, note="Studio 基準 0.71%"),
        tile("訂閱數", fmt(int(snap["channel"]["stats"].get("subscriberCount", 0))), note="頻道目前總數"),
    ])

    # 1. 每日自然 vs 廣告
    recent_days = {k: v for k, v in days.items() if d(k) >= d(last) - dt.timedelta(days=59)}
    c1 = card("每日觀看：自然流量與廣告分開", f"最近 60 天，資料到 {last}（Analytics 延遲約 2–3 天）。下面所有比較都只用自然流量。",
              legend([("自然流量", "--s1"), ("廣告", "--s2")]) + stacked_columns(recent_days, ["org", "ad"], ["自然", "廣告"], ["--s1", "--s2"]),
              table(["日期", "自然觀看", "廣告觀看", "自然分鐘"], [[k, fmt(v["org"]), fmt(v["ad"]), fmt(v["org_min"])] for k, v in sorted(recent_days.items(), reverse=True)]))

    # 2. 自然流量來源（28 天）
    s28 = {}
    cut = d(last) - dt.timedelta(days=27)
    for r in snap["daily_sources"]:
        if r["insightTrafficSourceType"] != "ADVERTISING" and d(r["day"]) >= cut:
            s28[r["insightTrafficSourceType"]] = s28.get(r["insightTrafficSourceType"], 0) + r["views"]
    items = sorted(((SOURCE_ZH.get(k, k), v) for k, v in s28.items() if v), key=lambda t: -t[1])
    c2 = card("自然流量從哪裡來", "最近 28 天，排除廣告。推薦影片多＝YouTube 在推，點閱率決定推了有沒有人點。", hbars(items),
              table(["來源", "觀看"], [[E(a), fmt(b)] for a, b in items]))

    # 3. 標題風格
    eps = [r for r in rows if r["style"] in ("hook", "poetic")]
    grp = lambda s: [r for r in eps if r["style"] == s]
    def gstat(s, key):
        return median([r[key] for r in grp(s) if not (key in ("org_avp", "ret30") and r["org_views"] < 10)])
    def cg(s):
        g = [r for r in grp(s) if r["impressions"]]
        i = sum(r["impressions"] for r in g); c = sum(r["impressions"] * r["ctr"] / 100 for r in g)
        return (c / i * 100, i) if i else (None, 0)
    style_rows = []
    for s, name in (("poetic", "EP01–23 舊標題"), ("hook", "EP24 起新標題")):
        ctr, imp = cg(s)
        style_rows.append([E(name), str(len(grp(s))), fmt(gstat(s, "first7")), fmt(gstat(s, "org_per_day"), 1),
                           f"{gstat(s, 'org_avp'):.0f}%" if gstat(s, "org_avp") else "—",
                           f"{gstat(s, 'ret30')*100:.0f}%" if gstat(s, "ret30") else "—",
                           f"{ctr:.2f}%（{imp:,.0f}）" if ctr is not None else "—"])
    pts = [(r["ep"], r["first7"], r["style"], f"EP{r['ep']:02d}｜前 {FIRST_DAYS} 天自然觀看 {r['first7']}") for r in eps if r["ep"] is not None]
    c3 = card("標題風格：舊的詩意標題 vs hooks.md 新標題",
              f"每點一集，縱軸是上架後前 {FIRST_DAYS} 天的自然觀看。表格是各組中位數；點閱率是加總後的比率（括號為曝光數）。"
              f"新集數比較新，推薦量還在累積，看趨勢不看單點。<br>{E(STUDIO_BASELINE)}",
              legend([("舊標題", "--s2"), ("新標題", "--s1")], "dot") + dot_plot(pts, "") +
              table(["組別", "支數", f"前 {FIRST_DAYS} 天自然觀看", "每天自然觀看", "平均觀看比例", "30 秒留存", "點閱率（曝光）"], style_rows))

    # 4. 留存（自然）：兩組平均曲線
    def avg_curve(s):
        acc = {}
        for r in grp(s):
            if r["org_views"] < 10 or not r["retention"]: continue
            for x, y in r["retention"]:
                acc.setdefault(round(x, 2), []).append(y)
        return sorted((x, sum(v) / len(v)) for x, v in acc.items())
    cp, ch = avg_curve("poetic"), avg_curve("hook")
    c4 = card("自然流量的留存曲線", "各組平均（只算自然觀看 10 次以上的影片）。縱軸是還在看的比例，開頭的落差就是 cold open 的成績。",
              legend([("舊標題", "--s2"), ("新標題", "--s1")], "line") +
              lines([("舊標題", "--s2", cp), ("新標題", "--s1", ch)], xfmt=lambda x: f"{x*100:.0f}%", yfmt=lambda v: f"{v*100:.0f}%" if v <= 1.5 else f"{v:.1f}"),
              table(["影片位置", "舊標題", "新標題"], [[f"{x*100:.0f}%", f"{y*100:.0f}%", f"{dict(ch).get(x, 0)*100:.0f}%"] for x, y in cp[::5]]))

    # 5. EP07 A/B
    ep7 = next((r for r in rows if r["ep"] == 7), None)
    c5 = ""
    if ep7:
        dd = {}
        for r in snap["video_daily_sources"].get(ep7["id"], []):
            if r["insightTrafficSourceType"] != "ADVERTISING":
                dd[r["day"]] = dd.get(r["day"], 0) + r["views"]
        cut = (d(EP07_CHANGE) - dt.timedelta(days=21)).isoformat()
        view_pts = sorted((k, v) for k, v in dd.items() if k >= cut)
        ctr_pts = sorted((day, a[1] / a[0] * 100) for (vid, day), a in reach.items() if vid == ep7["id"] and a[0] >= 20)
        before = [v for k, v in view_pts if k < EP07_CHANGE][-14:]
        after = [v for k, v in view_pts if k >= EP07_CHANGE]
        note = (f"換之前 14 天平均每天 {sum(before)/max(1,len(before)):.1f} 次自然觀看；換之後 {len(after)} 天"
                + (f"平均 {sum(after)/len(after):.1f} 次。" if after else "還沒有資料（Analytics 延遲）。"))
        ctr_note = (f"換之後點閱率 {sum(a[1] for (v, dy), a in reach.items() if v == ep7['id'] and dy >= EP07_CHANGE) / max(1, sum(a[0] for (v, dy), a in reach.items() if v == ep7['id'] and dy >= EP07_CHANGE)) * 100:.2f}%"
                    if any(v == ep7["id"] and dy >= EP07_CHANGE for (v, dy) in reach) else "點閱率等 Reporting API")
        c5 = card("EP07 標題與縮圖 A/B", f"{EP07_CHANGE} 換標題、換縮圖、停廣告。基準點閱率 {EP07_BASELINE_CTR}%（1,627 曝光）。{note}{ctr_note}。預計 12/4 判讀。",
                  "<h3>每日自然觀看</h3>" + lines([("自然觀看", "--s1", view_pts)], xs_are_dates=True, xfmt=lambda x: x[5:].replace("-", "/"),
                                                marker_x=EP07_CHANGE, marker_label="換標題") +
                  "<h3>每日點閱率（曝光 20 次以上的天）</h3>" +
                  (lines([("點閱率 %", "--s1", ctr_pts)], xs_are_dates=True, xfmt=lambda x: x[5:].replace("-", "/"), yfmt=lambda v: f"{v:.1f}%",
                         marker_x=EP07_CHANGE, marker_label="換標題") if ctr_pts else '<p class="empty">等 Reporting API 第一份報表（約 11/21 下午）</p>'),
                  table(["日期", "自然觀看", "點閱率"], [[k, fmt(v), next((f"{c:.2f}%" for dy, c in ctr_pts if dy == k), "—")] for k, v in reversed(view_pts)]))

    # 6. Shorts
    shorts = [r for r in rows if r["style"] == "short"]
    c6 = card("Shorts", "長度 3 分鐘以內的影片。", table(["標題", "上架", "自然觀看", "平均觀看比例"],
              [[E(r["title"]), r["published"], fmt(r["org_views"]), f"{r['org_avp']:.0f}%" if r["org_avp"] else "—"] for r in shorts])
              if shorts else '<p class="empty">還沒有 Shorts。EP37 的 Short 上傳後會出現在這裡。</p>')

    # 7. 逐集表
    trs = []
    for r in rows:
        if r["style"] == "short": continue
        st = {"hook": "新", "poetic": "舊", "trailer": "預告"}.get(r["style"], "")
        trs.append([f"EP{r['ep']:02d}" if r["ep"] is not None else "—",
                    f'<a href="https://youtu.be/{E(r["id"])}">{E(r["title"])}</a>', st, r["published"],
                    fmt(r["impressions"]), f"{r['ctr']:.2f}%" if r["ctr"] is not None else "—",
                    fmt(r["org_views"]), fmt(r["first7"]), f"{r['org_avd']:.0f}" if r["org_avd"] else "—",
                    f"{r['org_avp']:.0f}%" if r["org_avp"] else "—", f"{r['ret30']*100:.0f}%" if r["ret30"] is not None else "—",
                    fmt(r["ad_views"]) if r["ad_views"] else "", fmt(r["subs"])])
    c7 = card("逐集", "除了「廣告觀看」那欄，數字都是自然流量。曝光與點閱率從 Reporting API 開始的那天（11/20）起算。點欄位標題可排序。",
              table(["集", "標題", "標題風格", "上架", "曝光", "點閱率", "自然觀看", f"前 {FIRST_DAYS} 天", "平均秒數", "觀看比例", "30 秒留存", "廣告觀看", "新訂閱"], trs, "sortable"))

    act_html = "".join(f'<li><b>{E(a["kind"])}</b>　{E(a["text"])}</li>' for a in acts) or "<li>這週沒有規則觸發的動作。</li>"
    fresh = (f"Analytics 資料到 {last}；Reporting（曝光、點閱率）"
             + (f"到 {reach_days[-1]}，共 {len(reach_days)} 天" if reach_days else "還沒有報表（工作 11/20 建立，約 11/21 下午出第一份）"))
    return TEMPLATE.replace("%TITLE%", E(snap["channel"]["title"])).replace("%GEN%", E(snap["generated"])) \
        .replace("%FRESH%", E(fresh)).replace("%TILES%", tiles).replace("%ACTIONS%", act_html) \
        .replace("%BODY%", c1 + c2 + c3 + c4 + c5 + c6 + c7).replace("%EXPERIMENTS%", tsec + xsec)


TEMPLATE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>深夜 Debug 成效報表</title>
<style>
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;
--border:rgba(11,11,11,.10);--s1:#2a78d6;--s2:#eb6834;--good:#006300;--bad:#d03b3b}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--good:#0ca30c;--bad:#e66767}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--good:#0ca30c;--bad:#e66767}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:15px/1.6 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px 64px}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:0 0 4px}h3{font-size:14px;color:var(--ink2);margin:16px 0 4px}
.meta{color:var(--ink2);font-size:13px;margin:0 0 20px}.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;margin:16px 0}
.sub{color:var(--ink2);font-size:13px;margin:0 0 12px}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px}.tl{color:var(--ink2);font-size:13px}.tv2{font-size:26px;font-weight:600}
.tn{color:var(--muted);font-size:12px}.delta{font-size:13px;font-weight:600}.delta span{font-weight:400;color:var(--muted)}.delta.up{color:var(--good)}.delta.down{color:var(--bad)}
.actions ol{margin:0;padding-left:20px}.actions li{margin:8px 0}
.chart{width:100%;height:auto;display:block}.grid{stroke:var(--grid);stroke-width:1}.axis{stroke:var(--axis);stroke-width:1}
.tick{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}.lab{fill:var(--ink2);font-size:12px}.val{fill:var(--ink);font-size:12px;font-variant-numeric:tabular-nums}
.hit{outline:none;cursor:default}.hit:hover>*:not(rect[fill=transparent]),.hit:focus>*:not(rect[fill=transparent]){opacity:.8}
.legend{display:flex;gap:16px;font-size:13px;color:var(--ink2);margin:0 0 6px;flex-wrap:wrap}.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{width:10px;height:10px;border-radius:2px;display:inline-block}.lk{width:14px;height:2px;display:inline-block}
.legend .lk{height:2px}.legend span .lk[style]{border-radius:1px}
#tip{position:fixed;pointer-events:none;background:var(--surface);color:var(--ink);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:12px;
box-shadow:0 4px 16px rgba(0,0,0,.15);display:none;max-width:280px;z-index:9;white-space:pre-line}
#xh{position:absolute;pointer-events:none}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:6px 8px;border-bottom:1px solid var(--grid);text-align:right;white-space:nowrap}
th:first-child,td:first-child,td:nth-child(2),th:nth-child(2){text-align:left}td:nth-child(2){white-space:normal;min-width:200px}
td{font-variant-numeric:tabular-nums}.sortable th{cursor:pointer;user-select:none}a{color:var(--s1)}
.xps{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:12px}.xp{border:1px solid var(--border);border-radius:10px;padding:14px}.xh{display:flex;justify-content:space-between;align-items:baseline;gap:8px}.xh h3{margin:0;color:var(--ink);font-size:15px}.pill{font-size:12px;color:var(--ink2);border:1px solid var(--border);border-radius:999px;padding:1px 8px;white-space:nowrap}.xm{display:flex;justify-content:space-between;gap:12px;font-size:13px;padding:4px 0;border-bottom:1px solid var(--grid)}.xm span{color:var(--ink2)}.xm b{font-weight:600;text-align:right}code{font-size:12px}.todo{list-style:none;margin:0;padding:0}.todo li{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px;padding:8px 0;border-bottom:1px solid var(--grid);font-size:14px}.todo .who{font-size:12px;color:var(--muted);min-width:64px}.todo .tx{flex:1 1 300px}.todo li.done{color:var(--muted)}.pill.late{color:var(--bad);border-color:var(--bad)}details.tv{margin-top:8px;font-size:13px;color:var(--ink2)}details.tv summary{cursor:pointer}.empty{color:var(--muted);font-size:13px;padding:24px 0;text-align:center}
</style></head><body><main>
<h1>%TITLE% 成效報表</h1>
<p class="meta">產生於 %GEN%（台北）。%FRESH%。所有比較只看自然流量，廣告另列。</p>
<div class="tiles">%TILES%</div>
%EXPERIMENTS%
<section class="card actions"><h2>本週建議動作</h2><p class="sub">由規則挑出的候選，每週摘要再判斷要不要做。</p><ol>%ACTIONS%</ol></section>
%BODY%
</main><div id="tip"></div>
<script>
const tip=document.getElementById('tip');
function show(e,g){tip.textContent=g.dataset.tip.split('｜').join('\\n');tip.style.display='block';
 const r=e.clientX!==undefined&&e.clientX?{x:e.clientX,y:e.clientY}:(()=>{const b=g.getBoundingClientRect();return{x:b.left+b.width/2,y:b.top}})();
 const w=tip.offsetWidth;tip.style.left=Math.min(window.innerWidth-w-8,r.x+12)+'px';tip.style.top=(r.y+14)+'px';}
document.querySelectorAll('.hit').forEach(g=>{g.addEventListener('pointermove',e=>show(e,g));g.addEventListener('focus',e=>show({},g));
 g.addEventListener('pointerleave',()=>tip.style.display='none');g.addEventListener('blur',()=>tip.style.display='none');});
document.querySelectorAll('table.sortable').forEach(t=>{t.querySelectorAll('th').forEach((th,i)=>{let asc=false;th.addEventListener('click',()=>{
 const rows=[...t.tBodies[0].rows];const v=r=>{const s=r.cells[i].textContent.replace(/[,%秒]/g,'');const n=parseFloat(s);return isNaN(n)?(s==='—'||s===''?-Infinity:s):n};
 asc=!asc;rows.sort((a,b)=>{const x=v(a),y=v(b);return (x>y?1:x<y?-1:0)*(asc?1:-1)});rows.forEach(r=>t.tBodies[0].appendChild(r));});});});
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_dir = "/mnt/project-files/yt-report" if os.path.isdir("/mnt/project-files") else os.path.join(ROOT, "yt-report-data")
    ap.add_argument("--data-dir", default=default_dir, help="存 snapshot、Reporting CSV 的資料夾")
    ap.add_argument("--out", help="HTML 輸出路徑（預設 data-dir/report.html）")
    ap.add_argument("--offline", action="store_true", help="不抓資料，用 data-dir/snapshot.json 重畫")
    a = ap.parse_args()
    os.makedirs(a.data_dir, exist_ok=True)
    snap_path = os.path.join(a.data_dir, "snapshot.json")
    if a.offline:
        snap = json.load(open(snap_path, encoding="utf-8"))
    else:
        snap = fetch(API(), a.data_dir, dt.date.today())
        json.dump(snap, open(snap_path, "w", encoding="utf-8"), ensure_ascii=False)
    reach = load_reach(a.data_dir)
    A = analyse(snap, reach)
    acts = actions(A, reach)
    xsec, xsum = experiments_section(load_experiments(), snap, A, reach)
    tsec, tsum = todo_section(load_todo(), dt.datetime.now(TZ).date())
    out = a.out or os.path.join(a.data_dir, "report.html")
    open(out, "w", encoding="utf-8").write(render(snap, A, reach, acts, xsec, tsec))
    wk = window(A["days"], A["last_data"], 7)
    summary = dict(generated=snap["generated"], analytics_to=A["last_data"], reach_days=len({k[1] for k in reach}),
                   organic_views_7d=wk["org"], ad_views_7d=wk["ad"], organic_minutes_7d=wk["org_min"], actions=acts, experiments=xsum, todo=tsum,
                   episodes=[{k: r[k] for k in ("ep", "id", "title", "style", "org_views", "first7", "org_avp", "ret30", "impressions", "ctr")}
                             for r in A["rows"]])
    for name in ("summary.json", f"summary-{snap['generated'][:10]}.json"):  # 帶日期的那份給下週比較用
        json.dump(summary, open(os.path.join(a.data_dir, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"report: {out}\nanalytics to {A['last_data']}, reach days {summary['reach_days']}, actions {len(acts)}")


if __name__ == "__main__":
    main()
