"""Redraw an episode's report charts in the video's dark palette (docs/video-web.md「每集的配方」step 3).

Report charts are drawn for a light page; pasted into the dark paper theme they glare. So charts are redrawn from the
report's own numbers into 1600x440 PNGs on the page colour. The player shows any figure named chart-*.png without the
white frame it puts around captured report screenshots.

  python3 tools/webvideo/make_charts.py episodes/<ep>     # reads video/charts.json, writes video/visuals/<file>

video/charts.json: {"charts": [{"file": "chart-x.png", "kind": "hbars|stacked|lines|table", "title": "...", "sub": "...", ...}]}
  hbars   : rows [[label, value, colour]], unit, fmt ("{:.2f}"), labelw (px), vmax
  stacked : parts [[label, value, colour]], total_label
  lines   : xs [...], series [[name, [values or null], colour]], points [[name, x_index, value, colour]]
  table   : rows [[claim, origin, ok (bool), note]]
colour: "acc" (highlight), "red" (the point of the chart), "dim" (the rest), "blue", or any CSS colour.
Every number must come from the report (or script.json); write the report section in "from" so a reviewer can check.
Needs Node + Playwright and fonts-noto-cjk.
"""
import json, os, subprocess, sys
W, H = 1600, 440
BG, FG, MUTED, GRID, ACC, RED, DIMBAR = '#111318', '#ece6da', '#8a8478', '#2a2d35', '#f2b36f', '#ff7a6b', '#4a4f5a'
FONT = "font-family:'Noto Sans CJK TC',sans-serif"

def wrap(svg):
    return f'<!doctype html><meta charset=utf-8><style>html,body{{margin:0;background:{BG}}}</style><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" style="{FONT}">{svg}</svg>'

def title(t, sub=''):
    s = f'<text x="0" y="44" fill="{FG}" font-size="40" font-weight="700">{t}</text>'
    if sub: s += f'<text x="0" y="84" fill="{MUTED}" font-size="26">{sub}</text>'
    return s

def hbars(t, sub, rows, unit='', fmt='{:g}', labelw=330, top=120, vmax=None):
    vmax = vmax or max(v for _, v, _ in rows)
    n = len(rows); bh = min(56, (H - top - 10) / n - 14); gap = min(30, (H - top - 10 - n * bh) / max(1, n - 1)) if n > 1 else 0
    y_start = top + (H - top - 10 - (n * bh + (n - 1) * gap)) / 2
    s = title(t, sub); x0 = labelw; aw = W - x0 - 220
    for i, (lab, v, col) in enumerate(rows):
        y = y_start + i * (bh + gap)
        w = max(4, aw * v / vmax)
        s += f'<text x="{x0-24}" y="{y+bh*0.68}" fill="{FG}" font-size="32" text-anchor="end">{lab}</text>'
        s += f'<rect x="{x0}" y="{y}" width="{w}" height="{bh}" rx="6" fill="{col}"/>'
        s += f'<text x="{x0+w+18}" y="{y+bh*0.7}" fill="{col if col!=DIMBAR else FG}" font-size="34" font-weight="700">{fmt.format(v)}{unit}</text>'
    return s

def stacked(t, sub, parts, total_label):
    s = title(t, sub); x0, y, h = 0, 170, 110; tot = sum(v for _, v, _ in parts); aw = W - 40
    x = x0
    for lab, v, col in parts:
        w = aw * v / tot
        s += f'<rect x="{x}" y="{y}" width="{w-4}" height="{h}" rx="6" fill="{col}"/>'
        if w > 150:
            s += f'<text x="{x+18}" y="{y+48}" fill="{BG}" font-size="30" font-weight="700">{lab}</text><text x="{x+18}" y="{y+88}" fill="{BG}" font-size="30">{v:,} 元</text>'
        x += w
    # small parts: one legend line under the bar, right-aligned
    small = [(lab, v, col) for lab, v, col in parts if aw * v / tot <= 150]
    lx = W - 40; ly = y + h + 60
    for lab, v, col in reversed(small):
        txt = f'{lab} {v:,}'
        s += f'<text x="{lx}" y="{ly}" fill="{col}" font-size="30" font-weight="700" text-anchor="end">{txt}</text>'
        lx -= 30 * len(txt) * 0.72 + 40
    s += f'<text x="{W-40}" y="{y-24}" fill="{ACC}" font-size="36" font-weight="700" text-anchor="end">{total_label}</text>'
    return s

