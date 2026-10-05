# Motion studio rules

## Render contract
- Every film is a pure function of time: `window.seek(t)` paints frame t.
- No CSS transitions, no setTimeout, no requestAnimationFrame in render mode,
  no state carried between frames. Seeded noise only (mulberry32), never Math.random.
- Render with `node render.mjs`, encode H.264 yuv420p, CRF 16.

## Look
- Banned defaults: centered title on gradient, everything fading in,
  corner labels and frame borders, glow on UI chrome, generic particle bursts.
- One display face, one UI face. One accent color unless the brief says otherwise.
- Every 2 to 4 seconds something new must happen on screen.

## Sound
- Score and SFX are synthesized in code unless a track is supplied.
- Place hits on the measured beat grid (beats.json). Loudness -14 LUFS.

## Loop before you show me anything
1. Render one frame per beat as a contact sheet and LOOK at it.
2. Score it 1-10 on: hook in first 2s, readability at phone size,
   motion quality, variety, brand accuracy, sound sync.
3. Fix the 3 worst problems. Repeat until every score is 8+.
4. Only then do the full render.

## Tooling
- Layout: one folder per film, `films/<name>/index.html`, with optional `audio.wav` and `beats.json` beside it.
- A film sets `window.DURATION` (seconds) and defines `window.seek(t)`. Render mode sets `window.RENDER = true` before page scripts run.
- `python3 scripts/beats.py films/<name>/audio.wav` writes `beats.json` (`{ tempo, beats: [seconds…] }`).
- `node render.mjs films/<name> --sheet` renders the contact sheet (one frame per beat, or one per second without beats.json) to `out/<name>-sheet.png`.
- `node render.mjs films/<name>` renders `out/<name>.mp4`, muxing `audio.wav` normalized to -14 LUFS when present.
- Options: `--fps 30`, `--width 1920 --height 1080`, `--out path`. Set `CHROMIUM_PATH` if Playwright's pinned browser isn't installed.
