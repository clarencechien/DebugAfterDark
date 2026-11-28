"""Build a timeline.json for the web-page video player from an episode's make_video.py outputs.

Prototype (docs/video-web.md). It reuses what tools/make_video.py already measured, so nothing is
re-timed here: subtitle cues come from video/<ep>.srt, card times and chapters from
video/render_log.json, card text and per-segment backgrounds from video/visuals.json.
Times are video times (mp3 time minus render_log's trim_start_s).

usage: python3 tools/webvideo/build_timeline.py episodes/<ep> [-o timeline.json]  (default episodes/<ep>/video/out/web/, not in git)
"""
import argparse, json, os, re, subprocess, sys


def srt_cues(path):
    def sec(s):
        h, m, rest = s.split(':')
        return int(h) * 3600 + int(m) * 60 + float(rest.replace(',', '.'))
    cues = []
    for block in re.split(r'\n\s*\n', open(path, encoding='utf-8').read().strip()):
        lines = block.strip().split('\n')
        if len(lines) < 3 or '-->' not in lines[1]:
            continue
        a, b = [x.strip() for x in lines[1].split('-->')]
        cues.append({'t0': round(sec(a), 3), 't1': round(sec(b), 3), 'lines': lines[2:]})
    return cues


def mp3_duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ep_dir')
    ap.add_argument('-o', '--out')
    a = ap.parse_args()
    ep_dir = os.path.abspath(a.ep_dir)
    ep = os.path.basename(ep_dir.rstrip('/'))
    vdir = os.path.join(ep_dir, 'video')
    log = json.load(open(os.path.join(vdir, 'render_log.json'), encoding='utf-8'))
    vis = json.load(open(os.path.join(vdir, 'visuals.json'), encoding='utf-8'))
    trim = log.get('trim_start_s', 3.6)
    mp3 = os.path.join(ep_dir, f'{ep}.mp3')
    if not os.path.exists(mp3):
        sys.exit(f'missing {mp3}')

    # card text: render_log has value/time/source, visuals.json has top/label
    items, figs = {}, {}
    for seg in vis['segments']:
        for it in seg.get('items', []):
            if it.get('type') == 'number':
                items[(seg['id'], it['value'])] = it
            elif it.get('type') == 'figure':
                figs[(seg['id'], it['image'])] = it
    cards = []
    for c in log.get('cards', []):
        if 'figure' in c:  # a chart captured from the report
            it = figs.get((c['seg'], c['figure']), {})
            cards.append({'t': c['t'], 'seg': c['seg'], 'kind': 'figure',
                          'image': 'file://' + os.path.join(vdir, c['figure']),
                          'label': it.get('caption', ''), 'source': c.get('source', '')})
            continue
        it = items.get((c['seg'], c['value']), {})
        cards.append({'t': c['t'], 'seg': c['seg'], 'kind': 'number', 'top': it.get('top', ''),
                      'value': c['value'], 'label': it.get('label', ''), 'source': c.get('source', '')})

    cards.sort(key=lambda c: c['t'])  # player looks cards up by time; visuals.json may list figures after the numbers

    # one background per segment, from the segment's start
    seg_bg = {s['id']: s for s in vis['segments']}
    backgrounds = []
    for b in log['boundaries']:
        s = seg_bg.get(b['id'])
        if not s or not s.get('background'):
            continue
        src = os.path.join(vdir, s['background'])
        if os.path.exists(src):
            backgrounds.append({'t': round(max(0.0, b['start'] - trim), 3), 'src': 'file://' + src,
                                'label': s.get('background_label', '')})

    epj = os.path.join(ep_dir, 'episode.json')
    title = json.load(open(epj, encoding='utf-8')).get('title', '') if os.path.exists(epj) else ''
    data = {
        'episode': ep,
        'show': '深夜 Debug',
        'title': title,
        'mp3': mp3,
        'trim_start_s': trim,
        'duration': round(mp3_duration(mp3) - trim, 3),
        'report_label': vis.get('report_label', ''),
        'chapters': log.get('chapters', []),
        'cues': srt_cues(os.path.join(vdir, f'{ep}.srt')),
        'cards': cards,
        'backgrounds': backgrounds,
    }
    out = a.out or os.path.join(vdir, 'out', 'web', 'timeline.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(out, 'cues', len(data['cues']), 'cards', len(cards), 'chapters', len(data['chapters']),
          'duration', data['duration'])


if __name__ == '__main__':
    main()