def lines(t, sub, xs, series, extra_points):
    s = title(t, sub); x0, x1, y0, y1 = 120, W - 360, 120, H - 50
    X = lambda i: x0 + (x1 - x0) * i / (len(xs) - 1); Y = lambda v: y1 - (y1 - y0) * v / 100
    for g in (0, 25, 50, 75, 100):
        s += f'<line x1="{x0}" x2="{x1}" y1="{Y(g)}" y2="{Y(g)}" stroke="{GRID}"/><text x="{x0-16}" y="{Y(g)+9}" fill="{MUTED}" font-size="24" text-anchor="end">{g}%</text>'
    for i, xl in enumerate(xs):
        s += f'<text x="{X(i)}" y="{y1+38}" fill="{MUTED}" font-size="26" text-anchor="middle">{xl}</text>'
    for name, vals, col in series:
        pts = [(X(i), Y(v)) for i, v in enumerate(vals) if v is not None]
        s += f'<polyline points="{" ".join(f"{a},{b}" for a,b in pts)}" fill="none" stroke="{col}" stroke-width="5"/>'
        for a, b in pts: s += f'<circle cx="{a}" cy="{b}" r="9" fill="{col}"/>'
 
        a, b = pts[-1]; b += -14 if vals[-1] >= 45 else 22; s += f'<text x="{a+24}" y="{b+10}" fill="{col}" font-size="30" font-weight="700">{vals[-1]}%  {name}</text>'
    for name, i, v, col in extra_points:
        a, b = X(i), Y(v); s += f'<circle cx="{a}" cy="{b}" r="9" fill="{col}"/><text x="{a+24}" y="{b+10}" fill="{col}" font-size="30" font-weight="700">{v}%  {name}</text>'
    return s

def table(t, sub, rows):
    s = title(t, sub); y = 130; rh = (H - y) / len(rows)
    for i, (a, b, ok, note) in enumerate(rows):
        yy = y + i * rh
        s += f'<text x="0" y="{yy+34}" fill="{FG}" font-size="28">{a}</text>'
        s += f'<text x="500" y="{yy+34}" fill="{MUTED}" font-size="28">→</text>'
        s += f'<text x="550" y="{yy+34}" fill="{FG}" font-size="28">{b}</text>'
        col = '#7fd18b' if ok else RED
        s += f'<text x="1080" y="{yy+34}" fill="{col}" font-size="28" font-weight="700">{"✓" if ok else "✗"} {note}</text>'
        if i < len(rows) - 1: s += f'<line x1="0" x2="{W}" y1="{yy+rh-6}" y2="{yy+rh-6}" stroke="{GRID}"/>'
    return s

COL = {'acc': ACC, 'red': RED, 'dim': DIMBAR, 'blue': '#8fb7d9', 'acc2': '#e8c08a', 'acc3': '#d48a4a'}
c = lambda x: COL.get(x, x)


def draw(ch):
    k = ch['kind']
    if k == 'hbars':
        return hbars(ch['title'], ch.get('sub', ''), [(a, v, c(col)) for a, v, col in ch['rows']], unit=ch.get('unit', ''),
                     fmt=ch.get('fmt', '{:g}'), labelw=ch.get('labelw', 330), vmax=ch.get('vmax'))
    if k == 'stacked':
        return stacked(ch['title'], ch.get('sub', ''), [(a, v, c(col)) for a, v, col in ch['parts']], ch['total_label'])
    if k == 'lines':
        return lines(ch['title'], ch.get('sub', ''), ch['xs'], [(n, v, c(col)) for n, v, col in ch['series']],
                     [(n, i, v, c(col)) for n, i, v, col in ch.get('points', [])])
    if k == 'table':
        return table(ch['title'], ch.get('sub', ''), ch['rows'])
    sys.exit(f'unknown chart kind {k}')


def main():
    ep_dir = os.path.abspath(sys.argv[1])
    vdir = os.path.join(ep_dir, 'video')
    spec = json.load(open(os.path.join(vdir, 'charts.json'), encoding='utf-8'))
    os.makedirs(os.path.join(vdir, 'visuals'), exist_ok=True)
    jobs = []
    for ch in spec['charts']:
        out = os.path.join(vdir, 'visuals', ch['file'])
        html = out[:-4] + '.html'
        open(html, 'w', encoding='utf-8').write(wrap(draw(ch)))
        jobs.append((html, out))
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          "const p=await b.newPage({viewport:{width:%d,height:%d}});for(const [h,o] of %s){await p.goto('file://'+h);"
          "await p.screenshot({path:o});}await b.close();})()") % (W, H, json.dumps(jobs))
    try:
        subprocess.run(['node', '-e', js], check=True)
    finally:
        for h, _ in jobs:
            if os.path.exists(h): os.remove(h)
    for _, o in jobs: print(o)


if __name__ == '__main__':
    main()
