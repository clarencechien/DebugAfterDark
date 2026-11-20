#!/usr/bin/env python3
"""Cold open -> 1080x1920 YouTube Short (burned-in subs, cards, end card).

Each Short is described by episodes/<ep>/short.json (see docs/video.md, "Shorts").
All times in short.json are Short time = master mp3 time - audio.start.

  python3 tools/make_short.py <ep-dir> <out-dir>            # render mp4 + srt + preview/
  python3 tools/make_short.py <ep-dir> <out-dir> --previews # only preview jpgs (fast)
  python3 tools/make_short.py <ep-dir> --align [--end 60]   # print word timings of the cold open
                                                            # (faster-whisper, to write cues)
Needs: ffmpeg, Pillow, numpy, fonts-noto-cjk + fonts-noto-cjk-extra (Black/Medium weights).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-{}.ttc"
RED = (229, 40, 46, 255)
WHITE = (255, 255, 255, 255)
GREY = (190, 196, 210, 255)
DIM = (160, 166, 180, 255)
PANEL = (12, 14, 28, 215)
EDGE = (70, 76, 100, 255)
FADE = 0.3


def font(w, size):
    return ImageFont.truetype(FONT.format(w), size, index=3)  # index 3 = Traditional Chinese


def text_w(d, s, f):
    return d.textlength(s, font=f)


def centered(d, y, s, f, fill, stroke=0, sfill=(0, 0, 0, 255)):
    d.text(((W - text_w(d, s, f)) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)


def fit(d, s, weight, size, maxw):
    while size > 40:
        f = font(weight, size)
        if text_w(d, s, f) <= maxw:
            return f
        size -= 4
    return font(weight, size)


def red_box(d, y, s, f, pad_x=36, pad_y=18):
    w = text_w(d, s, f)
    bbox = d.textbbox((0, 0), s, font=f)
    th = bbox[3] - bbox[1]
    x = (W - w) / 2
    d.rectangle((x - pad_x, y, x + w + pad_x, y + th + 2 * pad_y), fill=RED)
    d.text((x, y + pad_y - bbox[1]), s, font=f, fill=WHITE)
    return y + th + 2 * pad_y


def source_line(d, s, y=1000):
    if s:
        f = fit(d, s, "Medium", 30, W - 140)
        d.text((W - 70 - text_w(d, s, f), y), s, font=f, fill=DIM)


# ---------------- card types ----------------

def card_number(c):
    """Big line, red box, grey label. {"top", "box", "label"?, "source"?}"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 440
    centered(d, y, c["top"], fit(d, c["top"], "Black", 120, 940), WHITE, stroke=4)
    y = red_box(d, y + 175, c["box"], fit(d, c["box"], "Black", 170, 880))
    if c.get("label"):
        centered(d, y + 30, c["label"], fit(d, c["label"], "Bold", 52, 960), GREY)
    source_line(d, c.get("source"))
    return im


def card_list(c):
    """Title, subtitle, panel of rows revealed one by one.
    {"title", "subtitle"?, "rows": [[left, right], ...], "shown": n, "source"?}
    right may be "" ; rows beyond `shown` are drawn as left + "？？"."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    centered(d, 330, c["title"], fit(d, c["title"], "Black", 76, 960), WHITE, stroke=3)
    if c.get("subtitle"):
        centered(d, 435, c["subtitle"], fit(d, c["subtitle"], "Bold", 44, 960), GREY)
    rows, shown = c["rows"], c.get("shown", len(c["rows"]))
    x0, x1, y, rh = 110, W - 110, 540, 105
    d.rounded_rectangle((x0 - 20, y - 20, x1 + 20, y + len(rows) * rh + 10), 18, fill=PANEL, outline=EDGE, width=2)
    for i, (left, right) in enumerate(rows):
        yy = y + i * rh
        d.text((x0 + 20, yy + 12), left, font=fit(d, left, "Bold", 54, 600), fill=WHITE)
        s, col = (right, (120, 220, 140, 255)) if i < shown else ("？？", RED)
        if s:
            f = font("Black", 52)
            d.text((x1 - 20 - text_w(d, s, f), yy + 10), s, font=f, fill=col)
        if i < len(rows) - 1:
            d.line((x0, yy + rh - 5, x1, yy + rh - 5), fill=EDGE, width=2)
    source_line(d, c.get("source"))
    return im


def card_choice(c):
    """A question with options revealed one by one (the last shown is red).
    {"title", "options": [...], "shown": n, "source"?}"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    centered(d, 400, c["title"], fit(d, c["title"], "Black", 110, 940), WHITE, stroke=4)
    y = 590
    opts = c["options"][: c.get("shown", len(c["options"]))]
    for i, s in enumerate(opts):
        f = fit(d, s, "Black", 92, 900)
        if i == len(opts) - 1:
            y = red_box(d, y, s, f) + 40
        else:
            bbox = d.textbbox((0, 0), s, font=f)
            th = bbox[3] - bbox[1]
            w = text_w(d, s, f)
            x = (W - w) / 2
            d.rectangle((x - 36, y, x + w + 36, y + th + 36), fill=PANEL, outline=EDGE, width=2)
            d.text((x, y + 18 - bbox[1]), s, font=f, fill=GREY)
            y += th + 36 + 40
    source_line(d, c.get("source"))
    return im


