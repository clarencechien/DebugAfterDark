"""Fill in the measurable fields of episodes/<ep>/episode.json from the mastered mp3: duration, bytes, sha256.

  python3 tools/package_episode.py episodes/<ep>
Everything else in episode.json (title, description, report slug, guid, models, takes) is written by hand or by the
other tools; this only refreshes what has to match the file byte for byte (the RSS <enclosure> length, PIPELINE.md §5.2).
"""
import hashlib, json, subprocess, sys
from pathlib import Path

ep = Path(sys.argv[1]); meta_p = ep / "episode.json"; meta = json.loads(meta_p.read_text(encoding="utf-8"))
mp3 = ep / meta["audio"]["file"]; data = mp3.read_bytes()
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)], capture_output=True, text=True).stdout)
lufs = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp3), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = float([l for l in lufs.splitlines() if l.strip().startswith("I:")][-1].split()[1])
meta["audio"].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), duration_s=round(dur, 1),
                     duration=f"{int(dur // 60)}:{int(dur % 60):02d}", lufs=lufs)
meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(meta["audio"], ensure_ascii=False))
