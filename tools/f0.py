"""Median pitch of every take, relative to the episode median of the chosen takes.

Usage: python3 tools/f0.py out/segments/D1_<ep>   (chosen take marked with *)
"""
import json, sys, numpy as np
sys.path.insert(0, "tools"); import measures as M
d = sys.argv[1]; L = json.load(open(f"{d}/select_log.json"))
meds = {}
for s in L["segments"]:
    for t in s["takes"]:
        f = M.f0_frames(M.read(f"{d}/{t['file']}")); f = f[f > 0]
        meds[t["file"]] = float(np.median(f))
ch = [meds[s["chosen"]] for s in L["segments"]]; ep = float(np.median(ch))
print("episode median", round(ep, 1))
for s in L["segments"]:
    print(f"{s['id']:16s}", "  ".join(f"{t['file'].split('.')[1]}{'*' if t['file']==s['chosen'] else ' '}{meds[t['file']]-ep:+5.1f}" for t in s["takes"]))
