"""Measure the beat grid of an audio file and write beats.json (and beats.js for films) beside it.

Usage: python3 scripts/beats.py films/<name>/audio.wav
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np

path = Path(sys.argv[1])
y, sr = librosa.load(path, sr=None, mono=True)
tempo, frames = librosa.beat.beat_track(y=y, sr=sr)
beats = librosa.frames_to_time(frames, sr=sr)
grid = {"tempo": round(float(np.atleast_1d(tempo)[0]), 2), "beats": [round(float(t), 3) for t in beats]}
if len(beats) >= 2:
    # Least-squares fit of a steady grid, so films can extend it over sections the tracker skipped.
    period, offset = np.polyfit(np.arange(len(beats)), beats, 1)
    grid["period"] = round(float(period), 4)
    grid["offset"] = round(float(offset % period), 4)
out = path.with_name("beats.json")
out.write_text(json.dumps(grid, indent=2))
# Films load this as a script, since file:// pages can't fetch JSON.
path.with_name("beats.js").write_text(f"window.BEATS = {json.dumps(grid)};\n")
print(f"{out}: {len(beats)} beats at {float(np.atleast_1d(tempo)[0]):.1f} BPM")
