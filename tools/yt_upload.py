#!/usr/bin/env python3
"""Upload one video (episode or Short) to the 深夜 Debug YouTube channel with the YouTube Data API v3.

Standard library only, like the rest of tools/ (runs on the GitHub Actions runner without pip). Pipeline: docs/video.md, step 9d.

  # what would be sent, no network:
  python3 tools/yt_upload.py --ep ep40 --video ep40.mp4 --dry-run
  # check the credentials point at the right channel (read-only):
  python3 tools/yt_upload.py --check
  # upload, scheduled public at youtube.publish_at:
  python3 tools/yt_upload.py --ep ep40 --video ep40.mp4 --sha256 <from video/render_log.json>
  # anything without an episode.json:
  python3 tools/yt_upload.py --video x.mp4 --title "…" --description-file d.txt --privacy private

Credentials (OAuth 2.0, installed-app client, authorized once by the channel owner; see
/mnt/project-files/youtube-api/get_refresh_token.py): environment variables YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
Scopes: youtube.upload (videos.insert), youtube (thumbnails, playlists, channels.list), youtube.force-ssl (captions;
the 2026-11-20 token lacks it, so --captions fails with 403 until the owner re-authorizes with it).

Steps, each one an API call:
  1. videos.insert, resumable upload in chunks, retried on 5xx and network errors. snippet: title, description, tags,
     categoryId, defaultLanguage / defaultAudioLanguage zh-TW. status: privacyStatus, publishAt (scheduled release,
     needs privacyStatus=private), selfDeclaredMadeForKids=false, containsSyntheticMedia (the host's voice is AI-generated).
  2. thumbnails.set     (--thumbnail, PNG/JPG up to 2 MB)
  3. captions.insert    (--captions, .srt, zh-TW)
  4. playlistItems.insert (--playlist)
  5. writes the new video id to youtube/uploads.json, so the same episode is never uploaded twice.

Quota (default 10,000 units/day): videos.insert is the expensive call; thumbnails.set, captions.insert and
playlistItems.insert are about 50 each. Check the official quota calculator before batch runs.

Scheduling: --privacy private plus --publish-at makes YouTube publish the video at that time. Verified 2026-11-20 after
the API Services review closed: a test upload kept privacyStatus private and its publishAt after processing, with no
rejection or failure reason (API uploads are no longer forced private). Plan for automated Shorts and video versions: docs/publish.md.
"""
import argparse, hashlib, json, mimetypes, os, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "youtube" / "uploads.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"
CHUNK = 8 * 1024 * 1024          # multiple of 256 KiB, as the resumable protocol requires
RETRY_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 8
CATEGORY_SCIENCE_TECH = "28"


class YouTubeError(RuntimeError):
    pass


# ───────────────────────────── auth and HTTP ─────────────────────────────

def access_token():
    missing = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing:
        sys.exit("missing environment variables: " + ", ".join(missing))
    body = urllib.parse.urlencode(dict(client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                                       refresh_token=os.environ["YT_REFRESH_TOKEN"], grant_type="refresh_token")).encode()
    try:
        r = json.load(urllib.request.urlopen(TOKEN_URL, body, timeout=30))
    except urllib.error.HTTPError as e:
        # invalid_grant: the owner revoked access (myaccount.google.com/permissions) or the token expired; rerun get_refresh_token.py
        sys.exit(f"token refresh failed: {e.code} {e.read().decode()[:300]}")
    return r["access_token"]


