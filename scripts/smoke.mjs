// Smoke test: render 30 frames of an HTML animation with headless Chromium, encode with ffmpeg.
import { chromium } from 'playwright';
import { mkdirSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const dir = 'out/smoke-frames';
rmSync(dir, { recursive: true, force: true });
mkdirSync(dir, { recursive: true });

// CHROMIUM_PATH lets a preinstalled browser stand in when its build differs from Playwright's pinned one.
const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const page = await browser.newPage({ viewport: { width: 640, height: 360 } });
await page.setContent(`<body style="margin:0;background:#111">
  <div id="b" style="position:absolute;top:150px;width:60px;height:60px;border-radius:50%;background:#f5a524"></div></body>`);
for (let f = 0; f < 30; f++) {
  await page.evaluate((x) => { document.getElementById('b').style.left = x + 'px'; }, 20 + f * 18);
  await page.screenshot({ path: `${dir}/${String(f).padStart(4, '0')}.png` });
}
await browser.close();

execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '30', '-i', `${dir}/%04d.png`,
  '-pix_fmt', 'yuv420p', 'out/smoke.mp4']);
console.log('ok: out/smoke.mp4');
