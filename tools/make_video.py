"""Step 9a (docs/video.md): turn a mastered episode into the 1920x1080 YouTube video version.

  python3 tools/make_video.py episodes/<ep> --skeleton        # writes video/visuals.json to edit by hand (chapters + number candidates)
  python3 tools/make_video.py episodes/<ep> --capture-figures # Playwright: report figures -> video/visuals/fig*.png
  python3 tools/make_video.py episodes/<ep> --out DIR         # renders DIR/<ep>.mp4 + preview/, writes video/*.srt, chapters.txt, thumbnails, render_log.json
  python3 tools/make_video.py episodes/<ep> --thumbnail-only  # only video/thumbnail-a.png, -b.png (from episode.json youtube.thumbnail)

Timeline: the master is sting 3.2 s + lead 0.4 s, s00, 0.6 s, ident (show/ident/ident.flac), 0.6 s, segments with 0.6 s gaps,
lead 0.4 s + outro sting 3.2 s (make_podcast.py cmd_master). Segment wavs are not in git, so the starts are measured on the mp3:
the ident by cross-correlation (exact), every later segment by fitting the chosen take's Breeze phrase starts (qa/select_log.json
`segments`; EP01-09 fall back to qa/stt_check.json `whisper_segments`) to speech onsets, then snapped into the 0.6 s gap silence.
The video drops the first 3.6 s (sting + lead) so frame 1 is the cold open; nothing else in the audio changes.

Needs ffmpeg, Pillow, numpy, fonts-noto-cjk (Traditional Chinese = ttc index 3), and LXGW WenKai TC for the show name
(looked up in ~/.cache/dad-fonts, then fc-match; falls back to Noto). --capture-figures needs Node + Playwright.
"""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
INTRO, LEAD, GAP, OUTRO = 3.2, 0.4, 0.6, 3.2
TRIM = INTRO + LEAD                     # dropped from the start of the video
W, H, FPS = 1920, 1080, 30
SR = 16000                              # analysis sample rate
FADE, CHAPTER_CARD = 0.3, 1.5
LINE_CHARS, MAX_LINES = 16, 2

RED, WHITE, GREY, DIM = (229, 40, 46, 255), (255, 255, 255, 255), (196, 200, 214, 255), (150, 156, 172, 255)
MARKER = re.compile(r"<[^>]+>")
CLAUSE_END = "，。？！；："


# ---------------------------------------------------------------- fonts
NOTO = "/usr/share/fonts/opentype/noto/NotoSansCJK-{}.ttc"
_fc = {}


