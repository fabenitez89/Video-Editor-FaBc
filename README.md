# Motion Studio

Toolchain for animations and motion graphics: HTML, Remotion or HyperFrames compositions rendered with headless Chromium and ffmpeg, plus Python for audio analysis (beat and onset detection).

## Setup

```bash
npm run setup        # pip deps, npm deps, Playwright Chromium
npm run smoke        # renders out/smoke.mp4 to prove the pipeline works
```

If your Chromium build differs from the one Playwright pins, point it at yours: `CHROMIUM_PATH=/path/to/chrome npm run smoke`.

## What's included

| Layer | Contents |
|---|---|
| Runtime | Node 22+, ffmpeg, Python with `numpy`, `librosa`, `soundfile` (`requirements.txt`) |
| Browser | `playwright` (dev dependency) |
| Skills | Remotion (`/remotion-create`, `/remotion-render`, …) and HyperFrames (`/hyperframes` router, animation, audio, CLI, …) vendored in `.agents/skills`, symlinked into `.claude/skills` |
| Plugin | `claude-animation@claude-animation-skill` (hand-drawn rigs, pens, synthesized sound), declared in `.claude/settings.json` |

Start Claude Code with `claude --model claude-opus-5-5`, and use `/model` to raise effort for flagship pieces.
