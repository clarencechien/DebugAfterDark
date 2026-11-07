"""Run twtone (github.com/clarencechien/twtonepoc) on an episode script: surface AI tells and Taiwan wording, zero tokens.

  python3 tools/twtone_check.py episodes/<ep>/script.json [--gate] [--verbose]

twtone checks a Traditional Chinese .md: zhtw-mcp (MoE-based zh-TW linter: wording, punctuation, translationese) plus
signals that paired studies found to be real AI tells (「不是…而是」 contrast pairs, conclusion colons, bridge openers,
long 、 runs), with thresholds from pre-2022 Taiwanese explanatory writing. It only reports; it never rewrites.

This script writes the spoken text (tags removed) as one paragraph per segment to out/twtone/<ep>.md, runs twtone in
quick mode, maps each reported line back to its segment id, and saves the report to episodes/<ep>/qa/twtone.md.
Recipe step 3: fix only the 「要改」 lines, one at a time, keeping facts and qualifiers; record each change in
rewrites/<seg>.json manual_edits. Spoken scripts are not reports: Ping's questions and 「對」「嘛」 style are intended, and
quotes 「」 are left alone (twtone ignores them too).

twtone lives outside this repo: set TWTONE (default /home/user/twtonepoc/twtone); recipe step 0 clones it and runs setup.sh.
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TWTONE = os.environ.get("TWTONE", "/home/user/twtonepoc/twtone")


def main(a):
    script = Path(a.script)
    ep = script.parent.name
    sc = json.loads(script.read_text(encoding="utf-8"))
    segs = [(s["id"], re.sub(r"<[^>]+>", "", s["text"]).strip()) for s in sc["segments"]]
    md = ROOT / "out" / "twtone" / f"{ep}.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("\n\n".join(t for _, t in segs) + "\n", encoding="utf-8")
    line_to_seg = {2 * i + 1: sid for i, (sid, _) in enumerate(segs)}   # paragraph i sits on line 2i+1
    if not Path(TWTONE).exists():
        sys.exit(f"twtone not found at {TWTONE}: git clone https://github.com/clarencechien/twtonepoc and run setup.sh, or set TWTONE")
    cmd = [TWTONE, str(md), "--no-fix"] + (["--gate"] if a.gate else []) + (["--verbose"] if a.verbose else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = re.sub(r"\bL(\d+)\b", lambda m: f"L{m.group(1)}（{line_to_seg.get(int(m.group(1)), '?')}）", r.stdout)
    report = script.parent / "qa" / "twtone.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"# twtone · {ep}\n\n輸入：`out/twtone/{ep}.md`（每段一行，已去掉音效標籤）\n\n{out}", encoding="utf-8")
    print(out)
    if r.stderr.strip():
        print(r.stderr, file=sys.stderr)
    print(f"report: {report}")
    sys.exit(r.returncode if a.gate else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("script")
    ap.add_argument("--gate", action="store_true", help="exit 1 when twtone finds a 要改 (severe) item")
    ap.add_argument("--verbose", action="store_true", help="also list 注意 items")
    main(ap.parse_args())
