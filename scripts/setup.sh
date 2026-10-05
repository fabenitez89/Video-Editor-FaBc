#!/usr/bin/env bash
# Reproduce the motion-studio toolchain on a fresh machine.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Runtime: Node 22+, ffmpeg, Python for audio analysis
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install node ffmpeg python
  else sudo apt-get update && sudo apt-get install -y ffmpeg python3-pip; fi
fi
pip install -r requirements.txt

# 2. Headless browser
npm install
if [ -z "${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-}" ]; then npx playwright install chromium; fi

# 3. Framework skills are vendored in .agents/skills (symlinked into .claude/skills).
#    To refresh them:  npx skills add remotion-dev/skills -y && npx skills add heygen-com/hyperframes -y
# 4. The claude-animation plugin is declared in .claude/settings.json and installs on first launch.
echo "Setup complete. Run: npm run smoke"
