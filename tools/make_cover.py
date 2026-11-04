"""Placeholder show cover, 3000x3000 RGB JPEG with no alpha (Apple's requirement), drawn from code.

  python3 tools/make_cover.py [--out show/cover-3000.jpg]
Needs a CJK font; WenQuanYi Zen Hei is used if present. Replace with a designed cover before submitting to directories.
"""
import argparse, math, random
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="show/cover-3000.jpg"); a = ap.parse_args()
S = 3000; img = Image.new("RGB", (S, S), (12, 14, 22)); d = ImageDraw.Draw(img)
for y in range(S):                                   # night gradient
    t = y / S; d.line([(0, y), (S, y)], fill=(int(12 + 18 * t), int(14 + 10 * t), int(22 + 30 * t)))
rnd = random.Random(20261104)                         # fixed seed: the cover is reproducible
for _ in range(260):
    x, y, r = rnd.randrange(S), rnd.randrange(int(S * 0.55)), rnd.choice([2, 3, 4, 5])
    c = rnd.randrange(120, 230); d.ellipse([x - r, y - r, x + r, y + r], fill=(c, c, c + 15 if c < 240 else 255))
cx, cy = int(S * 0.72), int(S * 0.24)                 # crescent moon
d.ellipse([cx - 230, cy - 230, cx + 230, cy + 230], fill=(236, 226, 190))
d.ellipse([cx - 140, cy - 280, cx + 300, cy + 160], fill=(18, 19, 32))
# a terminal line with a breakpoint dot
d.rounded_rectangle([300, 1640, 2700, 1980], radius=40, fill=(24, 28, 40), outline=(70, 80, 110), width=6)
d.ellipse([380, 1760, 480, 1860], fill=(225, 72, 72))
font = lambda size: ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", size)
d.text((540, 1745), "$ ping --after-dark", font=font(120), fill=(140, 230, 160))
d.text((300, 2150), "深夜 Debug", font=font(420), fill=(245, 242, 232))
d.text((310, 2640), "Debug After Dark", font=font(170), fill=(170, 180, 205))
img.save(a.out, "JPEG", quality=88, optimize=True); print(a.out, img.size, img.mode)
