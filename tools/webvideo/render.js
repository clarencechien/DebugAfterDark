// Record the web-page player into an mp4 (prototype, docs/video-web.md).
// Same idea as the A1 course demo replays: Playwright steps a deterministic page frame by frame
// and pipes PNGs to ffmpeg. Frames whose seek() key did not change reuse the last screenshot,
// so still stretches cost almost nothing.
//
// usage:
//   node tools/webvideo/render.js timeline.json out.mp4 [--theme slide|paper|terminal] [--from 0] [--to 30] [--fps 30]
//   node tools/webvideo/render.js timeline.json still.png --still 15.5 [--theme paper]
//   --variant step|ease|scan|pulse   how the cold-open trace bars move (theme opening; default step, the first version)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');

function arg(name, def) { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; }

(async () => {
  const [tl, out] = process.argv.slice(2);
  if (!tl || !out) { console.error('usage: render.js timeline.json out.mp4|out.png [--theme] [--from] [--to] [--fps] [--still t]'); process.exit(2); }
  const D = JSON.parse(fs.readFileSync(tl, 'utf8'));
  const theme = arg('theme', 'slide'), fps = +arg('fps', 30), variant = arg('variant', null);
  const from = +arg('from', 0), to = Math.min(+arg('to', D.duration), D.duration);
  const still = arg('still', null);

  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'player.html'));
  await p.evaluate(([d, th, v]) => load(d, th, v), [D, theme, variant]);
  await p.evaluate(() => document.fonts.ready);

  if (still !== null) {
    await p.evaluate(t => seek(t), +still);
    await p.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));
    await p.screenshot({ path: out });
    await b.close(); console.log(out); return;
  }

  // video frames on stdin, audio straight from the episode mp3 (offset by the trimmed intro)
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-ss', String(D.trim_start_s + from), '-t', String(to - from), '-i', D.mp3,
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-crf', '18',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });

  const n = Math.round((to - from) * fps);
  let last = null, lastKey = null, shots = 0;
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const key = await p.evaluate(t => seek(t), from + i / fps);
    if (key !== lastKey) { last = await p.screenshot({ type: 'png' }); lastKey = key; shots++; }
    if (!ff.stdin.write(last)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
  const secs = (Date.now() - t0) / 1000;
  console.log(JSON.stringify({ out, theme, variant, frames: n, screenshots: shots, seconds: +secs.toFixed(1),
    seconds_per_video_minute: +(secs / ((to - from) / 60)).toFixed(1) }));
})();
