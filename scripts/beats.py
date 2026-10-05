"""Measure the beat grid of an audio file and write beats.json beside it.

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
out = path.with_name("beats.json")
out.write_text(json.dumps({"tempo": round(float(np.atleast_1d(tempo)[0]), 2),
                           "beats": [round(float(t), 3) for t in beats]}, indent=2))
print(f"{out}: {len(beats)} beats at {float(np.atleast_1d(tempo)[0]):.1f} BPM")