def request(token, method, url, data=None, headers=None, params=None, ok=(200, 201)):
    """One HTTP call. Returns (status, headers, body bytes). Raises YouTubeError on an unexpected status."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    h = {"Authorization": "Bearer " + token}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            status, rh, body = r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        status, rh, body = e.code, dict(e.headers), e.read()
    if status not in ok:
        raise YouTubeError(f"{method} {url.split('?')[0]} -> {status}: {body.decode(errors='replace')[:500]}")
    return status, rh, body


def with_retries(what, fn):
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = str(e)
        except YouTubeError as e:
            if not any(f"-> {s}:" in str(e) for s in RETRY_STATUS):
                raise
            err = str(e)
        wait = min(2 ** attempt, 64)
        print(f"  {what}: {err[:120]} (retry in {wait}s)", file=sys.stderr)
        time.sleep(wait)
    raise YouTubeError(f"{what}: gave up after {MAX_RETRIES} attempts")


# ───────────────────────────── API calls ─────────────────────────────

def my_channel(token):
    _, _, body = request(token, "GET", f"{API}/channels", params=dict(part="snippet", mine="true"))
    items = json.loads(body).get("items", [])
    if not items:
        raise YouTubeError("these credentials have no YouTube channel")
    return items[0]["id"], items[0]["snippet"]["title"]


def upload_video(token, path, resource):
    """videos.insert with the resumable upload protocol. Returns the new video's resource."""
    size = path.stat().st_size
    ctype = mimetypes.guess_type(path.name)[0] or "video/mp4"
    parts = ",".join(resource)

    def start():
        _, h, _ = request(token, "POST", f"{UPLOAD_API}/videos", data=json.dumps(resource).encode(),
                          params=dict(uploadType="resumable", part=parts),
                          headers={"Content-Type": "application/json; charset=UTF-8",
                                   "X-Upload-Content-Type": ctype, "X-Upload-Content-Length": str(size)})
        return {k.lower(): v for k, v in h.items()}["location"]

    session = with_retries("start upload", start)
    offset = 0
    with path.open("rb") as f:
        while True:
            f.seek(offset)
            chunk = f.read(CHUNK)
            end = offset + len(chunk) - 1

            def put():
                return request(token, "PUT", session, data=chunk, ok=(200, 201, 308),
                               headers={"Content-Length": str(len(chunk)), "Content-Range": f"bytes {offset}-{end}/{size}"})

            try:
                status, h, body = with_retries(f"upload bytes {offset}-{end}", put)
            except YouTubeError:
                # ask the server how much it has, then resume from there
                status, h, body = request(token, "PUT", session, data=b"", ok=(200, 201, 308),
                                          headers={"Content-Length": "0", "Content-Range": f"bytes */{size}"})
            if status in (200, 201):
                print(f"  uploaded {size / 1e6:.1f} MB", file=sys.stderr)
                return json.loads(body)
            rng = {k.lower(): v for k, v in h.items()}.get("range")      # "bytes=0-1234"
            offset = int(rng.split("-")[1]) + 1 if rng else 0
            print(f"  {offset / size:6.1%}", file=sys.stderr)


def set_thumbnail(token, video_id, path):
    ctype = mimetypes.guess_type(path.name)[0] or "image/png"
    with_retries("thumbnails.set", lambda: request(token, "POST", f"{UPLOAD_API}/thumbnails/set", data=path.read_bytes(),
                                                   params=dict(videoId=video_id, uploadType="media"),
                                                   headers={"Content-Type": ctype}))


def insert_captions(token, video_id, path, language, name):
    meta = json.dumps({"snippet": {"videoId": video_id, "language": language, "name": name, "isDraft": False}}).encode()
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n").encode() + meta + \
           (f"\r\n--{b}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    with_retries("captions.insert", lambda: request(token, "POST", f"{UPLOAD_API}/captions", data=body,
                                                    params=dict(part="snippet", uploadType="multipart"),
                                                    headers={"Content-Type": f"multipart/related; boundary={b}"}))


def add_to_playlist(token, video_id, playlist_id):
    body = {"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    with_retries("playlistItems.insert", lambda: request(token, "POST", f"{API}/playlistItems", data=json.dumps(body).encode(),
                                                         params=dict(part="snippet"),
                                                         headers={"Content-Type": "application/json; charset=UTF-8"}))


# ───────────────────────────── inputs ─────────────────────────────

def episode(ep):
    hits = sorted(ROOT.glob(f"episodes/{ep}*/episode.json"))
    if len(hits) != 1:
        sys.exit(f"--ep {ep}: expected one episode folder, found {len(hits)}")
    return hits[0].parent, json.loads(hits[0].read_text(encoding="utf-8"))


def build(a):
    """Merge command-line options over episode.json. Returns (resource, extras)."""
    yt, ep_dir, e = {}, None, {}
    if a.ep:
        ep_dir, e = episode(a.ep)
        yt = e.get("youtube", {})
        if a.short:
            yt = {**yt, **yt.get("short", {})}
    title = a.title or yt.get("title") or e.get("title")
    if a.description_file:
        description = Path(a.description_file).read_text(encoding="utf-8")
    else:
        description = e.get("description", "")
    publish_at = a.publish_at if a.publish_at is not None else yt.get("publish_at")
    privacy = a.privacy
    if publish_at and privacy != "private":
        sys.exit("publishAt only works with --privacy private (YouTube makes it public at that time)")
    synthetic = a.synthetic if a.synthetic is not None else yt.get("synthetic_content", True)
    if not title:
        sys.exit("no title: pass --title or --ep with youtube.title in episode.json")
    if len(title) > 100:
        sys.exit(f"title is {len(title)} characters; YouTube allows 100")
    if len(description.encode("utf-8")) > 5000:
        sys.exit("description is over 5000 bytes")
    if "<" in title + description or ">" in title + description:
        sys.exit("YouTube rejects < and > in title and description")
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": bool(synthetic)}
    if publish_at:
        status["publishAt"] = publish_at
    resource = {"snippet": {"title": title, "description": description, "tags": a.tags or yt.get("tags", []),
                            "categoryId": a.category, "defaultLanguage": "zh-TW", "defaultAudioLanguage": "zh-TW"},
                "status": status}
    vdir = ep_dir / "video" if ep_dir else None
    thumb = Path(a.thumbnail) if a.thumbnail else (vdir / "thumbnail-a.png" if vdir and not a.short else None)
    caps = Path(a.captions) if a.captions else None
    if caps is None and vdir:
        found = sorted(vdir.glob("short*.srt" if a.short else "*.srt"))
        caps = found[0] if found else None
    playlist = a.playlist or (None if a.short else os.environ.get("YT_PLAYLIST_ID"))
    key = (a.ep + (":short" if a.short else "")) if a.ep else None
    return resource, dict(thumbnail=thumb if thumb and thumb.exists() else None, captions=caps, playlist=playlist, key=key)