def card_contrast(c):
    """Two claims stacked: grey panel (common belief) vs red panel (the report).
    {"a_label", "a_lines": [...], "b_label", "b_lines": [...], "show_b": bool, "source"?}"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = 90, W - 90

    def panel(y, label, lines, fill, text_fill, label_fill):
        lf = font("Bold", 44)
        tf = [fit(d, s, "Black", 76, x1 - x0 - 80) for s in lines]
        h = 40 + 60 + sum(100 for _ in lines) + 20
        d.rounded_rectangle((x0, y, x1, y + h), 18, fill=fill, outline=EDGE if fill == PANEL else None, width=2)
        d.text((x0 + 40, y + 30), label, font=lf, fill=label_fill)
        yy = y + 100
        for s, f in zip(lines, tf):
            d.text((x0 + 40, yy), s, font=f, fill=text_fill)
            yy += 100
        return y + h

    y = panel(300, c["a_label"], c["a_lines"], PANEL, GREY, DIM)
    if c.get("show_b"):
        centered(d, y + 14, "VS", font("Black", 60), WHITE)
        y = panel(y + 100, c["b_label"], c["b_lines"], RED, WHITE, (255, 225, 225, 255))
    source_line(d, c.get("source"), y=y + 20)
    return im


def card_end(c):
    """{"title", "box", "lines": [...], "cta"}"""
    im = Image.new("RGBA", (W, H), (6, 7, 16, 235))
    d = ImageDraw.Draw(im)
    centered(d, 520, c["title"], font("Black", 110), WHITE)
    y = red_box(d, 700, c["box"], font("Black", 110))
    for i, s in enumerate(c.get("lines", [])):
        centered(d, y + 60 + 80 * i, s, fit(d, s, "Bold", 56, 960), GREY)
    centered(d, y + 60 + 80 * len(c.get("lines", [])) + 70, c["cta"], font("Black", 64), WHITE)
    return im


CARD = {"number": card_number, "list": card_list, "choice": card_choice, "contrast": card_contrast}


def header(label):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((70, 168, 98, 196), fill=RED)
    d.text((116, 150), "深夜 Debug", font=font("Medium", 50), fill=(235, 235, 240, 255))
    f = font("Medium", 36)
    d.text((W - 70 - text_w(d, label, f), 160), label, font=f, fill=(170, 175, 190, 255))
    return im


def sub_layer(text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = text.split("\n")
    assert len(lines) <= 2, text
    f = font("Black", 72)
    for ln in lines:
        assert text_w(d, ln, f) <= 980, f"subtitle line too wide: {ln}"
    y = 1180
    for ln in lines:
        centered(d, y, ln, f, WHITE, stroke=7)
        y += 100
    return im


def background(total, art):
    """Right part of the banner (desk + monitor), blurred and darkened; slow pan."""
    ban = Image.open(art).convert("RGB")
    bw, bh = ban.size
    cw = int(bh * 9 / 16)
    x0 = int(bw * 0.70) - cw // 2
    BGW, BGH = int(W * 1.06), int(H * 1.06)
    bg = ban.crop((x0, 0, x0 + cw, bh)).resize((BGW, BGH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(6))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (8, 10, 22)), 0.55)
    g = np.linspace(0, 1, BGH)[:, None]
    mask = 0.25 + 0.45 * np.exp(-((g - 0.45) ** 2) / 0.06)
    BG = (np.asarray(bg).astype(np.float32) * (1 - mask[..., None])).clip(0, 255).astype(np.uint8)

    def at(t):
        ox = int((BGW - W) * (0.2 + 0.6 * t / total))
        oy = int((BGH - H) * 0.5)
        return Image.fromarray(BG[oy:oy + H, ox:ox + W]).convert("RGBA")
    return at


def align(ep_dir, end):
    """Print word timings of the master mp3 from 0 to `end` s (master time), to write cues."""
    import wave
    from faster_whisper import WhisperModel
    mp3 = mp3_of(ep_dir)
    tmp = "/tmp/_short_align.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(end), "-i", mp3, "-ar", "16000", "-ac", "1", tmp], check=True)
    w = wave.open(tmp)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    script = json.load(open(f"{ep_dir}/script.json"))
    first = script["segments"][0]["text"][:40]
    segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe(
        a, language="zh", word_timestamps=True, initial_prompt=first)
    print("master-mp3 time; Short time = master - audio.start")
    for s in segs:
        print(f"[{s.start:6.2f}-{s.end:6.2f}] " + " ".join(f"{x.word}@{x.start:.2f}" for x in s.words))
    print("\nsilences (-40 dB, >=0.25 s):")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-t", str(end), "-i", mp3, "-af", "silencedetect=n=-40dB:d=0.25", "-f", "null", "-"],
                       capture_output=True, text=True)
    print("\n".join(l.split("] ")[-1] for l in r.stderr.splitlines() if "silence_" in l))


def mp3_of(ep_dir):
    ep = json.load(open(f"{ep_dir}/episode.json"))
    return f"{ep_dir}/{ep['audio']['file']}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ep_dir = os.path.abspath(args[0])
    if "--align" in sys.argv:
        end = float(sys.argv[sys.argv.index("--end") + 1]) if "--end" in sys.argv else 70
        return align(ep_dir, end)
    out = args[1]
    only_previews = "--previews" in sys.argv
    os.makedirs(out, exist_ok=True)
    cfg = json.load(open(f"{ep_dir}/short.json"))
    name = cfg.get("name", f"{os.path.basename(ep_dir).split('-')[0]}-short")

    a0, a1 = cfg["audio"]["start"], cfg["audio"]["end"]
    speech = a1 - a0
    endcard = cfg.get("endcard_s", 2.0)
    total = speech + endcard
    bg_at = background(total, f"{REPO}/{cfg.get('background', 'show/art/banner-v2-0-2400.jpg')}")

    cards = []  # (start, layer, key)
    for i, c in enumerate(cfg["cards"]):
        cards.append((c["at"], CARD[c["type"]](c), c.get("group", i)))
    end_layer = card_end(cfg["end"])
    cards.append((speech, end_layer, "END"))
    cards.sort(key=lambda x: x[0])
    hdr = header(cfg["label"])
    cues = cfg["cues"]
    cue_end = cfg["cue_end"]
    subs = [(s, cues[i + 1][0] if i + 1 < len(cues) else cue_end, sub_layer(t), t) for i, (s, t) in enumerate(cues)]
    empty = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def frame(t):
        im = bg_at(t)
        cur = prev = None
        start = 0
        for s, lay, g in cards:
            if t >= s:
                prev, cur, start = cur, (lay, g), s
        dt = t - start
        same_group = prev and cur and prev[1] == cur[1]  # reveal steps of one card: no fade
        a = 1.0 if (dt >= FADE or t < FADE or same_group) else dt / FADE
        if prev and a < 1:
            im = Image.alpha_composite(im, Image.blend(empty, prev[0], 1 - a))
        im = Image.alpha_composite(im, cur[0] if a >= 1 else Image.blend(empty, cur[0], a))
        if t < speech:
            im = Image.alpha_composite(im, hdr)
            for s, e, L, _ in subs:
                if s <= t < e:
                    im = Image.alpha_composite(im, L)
            ImageDraw.Draw(im).rectangle((0, H - 8, int(W * t / speech), H), fill=RED)
        return im.convert("RGB")

    pdir = f"{out}/preview"
    os.makedirs(pdir, exist_ok=True)
    previews = {float(k): v for k, v in cfg.get("previews", {}).items()}
    previews.setdefault(0.0, "00-first-frame")
    previews.setdefault(round(speech + 1.0, 2), "99-end-card")
    if only_previews:
        for t, nm in previews.items():
            frame(t).resize((540, 960), Image.LANCZOS).save(f"{pdir}/{nm}.jpg", quality=88)
        print("previews ->", pdir)
        return

    wav = f"{out}/_audio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a0), "-to", str(a1), "-i", mp3_of(ep_dir),
                    "-af", f"apad=pad_dur={endcard}", "-ar", "48000", wav], check=True)
    mp4 = f"{out}/{name}.mp4"
    n = int(round(total * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    pts = {int(round(k * FPS)): v for k, v in previews.items()}
    for i in range(n):
        fr = frame(i / FPS)
        ff.stdin.write(fr.tobytes())
        if i in pts:
            fr.resize((540, 960), Image.LANCZOS).save(f"{pdir}/{pts[i]}.jpg", quality=88)
    ff.stdin.close()
    ff.wait()
    os.remove(wav)

    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(f"{out}/{name}.srt", "w") as fh:
        for i, (s, e, _, t) in enumerate(subs):
            fh.write(f"{i + 1}\n{ts(s)} --> {ts(e)}\n{t}\n\n")
    print(f"{mp4}: {n} frames, {total:.2f} s")


if __name__ == "__main__":
    main()
