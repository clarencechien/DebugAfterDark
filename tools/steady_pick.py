"""Usage: python3 tools/steady_pick.py <ep>   (after select_takes.py; rewrites select_log.json and <seg>.wav)

Pick, per segment, the steadiest take within pitch ±5 Hz, pace ±10% and CER within 0.02 of the best."""
import json, re, subprocess, statistics, shutil, sys
ep = sys.argv[1]; d = f'out/segments/D1_{ep}'
out = subprocess.run(['python3', 'tools/f0.py', d], capture_output=True, text=True).stdout
pitch = {}
for line in out.splitlines():
    m = re.match(r'(s\d+_\w+)\s+(.*)', line)
    if not m: continue
    for t, v in re.findall(r'(take\d+)\*?\s*([+-]\d+\.\d)', m.group(2)): pitch[(m.group(1), t)] = float(v)
L = json.load(open(f'{d}/select_log.json'))
cps_med = statistics.median(t['cps'] for e in L['segments'] for t in e['takes'])
for e in L['segments']:
    sid = e['id']; best = min(t['cer'] for t in e['takes'])
    ok = []
    for t in e['takes']:
        tk = re.search(r'(take\d+)', t['file']).group(1); p = pitch.get((sid, tk), 99)
        if t['cer'] <= best + 0.02 and abs(p) <= 5 and abs(t['cps'] - cps_med) / cps_med <= 0.10: ok.append((t['jitter'], t['file'], p, t['cps'], t['cer']))
    if not ok: print(sid, 'no take passes; keep', e['chosen']); continue
    j, f, p, c, r = min(ok)
    if f != e['chosen']:
        old = next(t for t in e['takes'] if t['file'] == e['chosen'])
        e['manual_override'] = f"音高跳動較低的 {f.split('.')[1]}（{j:.3f}，音高 {p:+.1f} Hz）取代 {e['chosen'].split('.')[1]}（{old['jitter']:.3f}）"
        e['chosen'] = f; shutil.copy(f'{d}/{f}', f'{d}/{sid}.wav')
    print(sid, e['chosen'].split('.')[1], f'jit {j:.3f} pitch {p:+.1f} cps {c} cer {r}')
json.dump(L, open(f'{d}/select_log.json', 'w'), ensure_ascii=False, indent=1)