def noto(weight, size):
    k = (weight, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(NOTO.format(weight), size, index=3)
    return _fc[k]


def wenkai(size):
    for p in [Path.home() / ".cache/dad-fonts/LXGWWenKaiTC-Bold.ttf"]:
        if p.exists(): return ImageFont.truetype(str(p), size)
    try:
        p = subprocess.run(["fc-match", "-f", "%{file}", "LXGW WenKai TC:bold"], capture_output=True, text=True).stdout
        if "WenKai" in p: return ImageFont.truetype(p, size)
    except FileNotFoundError:
        pass
    return noto("Medium", size)


# ---------------------------------------------------------------- audio analysis
def load_pcm(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


def envelope_db(a):
    hop = SR // 100
    e = np.convolve(a.astype(np.float64) ** 2, np.ones(hop * 2) / (hop * 2), "same")[::hop]
    return 10 * np.log10(e + 1e-12)          # 10 ms frames


def silences(db, th=-45.0, min_s=0.4):
    q = db < th; out = []; i = 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]: j += 1
            if (j - i) / 100 >= min_s: out.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return out


def onsets(db, th=-42.0, quiet=0.15):
    out, run = [], 0
    for i, v in enumerate(db > th):
        if not v: run += 1
        else:
            if run >= quiet * 100: out.append(i / 100)
            run = 0
    return np.array(out)


def find_ident(a, ident, search_s=150):
    seg = a[: search_s * SR]
    n = len(seg) + len(ident); N = 1 << (n - 1).bit_length()
    c = np.fft.irfft(np.fft.rfft(seg, N) * np.conj(np.fft.rfft(ident, N)), N)[: len(seg) - len(ident)]
    k = int(np.argmax(c))
    return k / SR, float(c[k] / (np.sort(c)[-SR] + 1e-12))


def phrases_for(ep_dir, ids):
    sl = ep_dir / "qa/select_log.json"; out = {}
    if sl.exists():
        for s in json.loads(sl.read_text(encoding="utf-8")).get("segments", []):
            take = next((t for t in s.get("takes", []) if t["file"] == s.get("chosen")), None)
            if take and take.get("segments"): out[s["id"]] = [(float(p), str(t)) for p, t in take["segments"]]
    if len(out) < len(ids):
        st = ep_dir / "qa/stt_check.json"
        if st.exists():
            for s in json.loads(st.read_text(encoding="utf-8")).get("segments", []):
                if s["id"] in out: continue
                ws = s.get("whisper_segments")
                if isinstance(ws, str):
                    import ast; ws = ast.literal_eval(ws)
                if ws: out[s["id"]] = [(float(p), str(t)) for p, t in ws]
    missing = [i for i in ids if i not in out]
    if missing: sys.exit(f"no phrase timestamps for {missing}")
    return out


def timeline(ep_dir, mp3, ids, phr):
    """Segment start/end in mp3 time. Returns dict and a list of check rows."""
    a = load_pcm(mp3); total = len(a) / SR
    ident_p = ROOT / "show/ident/ident.flac"
    ident_len = duration(ident_p)
    ident_at, peak = find_ident(a, load_pcm(ident_p))
    if peak < 3: sys.exit(f"ident not found (peak ratio {peak:.1f})")
    db = envelope_db(a); ons = onsets(db); sil = silences(db)
    S = {ids[0]: TRIM, ids[1]: ident_at + ident_len + GAP}
    fit = dict(S); prev = ids[1]
    for sid in ids[2:]:
        lo = S[prev] + phr[prev][-1][0] + 0.8
        ps0 = np.array([p for p, _ in phr[sid]])
        best = None
        for cand in np.arange(lo, lo + 15, 0.01):
            d = np.abs((cand + ps0)[:, None] - ons[None, :]).min(1)
            sc = float(np.clip(d, 0, 0.3).sum())
            if best is None or sc < best[0]: best = (sc, cand)
        fit[sid] = float(best[1])
        # snap into the gap: the 0.6 s before a segment is pure silence, and speech cannot start before the segment does
        gap = min(sil, key=lambda s: 0 if s[0] - 0.15 <= fit[sid] <= s[1] + 0.15 else min(abs(fit[sid] - s[0]), abs(fit[sid] - s[1])))
        S[sid] = float(np.clip(fit[sid], gap[0] + GAP, gap[1] - ps0[0]))
        prev = sid
    ends = {}
    for k, sid in enumerate(ids):
        if k == 0: ends[sid] = ident_at - GAP
        elif k < len(ids) - 1: ends[sid] = S[ids[k + 1]] - GAP
        else: ends[sid] = total - LEAD - OUTRO
    # check: each boundary sits in a silence of at least GAP (tolerance 0.15 s), i.e. a gap of silence ends within 0.15 s of it
    rows = []
    for k, sid in enumerate(ids):
        b = S[sid]
        inside = [s for s in sil if s[0] - 0.15 <= b - GAP and b <= s[1] + 0.15]
        err = 0.0 if inside else min(min(abs(b - GAP - s[0]), abs(b - s[1])) for s in sil)
        rows.append({"id": sid, "start": round(b, 3), "fit": round(fit[sid], 3), "end": round(ends[sid], 3),
                     "gap_silence": [round(x, 2) for x in inside[0]] if inside else None, "error_s": round(err, 3)})
    rows.insert(1, {"id": "ident", "start": round(ident_at, 3), "end": round(ident_at + ident_len, 3),
                    "method": f"cross-correlation, peak ratio {peak:.1f}",
                    "error_s": round(min(abs(ident_at - GAP - ends[ids[0]]), 0.0), 3)})
    return S, ends, {"ident_at": ident_at, "ident_len": ident_len, "total": total, "onsets": ons, "db": db}, rows


# ---------------------------------------------------------------- text
def clean(text):
    t = MARKER.sub("", text)
    return re.sub(r"\s+", " ", t).strip()


def norm_chars(s):
    return [c.lower() for c in s if c.isalnum()]


def char_times(seg_text, phrases, t0, t_end):
    """Time (mp3 seconds) for every character index of the cleaned segment text, from the phrase starts."""
    txt = clean(seg_text)
    nidx = []; n = 0
    for c in txt:
        nidx.append(n)
        if c.isalnum(): n += 1
    scr = norm_chars(txt)
    asr, starts = [], []
    for p, t in phrases:
        starts.append((len(asr), p)); asr += norm_chars(t)
    m = [None] * (len(asr) + 1)
    for op, i1, i2, j1, j2 in SequenceMatcher(None, asr, scr, autojunk=False).get_opcodes():
        for i in range(i1, i2 + 1):
            m[i] = j1 + (j2 - j1) * (i - i1) / max(i2 - i1, 1) if op != "insert" else j1
    knots = []
    for ai, p in starts:
        j = m[ai] if m[ai] is not None else 0
        knots.append((float(j), t0 + p))
    knots.sort()
    xs = [k[0] for k in knots] + [float(len(scr))]
    ys = [k[1] for k in knots] + [t_end]
    xs[0] = min(xs[0], 0.0)
    # strictly increasing
    for i in range(1, len(ys)): ys[i] = max(ys[i], ys[i - 1] + 0.01)
    times = np.interp(nidx + [len(scr)], xs, ys)
    return txt, times, knots


def text_width(s):
    return sum(0.5 if ord(c) < 0x2E80 else 1.0 for c in s)


def strip_end(s):
    return s.strip().rstrip("，。；：、").strip()


def split_line(s):
    """Break a clause that is too long for one line into two, near the middle, not inside 《》 or an ASCII word."""
    if text_width(s) <= LINE_CHARS: return [s]
    best = None
    depth = 0
    for i in range(1, len(s)):
        ch, prev = s[i], s[i - 1]
        depth += (prev in "《「（") - (prev in "》」）")
        if depth > 0: continue
        if prev.isascii() and prev.isalnum() and ch.isascii() and ch.isalnum(): continue
        a, b = s[:i].strip(), s[i:].strip()
        if text_width(a) > LINE_CHARS or text_width(b) > LINE_CHARS: continue
        score = abs(text_width(a) - text_width(b)) - (3 if prev in "、的是了在和跟" else 0)
        if best is None or score < best[0]: best = (score, [a, b])
    return best[1] if best else None


def cues_for(txt, times):
    """Subtitle cues for one segment: one clause per line, at most two lines, 16 chars a line."""
    clauses, cur, st = [], "", 0
    for i, c in enumerate(txt):
        if not cur: st = i
        cur += c
        if c in CLAUSE_END:
            clauses.append((st, cur)); cur = ""
    if cur.strip(): clauses.append((st, cur))
    units = []                                   # (start_idx, [lines], ends_sentence)
    for st, c in clauses:
        lead = len(c) - len(c.lstrip()); st += lead; c = c.strip()
        sentence = c[-1] in "。？！"
        body = c.rstrip("，。；：") if c[-1] in "，。；：" else c
        lines = split_line(body)
        if lines: units.append([st, lines, sentence]); continue
        # longer than two lines: cut into pieces of at most 2x16, timed by character interpolation
        pieces, rest, off = [], body, 0
        while rest:
            take = len(rest)
            while text_width(rest[:take]) > LINE_CHARS * 2 or (take < len(rest) and split_line(rest[:take]) is None): take -= 1
            if take < len(rest):     # prefer breaking after 的/了/，
                for k in range(take, max(take - 6, 1), -1):
                    if rest[k - 1] in "的了是、" and split_line(rest[:k]): take = k; break
            pieces.append((off, rest[:take])); off += take; rest = rest[take:]
        for k, (o, p) in enumerate(pieces):
            units.append([st + o, split_line(p), sentence and k == len(pieces) - 1])
    cues = []
    for st, lines, sentence in units:
        if cues and len(cues[-1]["lines"]) == 1 and len(lines) == 1 and not cues[-1]["sentence"] \
                and times[st] - cues[-1]["t"] < 3.5:
            cues[-1]["lines"].append(lines[0]); cues[-1]["sentence"] = sentence
            continue
        cues.append({"i": st, "t": float(times[st]), "lines": lines, "sentence": sentence})
    return cues


# ---------------------------------------------------------------- numbers (card check)
CN_DIG = {"〇": 0, "零": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNIT = {"十": 10, "百": 100, "千": 1000}
CN_BIG = {"萬": 1e4, "億": 1e8, "兆": 1e12}


def cn_value(tok):
    if "點" in tok:
        a, b = tok.split("點", 1)
        return (cn_value(a) if a else 0) + float("0." + "".join(str(CN_DIG.get(c, 0)) for c in b))
    if not any(c in CN_UNIT or c in CN_BIG for c in tok):
        return float("".join(str(CN_DIG[c]) for c in tok))       # 二〇二二, 一九九一
    total, section, num = 0.0, 0.0, 0
    for c in tok:
        if c in CN_DIG: num = CN_DIG[c]
        elif c in CN_UNIT: section += (num or 1) * CN_UNIT[c]; num = 0
        elif c in CN_BIG: total += (section + num) * CN_BIG[c]; section, num = 0.0, 0
    return total + section + num


def script_numbers(text):
    vals = set()
    chars = "".join(CN_DIG) + "".join(CN_UNIT) + "".join(CN_BIG) + "點"
    for m in re.finditer(f"[{chars}]+", text):
        tok = m.group()
        if tok in ("萬", "億", "兆", "千", "百", "點"): continue
        try: v = cn_value(tok)
        except (KeyError, ValueError): continue
        vals.add(v)
        nxt = text[m.end(): m.end() + 2]
        if nxt[:1] == "成":                        # 三成 = 30 %, 三成六 = 36 %
            tail = re.match(f"成([{''.join(CN_DIG)}])", nxt + text[m.end() + 2: m.end() + 3])
            vals.add(v * 10 + (CN_DIG[tail.group(1)] if tail else 0)); vals.add(v * 10)
        if text[m.start() - 3: m.start()] == "百分之": vals.add(v)
        for k, bv in CN_BIG.items():               # 三億五千萬 also counts as 3.5 億
            if k in tok: vals.add(v / bv)
        pre = text[max(0, m.start() - 4): m.start()]
        if "分之" in text[m.end(): m.end() + 2] or pre.endswith("分之"): vals.add(v)
    for m in re.finditer(r"\d+(?:\.\d+)?", text): vals.add(float(m.group()))
    return vals


def card_numbers(s):
    out = []
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*([萬億兆]?)", s):
        v = float(m.group(1).replace(",", "")); out.append((m.group(), v, v * CN_BIG.get(m.group(2), 1) if m.group(2) else v))
    return out


def check_card(item, script_text):
    vals = script_numbers(script_text); bad = []
    for field in ("top", "value", "label"):
        for raw, v, full in card_numbers(item.get(field, "")):
            if not any(abs(x - v) < 1e-6 or abs(x - full) < 1e-6 for x in vals): bad.append(raw)
    return bad


# ---------------------------------------------------------------- drawing
def cover_bg(path, w, h, blur=4, dark=0.62):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    x = (im.width - w) // 2; y = (im.height - h) // 2
    im = im.crop((x, y, x + w, y + h))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return Image.blend(im, Image.new("RGB", (w, h), (8, 10, 22)), dark).convert("RGBA")


def tw(d, s, f): return d.textlength(s, font=f)


def fit_font(d, s, weight, size, maxw, minsize=40):
    while size > minsize and tw(d, s, noto(weight, size)) > maxw: size -= 4
    return noto(weight, size)


def centered(d, y, s, f, fill, stroke=0, cx=W / 2):
    d.text((cx - tw(d, s, f) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))


def red_box(d, y, s, f, cx=W / 2, pad_x=40, pad_y=20):
    w = tw(d, s, f); bb = d.textbbox((0, 0), s, font=f); th = bb[3] - bb[1]
    x = cx - w / 2
    d.rectangle((x - pad_x, y, x + w + pad_x, y + th + 2 * pad_y), fill=RED)
    d.text((x, y + pad_y - bb[1]), s, font=f, fill=WHITE)
    return y + th + 2 * pad_y


def source_tag(d, s):
    if not s: return
    f = noto("Medium", 30)
    d.text((W - 90 - tw(d, s, f), 712), s, font=f, fill=DIM)


def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def number_card(it):
    im = layer(); d = ImageDraw.Draw(im)
    top, val, lab = it.get("top", ""), it["value"], it.get("label", "")
    fv = fit_font(d, val, "Black", 150, 1640)
    hv = d.textbbox((0, 0), val, font=fv); hv = hv[3] - hv[1] + 40
    block = (100 if top else 0) + hv + (80 if lab else 0)
    y = 150 + (560 - block) / 2
    if top:
        centered(d, y, top, fit_font(d, top, "Black", 76, 1640), WHITE, stroke=3); y += 112
    y = red_box(d, y, val, fv)
    if lab: centered(d, y + 26, lab, fit_font(d, lab, "Bold", 46, 1640), GREY)
    source_tag(d, ("引用：" + it["source"]) if it.get("source") else "")
    return im


def figure_card(it, vdir):
    im = layer(); d = ImageDraw.Draw(im)
    fig = Image.open(vdir / it["image"]).convert("RGBA")
    box_w, box_h = 1720, 520
    s = min(box_w / fig.width, box_h / fig.height)
    fig = fig.resize((int(fig.width * s), int(fig.height * s)), Image.LANCZOS)
    x = (W - fig.width) // 2; y = 160 + (520 - fig.height) // 2
    pad = 18
    d.rounded_rectangle((x - pad, y - pad, x + fig.width + pad, y + fig.height + pad), 16, fill=(240, 242, 236, 255))
    im.alpha_composite(fig, (x, y))
    if it.get("caption"): centered(d, y - pad - 62, it["caption"], noto("Bold", 40), GREY)
    source_tag(d, ("引用：" + it["source"]) if it.get("source") else "")
    it["_scale"] = round(s, 3)
    return im


def title_card(kicker, title, sub=""):
    im = layer(); d = ImageDraw.Draw(im)
    f = fit_font(d, title, "Black", 104, 1640)
    y = 300
    if kicker: centered(d, y - 90, kicker, noto("Bold", 44), DIM)
    centered(d, y, title, f, WHITE, stroke=3)
    bb = d.textbbox((0, 0), title, font=f)
    d.rectangle((W / 2 - 70, y + bb[3] + 30, W / 2 + 70, y + bb[3] + 40), fill=RED)
    if sub: centered(d, y + bb[3] + 80, sub, fit_font(d, sub, "Bold", 48, 1640), GREY)
    return im


def ident_card(ep_label, title):
    im = layer(); d = ImageDraw.Draw(im)
    f = wenkai(150); s = "深夜 Debug"
    x = (W - tw(d, s, f)) / 2 + 40
    d.ellipse((x - 100, 330, x - 44, 386), fill=RED)
    d.text((x, 270), s, font=f, fill=WHITE)
    centered(d, 480, "Debug After Dark", noto("Medium", 44), DIM)
    centered(d, 590, f"{ep_label}　{title}", fit_font(d, f"{ep_label}　{title}", "Bold", 48, 1640), GREY)
    return im


def end_card(lines):
    im = layer(); d = ImageDraw.Draw(im)
    y = 260
    centered(d, y, lines[0], noto("Black", 96), WHITE); y += 150
    y = red_box(d, y, lines[1], noto("Black", 96))
    for s in lines[2:]:
        centered(d, y + 50, s, fit_font(d, s, "Bold", 48, 1640), GREY); y += 80
    return im


def header(chapter):
    im = layer(); d = ImageDraw.Draw(im)
    d.ellipse((72, 58, 100, 86), fill=RED)
    d.text((118, 40), "深夜 Debug", font=wenkai(50), fill=(235, 235, 240, 255))
    if chapter:
        f = fit_font(d, chapter, "Medium", 34, 1100, 24)
        d.text((W - 80 - tw(d, chapter, f), 52), chapter, font=f, fill=DIM)
    return im


def sub_layer(lines):
    im = layer(); d = ImageDraw.Draw(im)
    f = noto("Black", 66)
    y = 1000 - 92 * len(lines)
    for ln in lines:
        centered(d, y, ln, f, WHITE, stroke=7); y += 92
    return im


def thumbnail(bg_path, white, red, out):
    w, h = 1280, 720
    im = cover_bg(bg_path, w, h, blur=0, dark=0.35)
    g = np.linspace(1, 0, w)[None, :, None] ** 1.4
    a = np.asarray(im).astype(np.float32)
    a[..., :3] = a[..., :3] * (1 - 0.65 * g) + np.array([6, 7, 16]) * 0.65 * g
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    d.ellipse((60, 58, 84, 82), fill=RED)
    d.text((96, 40), "深夜 Debug", font=wenkai(44), fill=(235, 235, 240, 255))
    fw = noto("Black", 170)
    while tw(d, white, fw) > 1150 and fw.size > 80: fw = noto("Black", fw.size - 6)
    fr = noto("Black", 150)
    while tw(d, red, fr) > 1090 and fr.size > 70: fr = noto("Black", fr.size - 6)
    bw = d.textbbox((0, 0), white, font=fw); br = d.textbbox((0, 0), red, font=fr)
    hw, hr = bw[3] - bw[1], br[3] - br[1]
    y_red = h - 70 - (hr + 44); y_white = y_red - 36 - hw
    d.text((70, y_white - bw[1]), white, font=fw, fill=WHITE, stroke_width=4, stroke_fill=(0, 0, 0, 255))
    d.rectangle((64, y_red, 64 + tw(d, red, fr) + 52, y_red + hr + 44), fill=RED)
    d.text((90, y_red + 22 - br[1]), red, font=fr, fill=WHITE)
    im.convert("RGB").save(out, optimize=True)


# ---------------------------------------------------------------- figures
CAPTURE_JS = r"""
const {chromium}=require('playwright');
(async()=>{const [url,out]=process.argv.slice(2);const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1280,height:900},deviceScaleFactor:2});
await p.goto(url,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);
const els=await p.$$('figure, svg, table, canvas');let n=0;const rows=[];
for(const e of els){const bb=await e.boundingBox();if(!bb||bb.width<200||bb.height<100)continue;
 if(await e.evaluate(x=>!!x.parentElement.closest('figure')))continue;
 n++;const f=`fig${String(n).padStart(2,'0')}.png`;await e.screenshot({path:`${out}/${f}`});
 rows.push({file:f,tag:await e.evaluate(x=>x.tagName.toLowerCase()),w:bb.width,h:bb.height,
  text:(await e.innerText()).slice(0,200)});}
console.log(JSON.stringify(rows));await b.close();})();
"""


def capture_figures(ep, vdir):
    url = ep.get("source_url") or f"https://imitator.ai-apps.work/r/{ep['report_slug']}"
    out = vdir / "visuals"; out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "cap.js"; js.write_text(CAPTURE_JS)
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        r = subprocess.run(["node", str(js), url, str(out)], capture_output=True, text=True, env={**os.environ, "NODE_PATH": root})
    if r.returncode: print(r.stderr[-2000:]); return None
    rows = json.loads(r.stdout.strip().splitlines()[-1])
    (out / "figures.json").write_text(json.dumps({"url": url, "figures": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


# ---------------------------------------------------------------- chapters
def mmss(s):
    s = int(s + 1e-6); return f"{s // 60:02d}:{s % 60:02d}"


def description_chapters(desc):
    return [m.group(2).strip() for m in re.finditer(r"^(\d{2}:\d{2}) (.+)$", desc, re.M)]


def skeleton(ep_dir, ep, script):
    ids = [s["id"] for s in script["segments"]]
    names = description_chapters(ep.get("description", ""))
    if len(names) != len(ids): names = ids
    segs = []
    for s, name in zip(script["segments"], names):
        items = []
        txt = clean(s["text"])
        for sent in re.split(r"(?<=[。？！])", txt):
            if re.search(r"[0-9〇一二兩三四五六七八九十百千萬億兆]{2,}|\d", sent):
                items.append({"type": "number", "anchor": sent.strip()[:20], "top": "", "value": "TODO", "label": "", "source": ""})
        segs.append({"id": s["id"], "chapter": name, "items": items})
    rep = re.search(r"原文：〈(.+?)〉", ep.get("description", ""))
    return {"report_label": f"〈{rep.group(1)}〉" if rep else "", "segments": segs,
            "end_card": ["原文與來源在說明欄", "深夜 Debug", "每集十分鐘，把一篇深度文章講成聽得懂的版本"]}


# ---------------------------------------------------------------- main render
def render(ep_dir, out_dir, args):
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    script = json.loads((ep_dir / "script.json").read_text(encoding="utf-8"))
    vdir = ep_dir / "video"; vis = json.loads((vdir / "visuals.json").read_text(encoding="utf-8"))
    name = ep_dir.name; mp3 = ep_dir / ep["audio"]["file"]
    segs = script["segments"]; ids = [s["id"] for s in segs]
    vseg = {s["id"]: s for s in vis["segments"]}
    phr = phrases_for(ep_dir, ids)
    S, E, info, bounds = timeline(ep_dir, mp3, ids, phr)
    mp3_len = info["total"]; vid_len = mp3_len - TRIM
    log = {"episode": name, "trim_start_s": TRIM, "trim_note": "sting 3.2 s + lead 0.4 s removed with atrim; rest of the audio untouched",
           "boundaries": bounds, "checks": {}}

    # ---- subtitles
    cues, ctimes = [], {}
    for k, s in enumerate(segs):
        txt, times, knots = char_times(s["text"], phr[s["id"]], S[s["id"]], E[s["id"]])
        ctimes[s["id"]] = (txt, times)
        for c in cues_for(txt, times):
            c["seg"] = s["id"]; cues.append(c)
    for i, c in enumerate(cues):
        nxt = cues[i + 1] if i + 1 < len(cues) else None
        segend = E[c["seg"]]
        c["end"] = min(nxt["t"], segend + 0.2) if nxt and nxt["seg"] == c["seg"] else segend + 0.2
        c["end"] = max(c["end"], c["t"] + 0.5)
    for c in cues: c["vt"], c["vend"] = c["t"] - TRIM, c["end"] - TRIM

    # ---- chapters (video time)
    chap = []
    for k, sid in enumerate(ids):
        t = 0.0 if k == 0 else (info["ident_at"] - TRIM if k == 1 else S[sid] - TRIM)
        chap.append((t, vseg.get(sid, {}).get("chapter", sid)))

    # ---- visual events (video time): (t, key)
    layers, events = {}, []
    report = vis.get("report_label", "")
    card_rows = []
    for k, s in enumerate(segs):
        sid = s["id"]; v = vseg.get(sid, {"items": []})
        txt, times = ctimes[sid]
        st, en = S[sid] - TRIM, E[sid] - TRIM
        tkey = f"title:{sid}"
        layers[tkey] = title_card(f"第 {k + 1} 段" if k else "", v.get("chapter", sid))
        if k: events.append((st, tkey, True))            # chapter card
        floor = st + (CHAPTER_CARD if k else 0)
        for j, it in enumerate(v.get("items", [])):
            anchor = it.get("anchor", "")
            pos = txt.find(anchor) if anchor else 0
            if pos < 0: print(f"  anchor not found in {sid}: {anchor}"); pos = 0
            t = max(float(times[pos]) - TRIM, floor) if (k or pos) else 0.0
            key = f"{sid}:{j}"
            if it["type"] == "number":
                if it.get("source") == "report": it = {**it, "source": report}
                layers[key] = number_card(it)
                bad = check_card(it, clean(s["text"]))
                card_rows.append({"seg": sid, "value": it["value"], "t": round(t, 2), "source": it.get("source", ""),
                                  "numbers_not_in_script": bad})
            elif it["type"] == "figure":
                if it.get("source") == "report": it = {**it, "source": report}
                layers[key] = figure_card(it, vdir)
                card_rows.append({"seg": sid, "figure": it["image"], "t": round(t, 2), "source": it.get("source", ""),
                                  "scale": it["_scale"]})
            elif it["type"] == "title":
                layers[key] = title_card(it.get("top", ""), it["value"], it.get("label", ""))
            events.append((t, key, False))
        if k == 0:
            layers["ident"] = ident_card(f"EP{ep['number']:02d}", ep["title"].split(" ", 1)[-1])
            events.append((info["ident_at"] - TRIM - 0.3, "ident", False))
    layers["end"] = end_card(vis.get("end_card", ["原文與來源在說明欄", "深夜 Debug"]))
    events.append((E[ids[-1]] - TRIM + 0.3, "end", False))
    events.sort(key=lambda e: e[0])
    # chapter cards last CHAPTER_CARD seconds, then fall back to the item that was active, or the title card
    timeline_ev = []
    for t, key, is_chap in events:
        timeline_ev.append((t, key))
        if is_chap:
            sid = key.split(":", 1)[1]
            later = [e for e in events if e[0] > t and not e[2]]
            if not later or later[0][0] > t + CHAPTER_CARD:
                timeline_ev.append((t + CHAPTER_CARD, key))    # stays as title card until the first item
    timeline_ev.sort(key=lambda e: e[0])
    t_arr = np.array([e[0] for e in timeline_ev]); k_arr = [e[1] for e in timeline_ev]

    def card_at(t):
        i = int(np.searchsorted(t_arr, t, side="right")) - 1
        if i < 0: return k_arr[0], None, 9.0
        prev = k_arr[i - 1] if i > 0 else None
        return k_arr[i], prev, t - t_arr[i]

    chap_t = np.array([c[0] for c in chap])
    headers = {c[1]: header(c[1]) for c in chap}
    subs = {}
    cue_t = np.array([c["vt"] for c in cues])
    BG = cover_bg(ROOT / vis.get("background", "show/art/banner-v2-0-2400.jpg"), W, H)
    blank = layer()

    def frame(t):
        cur, prev, dt = card_at(t)
        steps = int(FADE * FPS)
        a = 1.0 if (dt >= FADE or prev is None or prev == cur) else round(dt / FADE * steps) / steps
        ci = int(np.searchsorted(cue_t, t, side="right")) - 1
        sub = ci if ci >= 0 and t < cues[ci]["vend"] else -1
        hi = int(np.searchsorted(chap_t, t, side="right")) - 1
        hname = chap[max(hi, 0)][1] if cur != "end" else ""
        return (cur, prev if a < 1 else None, a, sub, hname)

    cache_key, cache_bytes = None, None
    lay_cache = {}

    def compose(key):
        cur, prev, a, sub, hname = key
        im = BG.copy()
        if prev is not None:
            im.alpha_composite(Image.blend(blank, layers[prev], 1 - a))
            im.alpha_composite(Image.blend(blank, layers[cur], a))
        else:
            im.alpha_composite(layers[cur])
        if hname: im.alpha_composite(headers[hname])
        if sub >= 0:
            if sub not in subs: subs[sub] = sub_layer(cues[sub]["lines"])
            im.alpha_composite(subs[sub])
        return im.convert("RGB")

    out_dir.mkdir(parents=True, exist_ok=True)
    mp4 = out_dir / f"{name}.mp4"
    n = int(round(vid_len * FPS))
    preview_t = vis.get("preview_times") or [0.0]
    pdir = out_dir / "preview"; pdir.mkdir(exist_ok=True)
    want = {int(round(t * FPS)): f"{i + 1:02d}-{t:06.1f}s" for i, t in enumerate(preview_t)}
    blackish = 0; max_black = 0
    if args.no_video:
        for fi, nm in want.items(): compose(frame(fi / FPS)).save(pdir / f"{nm}.jpg", quality=88)
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-i", str(mp3), "-filter_complex", f"[1:a]atrim=start={TRIM},asetpts=PTS-STARTPTS[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", args.preset, "-crf", "20", "-tune", "stillimage",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(mp4)]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            key = frame(i / FPS)
            if key != cache_key:
                img = compose(key); cache_key, cache_bytes = key, img.tobytes()
                lum = float(np.asarray(img.convert("L"), dtype=np.float32).std())
                blackish = blackish + 1 if lum < 4 else 0
            else:
                blackish = blackish + 1 if blackish else 0
            max_black = max(max_black, blackish)
            ff.stdin.write(cache_bytes)
            if i in want:
                Image.frombytes("RGB", (W, H), cache_bytes).save(pdir / f"{want[i]}.jpg", quality=88)
            if i % (FPS * 60) == 0: print(f"  {i / FPS / 60:.0f} min", flush=True)
        ff.stdin.close()
        if ff.wait(): sys.exit("ffmpeg failed")

    # ---- write text outputs
    def ts(x):
        ms = int(round(max(x, 0) * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = "".join(f"{i + 1}\n{ts(c['vt'])} --> {ts(c['vend'])}\n" + "\n".join(c["lines"]) + "\n\n" for i, c in enumerate(cues))
    (vdir / f"{name}.srt").write_text(srt, encoding="utf-8")
    (out_dir / f"{name}.srt").write_text(srt, encoding="utf-8")
    chtxt = "".join(f"{mmss(t)} {nm}\n" for t, nm in chap)
    (vdir / "chapters.txt").write_text(chtxt, encoding="utf-8"); (out_dir / "chapters.txt").write_text(chtxt, encoding="utf-8")
    pairs = ep.get("youtube", {}).get("thumbnail", [])
    for suf, (wt, rd) in zip("ab", pairs):
        thumbnail(ROOT / "show/art/banner-v2-0-2400.jpg", wt, rd, vdir / f"thumbnail-{suf}.png")
        Image.open(vdir / f"thumbnail-{suf}.png").save(out_dir / f"thumbnail-{suf}.png")

    # ---- acceptance
    C = log["checks"]
    C["boundaries"] = {"pass": all(r["error_s"] <= 0.15 for r in bounds), "max_error_s": max(r["error_s"] for r in bounds),
                       "rule": "each segment start sits at the end of a >= 0.6 s silence (gap) within 0.15 s; ident by cross-correlation"}
    ons = info["onsets"]
    sync_pick = {"開頭": 0, "結尾": len(cues) - 1,
                 "數字句": next(i for i, c in enumerate(cues) if re.search(r"[一二三四五六七八九十百千]{2,}|\d", "".join(c["lines"])) and i > 3),
                 "固定開場後第一句": next(i for i, c in enumerate(cues) if c["seg"] == ids[1]),
                 "最後一段中間": [i for i, c in enumerate(cues) if c["seg"] == ids[-1]][len([c for c in cues if c["seg"] == ids[-1]]) // 2]}
    rows = []
    for nm, i in sync_pick.items():
        t = cues[i]["t"]; near = float(ons[np.argmin(np.abs(ons - t))])
        rows.append({"point": nm, "cue": "／".join(cues[i]["lines"]), "video_t": round(t - TRIM, 2),
                     "speech_onset_video_t": round(near - TRIM, 2), "error_s": round(abs(near - t), 2)})
    C["subtitle_sync"] = {"pass": all(r["error_s"] <= 0.3 for r in rows), "points": rows}
    sub_all = "".join("".join(c["lines"]) for c in cues)
    scr_all = "".join(clean(s["text"]) for s in segs)
    same = norm_chars(sub_all) == norm_chars(scr_all)
    over = [c["lines"] for c in cues if len(c["lines"]) > MAX_LINES or any(text_width(l) > LINE_CHARS for l in c["lines"])]
    C["subtitle_text"] = {"pass": same and not over, "identical_to_script": same, "cues": len(cues), "too_long": over}
    if not args.no_video:
        vd = duration(mp4)
        C["length"] = {"pass": abs(vd - vid_len) <= 0.1, "video_s": round(vd, 3), "mp3_minus_trim_s": round(vid_len, 3)}
        def lufs(p):
            o = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-map", "0:a", "-af", "ebur128", "-f", "null", "-"],
                               capture_output=True, text=True).stderr
            return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
        lm, lv = lufs(mp3), lufs(mp4)
        C["loudness"] = {"pass": abs(lm - lv) <= 0.5, "mp3_lufs": lm, "video_lufs": lv}
        bd = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-map", "0:v", "-vf", "blackdetect=d=1:pix_th=0.05", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        blacks = re.findall(r"black_start:\S+ black_end:\S+", bd)
        C["picture"] = {"pass": not blacks and max_black < FPS, "black_over_1s": blacks, "first_frame": k_arr[0],
                        "first_frame_is_cover": k_arr[0].startswith("title")}
        log["mp4"] = {"file": mp4.name, "bytes": mp4.stat().st_size, "sha256": hashlib.sha256(mp4.read_bytes()).hexdigest(),
                      "frames": n, "fps": FPS, "size": f"{W}x{H}"}
    lens = [chap[i + 1][0] - chap[i][0] for i in range(len(chap) - 1)] + [vid_len - chap[-1][0]]
    C["chapters"] = {"pass": chap[0][0] == 0 and len(chap) >= 3 and min(lens) >= 10, "count": len(chap), "shortest_s": round(min(lens), 1),
                     "ident": "merged into chapter 2 (starts at the ident)"}
    nums = [r for r in card_rows if "value" in r]
    C["number_cards"] = {"pass": all(not r["numbers_not_in_script"] and r["source"] for r in nums), "count": len(nums),
                         "problems": [r for r in nums if r["numbers_not_in_script"] or not r["source"]]}
    figs = [r for r in card_rows if "figure" in r]
    C["figures"] = {"count": len(figs), "rows": figs, "note": vis.get("figures_note", "")}
    log["cards"] = card_rows
    log["chapters"] = [{"t": round(t, 2), "name": nm} for t, nm in chap]
    (vdir / "render_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in C.items(): print(f"{k:15s} {'PASS' if v.get('pass', True) else 'FAIL'}")
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep_dir")
    ap.add_argument("--out", help="where the mp4, srt, chapters, thumbnails and previews go (default episodes/<ep>/video/out)")
    ap.add_argument("--skeleton", action="store_true")
    ap.add_argument("--capture-figures", action="store_true")
    ap.add_argument("--thumbnail-only", action="store_true")
    ap.add_argument("--no-video", action="store_true", help="everything except the mp4 (fast check of subtitles and cards)")
    ap.add_argument("--preset", default="medium")
    a = ap.parse_args()
    ep_dir = Path(a.ep_dir).resolve(); vdir = ep_dir / "video"; vdir.mkdir(exist_ok=True)
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    if a.thumbnail_only:
        for suf, (wt, rd) in zip("ab", ep.get("youtube", {}).get("thumbnail", [])):
            thumbnail(ROOT / "show/art/banner-v2-0-2400.jpg", wt, rd, vdir / f"thumbnail-{suf}.png"); print(vdir / f"thumbnail-{suf}.png")
        return
    if a.skeleton:
        p = vdir / "visuals.json"
        if p.exists(): sys.exit(f"{p} exists; not overwriting")
        script = json.loads((ep_dir / "script.json").read_text(encoding="utf-8"))
        p.write_text(json.dumps(skeleton(ep_dir, ep, script), ensure_ascii=False, indent=1), encoding="utf-8"); print(p); return
    if a.capture_figures:
        rows = capture_figures(ep, vdir)
        print(json.dumps(rows, ensure_ascii=False, indent=1) if rows is not None else "capture failed: use number cards only")
        return
    render(ep_dir, Path(a.out) if a.out else vdir / "out", a)


if __name__ == "__main__":
    main()
