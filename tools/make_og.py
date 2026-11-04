"""Render the link-preview image (Open Graph / Twitter card) from show/og/og.html: 1200x630 JPEG at show/og/og-1200x630.jpg.

  python3 tools/make_og.py
Uses the site's banner and typefaces so a shared link looks like the site header. Needs Playwright (pre-installed here).
"""
import subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
html, png, jpg = ROOT / "show/og/og.html", ROOT / "out/og.png", ROOT / "show/og/og-1200x630.jpg"
png.parent.mkdir(exist_ok=True)
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1200,height:630}}}});
await p.goto('file://{html}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);await p.screenshot({{path:'{png}'}});await b.close();}})()"""
subprocess.run(["node", "-e", js], check=True)
Image.open(png).convert("RGB").save(jpg, "JPEG", quality=88, optimize=True)
print(jpg)
