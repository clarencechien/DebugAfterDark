"""Show artwork with Gemini image generation (cover candidates and the site banner).

  python3 tools/gen_art.py cover   [--n 3]      # square, 4K, resized to 3000x3000 RGB JPEG
  python3 tools/gen_art.py banner               # 16:9 header for the podcast site
Every image is saved under show/art/ with a JSON sidecar: model, prompt, prompt sha256, size. The chosen cover is copied
to show/cover-3000.jpg by hand after review; tools/make_cover.py remains as a code-drawn fallback.
Brief: late night, a small lamp left on, a terminal with a red breakpoint dot. No faces (the host is an AI character),
no real logos or brands, readable as a ~200 px thumbnail.
"""
import argparse, hashlib, io, json, os
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "show" / "art"
MODEL = "gemini-3-pro-image"

BASE = ("A podcast cover artwork for a late-night technology podcast for software engineers in Taiwan. "
        "Scene: a quiet desk at about 1:30 a.m., seen from slightly above. A small warm desk lamp is the only warm light. "
        "A laptop screen glows cool blue with a few lines of terminal text, and one bright red breakpoint dot in the code gutter "
        "is the focal point. A mug of water, a window with a soft, out-of-focus city at night and a thin crescent moon. "
        "Mood: calm, intimate, a little nostalgic, cozy rather than gloomy. Style: clean modern flat illustration with subtle grain, "
        "deep navy and indigo palette with warm amber lamp light and a single red accent. Strong, simple composition with large "
        "shapes so it still reads at thumbnail size. No people, no faces, no hands, no real brand logos, no watermark.")

COVER_PROMPTS = [
    BASE + " Typography: the title 深夜 Debug in large, bold, clean traditional Chinese and Latin letters across the lower third, "
           "and a smaller subtitle Debug After Dark underneath. Text must be spelled exactly as given and be highly legible.",
    BASE + " Typography: the title 深夜 Debug set in a large monospaced, terminal-like style near the top, with a small subtitle "
           "Debug After Dark. Text must be spelled exactly as given and be highly legible.",
    BASE + " Leave the lower third as calm dark empty space for a title to be added later. Do not draw any text or letters.",
]
BANNER_PROMPT = (BASE.replace("A podcast cover artwork", "A wide website header illustration")
                 + " Wide panoramic composition, the desk on the right, empty dark space on the left for text. Do not draw any text.")


def generate(prompt, aspect, name, size="4K"):
    c = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ["gemini_key"])
    r = c.models.generate_content(model=MODEL, contents=prompt, config=types.GenerateContentConfig(
        response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size)))
    part = next(p for p in r.candidates[0].content.parts if getattr(p, "inline_data", None))
    img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
    ART.mkdir(parents=True, exist_ok=True)
    raw = ART / f"{name}.png"; img.save(raw)
    meta = {"model": MODEL, "aspect_ratio": aspect, "image_size": size, "prompt": prompt,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "pixels": img.size}
    (ART / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return img, raw


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("what", choices=["cover", "banner"]); ap.add_argument("--n", type=int, default=3)
    a = ap.parse_args()
    if a.what == "cover":
        for k in range(a.n):
            img, raw = generate(COVER_PROMPTS[k % len(COVER_PROMPTS)], "1:1", f"cover-{k}")
            img.resize((3000, 3000), Image.LANCZOS).save(ART / f"cover-{k}-3000.jpg", "JPEG", quality=90, optimize=True)
            print(raw, img.size)
    else:
        img, raw = generate(BANNER_PROMPT, "16:9", "banner")
        img.resize((1920, int(1920 * img.size[1] / img.size[0])), Image.LANCZOS).save(ART / "banner-1920.jpg", "JPEG", quality=85, optimize=True)
        print(raw, img.size)
