#!/usr/bin/env python3
"""Fix up the episodes YouTube imports from the podcast RSS feed: mark them AI-generated and make them public.

YouTube's RSS import uploads every new episode as private and leaves "altered or synthetic content" unset
(docs/hooks.md, YouTube 上傳設定). Run hourly by .github/workflows/yt-autofix.yml until episodes are uploaded with
tools/yt_upload.py instead.

  python3 tools/yt_autofix.py --dry-run     # list what it would change, no writes
  python3 tools/yt_autofix.py               # change it

It looks at the channel's 50 newest videos and changes only the private ones whose title carries an episode number
(EP40, ｜EP40) whose episodes/*/episode.json is status "final" with a "published" time in the past. For each of those,
one videos.update sets status.containsSyntheticMedia = true and privacyStatus = public. Once a video is public the
next run leaves it alone, so each episode costs one update. Never touched: public or unlisted videos, scheduled
videos (publishAt), private videos with no matching published episode, video ids listed in KEEP_PRIVATE, and
anything tools/yt_upload.py uploaded (youtube/uploads.json: video versions and Shorts), so only the RSS imports change.
An episode someone makes public by hand before the job runs does not get the AI label; set it in Studio.
(The API accepts containsSyntheticMedia on write but never returns it on read, so the label cannot be checked later.)
videos.update replaces the whole status part, so every other status field is sent back unchanged.

Quota: about 3 units per run to list, 50 per update; hourly runs stay far under the 10,000 daily units. Standard library only. Credentials as tools/yt_upload.py.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yt_upload import API, ROOT, access_token, request, with_retries, my_channel, load_uploads  # noqa: E402

CHANNEL = "UCet7D-lLR3LKQY0NeMjYxoA"      # 深夜 Debug
KEEP_PRIVATE = set()                        # video ids that must never be made public
KEEP_FIELDS = ("privacyStatus", "publishAt", "embeddable", "license", "publicStatsViewable")


def published_episodes(now):
    eps = {}
    for p in ROOT.glob("episodes/*/episode.json"):
        e = json.loads(p.read_text(encoding="utf-8"))
        if e.get("status") == "final" and e.get("published") and datetime.fromisoformat(e["published"]) <= now:
            eps[int(e["number"])] = e
    return eps


def newest_videos(token):
    _, _, b = request(token, "GET", f"{API}/channels", params=dict(part="contentDetails", mine="true"))
    uploads = json.loads(b)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    _, _, b = request(token, "GET", f"{API}/playlistItems", params=dict(part="contentDetails", playlistId=uploads, maxResults=50))
    ids = [i["contentDetails"]["videoId"] for i in json.loads(b)["items"]]   # newest first; 50 is plenty for --days
    if not ids:
        return []
    _, _, b = request(token, "GET", f"{API}/videos", params=dict(part="snippet,status", id=",".join(ids)))
    return json.loads(b)["items"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    now = datetime.now(timezone.utc)
    token = access_token()
    cid, title = my_channel(token)
    if cid != CHANNEL:
        sys.exit(f"credentials point at {title} ({cid}), not 深夜 Debug ({CHANNEL}); nothing changed")
    eps = published_episodes(now)
    ours = {vid for kinds in load_uploads().values() for vid in kinds.values()}
    fails = 0
    todo = 0
    for v in newest_videos(token):
        st, vt = v["status"], v["snippet"]["title"]
        if st.get("privacyStatus") != "private":
            continue
        m = re.search(r"EP(\d+)", vt)
        if "publishAt" in st or v["id"] in KEEP_PRIVATE or v["id"] in ours or m is None or int(m.group(1)) not in eps:
            print(f"left private: {v['id']} {vt}")
            continue
        todo += 1
        body = {k: st[k] for k in KEEP_FIELDS if k in st}
        body["selfDeclaredMadeForKids"] = st.get("selfDeclaredMadeForKids", st.get("madeForKids", False))
        body["containsSyntheticMedia"] = True
        body["privacyStatus"] = "public"
        what = "AI label + public"
        if a.dry_run:
            print(f"would set {what}: {v['id']} {vt}")
            continue
        try:
            _, _, b = with_retries(v["id"], lambda: request(token, "PUT", f"{API}/videos", params=dict(part="status"),
                                                           data=json.dumps(dict(id=v["id"], status=body)).encode(),
                                                           headers={"Content-Type": "application/json"}))
            got = json.loads(b)["status"]
            ok = got.get("containsSyntheticMedia") is True and got.get("privacyStatus") == body["privacyStatus"]
            print(f"{'ok' if ok else 'MISMATCH'} {what}: {v['id']} {vt} -> {got.get('privacyStatus')}")
            fails += not ok
        except Exception as e:  # keep going with the other videos, fail the run at the end
            print(f"FAILED {what}: {v['id']} {vt}: {e}", file=sys.stderr)
            fails += 1
    print(f"{todo} episode(s) to fix, {fails} failed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
