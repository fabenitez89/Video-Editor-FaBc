// Deterministic film renderer: seeks the page to each frame time, screenshots it, pipes PNGs to ffmpeg.
// Usage: node render.mjs films/<name> [--sheet | --at t1,t2,...] [--fps 30] [--width 1920] [--height 1080] [--out path]
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { basename, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const flag = (name) => args.includes(`--${name}`);
const opt = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : fallback;
};
const valued = new Set(['--fps', '--width', '--height', '--out', '--at']);
const filmDir = args.find((a, i) => !a.startsWith('--') && !valued.has(args[i - 1]));
if (!filmDir) {
  console.error('usage: node render.mjs films/<name> [--sheet] [--fps 30] [--width 1920] [--height 1080] [--out path]');
  process.exit(1);
}
const name = basename(resolve(filmDir));
const fps = Number(opt('fps', 30));
const width = Number(opt('width', 1920));
const height = Number(opt('height', 1080));
const at = opt('at', null)?.split(',').map(Number);
const sheet = flag('sheet') || Boolean(at);
const out = opt('out', `out/${name}${sheet ? '-sheet.png' : '.mp4'}`);
const audio = join(filmDir, 'audio.wav');
const beatsFile = join(filmDir, 'beats.json');

// Two-pass loudnorm: measure first, then apply linearly so the result lands on -14 LUFS.
async function loudnormFilter(file) {
  const target = 'I=-14:TP=-2:LRA=11'; // 2 dB headroom: AAC encoding adds inter-sample overs
  const proc = spawn('ffmpeg', ['-hide_banner', '-i', file, '-af', `loudnorm=${target}:print_format=json`, '-f', 'null', '-']);
  let log = '';
  proc.stderr.on('data', (d) => { log += d; });
  await new Promise((ok) => proc.on('close', ok));
  const m = JSON.parse(log.slice(log.lastIndexOf('{')));
  return `loudnorm=${target}:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}`
    + `:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
}

function ffmpeg(ffArgs) {
  const proc = spawn('ffmpeg', ['-y', '-loglevel', 'error', ...ffArgs], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, fail) => proc.on('close', (code) => (code ? fail(new Error(`ffmpeg exited ${code}`)) : ok())));
  return { stdin: proc.stdin, done };
}

mkdirSync('out', { recursive: true });
const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const page = await browser.newPage({ viewport: { width, height } });
await page.addInitScript(() => { window.RENDER = true; });
await page.goto(pathToFileURL(resolve(filmDir, 'index.html')).href);
await page.evaluate(async () => { await window.READY; await document.fonts.ready; });
const duration = await page.evaluate(() => {
  if (typeof window.seek !== 'function') throw new Error('film must define window.seek(t)');
  if (!(window.DURATION > 0)) throw new Error('film must set window.DURATION in seconds');
  return window.DURATION;
});

async function frameAt(t) {
  await page.evaluate((time) => window.seek(time), t);
  return page.screenshot({ type: 'png' });
}

if (sheet) {
  const grid = existsSync(beatsFile) ? JSON.parse(readFileSync(beatsFile, 'utf8')) : null;
  const times = at ?? (grid?.period
    ? Array.from({ length: Math.ceil((duration - grid.offset) / grid.period) }, (_, i) => grid.offset + i * grid.period)
    : grid ? grid.beats.filter((t) => t < duration) : Array.from({ length: Math.ceil(duration) }, (_, i) => i));
  const cols = Math.min(6, times.length);
  const rows = Math.ceil(times.length / cols);
  const enc = ffmpeg(['-f', 'image2pipe', '-c:v', 'png', '-i', '-',
    '-vf', `scale=480:-1,drawtext=text='%{eif\\:n\\:d}':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,tile=${cols}x${rows}:padding=4`,
    '-frames:v', '1', out]);
  for (const t of times) enc.stdin.write(await frameAt(t));
  enc.stdin.end();
  await enc.done;
  console.log(`sheet: ${out} (${times.length} frames at ${times.map((t) => t.toFixed(2)).join(', ')}s)`);
} else {
  const total = Math.round(duration * fps);
  const hasAudio = existsSync(audio);
  const enc = ffmpeg([
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    ...(hasAudio ? ['-i', audio, '-af', await loudnormFilter(audio), '-c:a', 'aac', '-b:a', '192k', '-shortest'] : []),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'slow', '-movflags', '+faststart', out,
  ]);
  for (let f = 0; f < total; f++) {
    enc.stdin.write(await frameAt(f / fps));
    if (f % fps === 0) process.stdout.write(`\r${f}/${total}`);
  }
  enc.stdin.end();
  await enc.done;
  console.log(`\rvideo: ${out} (${total} frames, ${fps}fps${hasAudio ? ', audio -14 LUFS' : ''})`);
}
await browser.close();