def load_uploads():
    return json.loads(UPLOADS.read_text(encoding="utf-8")) if UPLOADS.exists() else {}


def record(key, video_id):
    data = load_uploads()
    ep, _, kind = key.partition(":")
    data.setdefault(ep, {})["short" if kind == "short" else "video"] = video_id
    UPLOADS.parent.mkdir(exist_ok=True)
    UPLOADS.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ───────────────────────────── main ─────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="only refresh the token and print which channel it belongs to")
    ap.add_argument("--ep", help="episode id prefix, e.g. ep40; reads episodes/ep40*/episode.json")
    ap.add_argument("--short", action="store_true", help="upload the episode's Short (uses youtube.short.*)")
    ap.add_argument("--video", help="the mp4 to upload")
    ap.add_argument("--sha256", help="refuse to upload unless the mp4 has this sha256 (from video/render_log.json)")
    ap.add_argument("--title")
    ap.add_argument("--description-file")
    ap.add_argument("--tags", nargs="*")
    ap.add_argument("--category", default=CATEGORY_SCIENCE_TECH)
    ap.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    ap.add_argument("--publish-at", help="ISO 8601 time to make the video public, e.g. 2026-11-27T21:00:00+08:00")
    ap.add_argument("--synthetic", dest="synthetic", action="store_true", default=None, help="declare altered or synthetic content")
    ap.add_argument("--no-synthetic", dest="synthetic", action="store_false")
    ap.add_argument("--thumbnail")
    ap.add_argument("--captions", help=".srt file")
    ap.add_argument("--caption-name", default="中文（台灣）")
    ap.add_argument("--playlist", help="playlist id (default: env YT_PLAYLIST_ID, long videos only)")
    ap.add_argument("--channel", help="refuse to upload unless the credentials belong to this channel id")
    ap.add_argument("--force", action="store_true", help="upload even if youtube/uploads.json already has this episode")
    ap.add_argument("--dry-run", action="store_true", help="print what would be sent and stop")
    a = ap.parse_args()

    if a.check:
        cid, name = my_channel(access_token())
        print(f"{name} ({cid})")
        return

    if not a.video:
        ap.error("--video is required")
    video = Path(a.video)
    if not video.is_file():
        sys.exit(f"{video}: not found")
    resource, x = build(a)
    if x["key"] and not a.force:
        done = load_uploads().get(x["key"].split(":")[0], {}).get("short" if a.short else "video")
        if done:
            sys.exit(f"{x['key']} is already uploaded as https://youtu.be/{done} (youtube/uploads.json); --force to upload again")
    if a.sha256 and sha256(video) != a.sha256.lower():
        sys.exit(f"{video}: sha256 does not match --sha256; not uploading a file nobody reviewed")

    plan = {"video": str(video), "bytes": video.stat().st_size, "resource": resource,
            "thumbnail": str(x["thumbnail"]) if x["thumbnail"] else None,
            "captions": str(x["captions"]) if x["captions"] else None, "playlist": x["playlist"], "record_as": x["key"]}
    print(json.dumps(plan, ensure_ascii=False, indent=1))
    if a.dry_run:
        return

    token = access_token()
    cid, name = my_channel(token)
    print(f"channel: {name} ({cid})", file=sys.stderr)
    if a.channel and cid != a.channel:
        sys.exit(f"credentials belong to {cid}, not {a.channel}; not uploading")

    v = upload_video(token, video, resource)
    vid = v["id"]
    print(f"video: https://youtu.be/{vid} ({v['status'].get('privacyStatus')}, "
          f"publishAt {v['status'].get('publishAt', '-')}, upload {v['status'].get('uploadStatus')})", file=sys.stderr)
    if x["key"]:
        record(x["key"], vid)                       # write first: a later step failing must not cause a re-upload
    problems = []
    for what, fn in (("thumbnail", lambda: x["thumbnail"] and set_thumbnail(token, vid, x["thumbnail"])),
                     ("captions", lambda: x["captions"] and insert_captions(token, vid, x["captions"], "zh-TW", a.caption_name)),
                     ("playlist", lambda: x["playlist"] and add_to_playlist(token, vid, x["playlist"]))):
        try:
            fn()
        except YouTubeError as e:
            problems.append(f"{what}: {e}")
    print(json.dumps({"video_id": vid, "url": f"https://youtu.be/{vid}", "problems": problems}, ensure_ascii=False))
    if problems:
        sys.exit("video uploaded, but: " + "; ".join(problems))


if __name__ == "__main__":
    main()
