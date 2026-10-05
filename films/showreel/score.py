"""Synthesize the showreel score: 15 s at 120 BPM in F minor, one bar per scene.

Usage: python3 films/showreel/score.py   (writes audio.wav beside this file)
"""
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 120
BEAT = 60 / BPM
LENGTH = 15.0
rng = np.random.default_rng(15)

n = int(SR * LENGTH)
drums = np.zeros(n)
music = np.zeros(n)
sfx = np.zeros(n)
duck = np.ones(n)  # sidechain gain applied to music


def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def place(bus, start, sig, gain=1.0):
    i = int(start * SR)
    j = min(n, i + len(sig))
    if i < n:
        bus[i:j] += sig[: j - i] * gain


def filt(sig, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=SR, output="sos"), sig)


def noise(dur):
    return rng.standard_normal(int(SR * dur))


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


# ---- instruments -------------------------------------------------------------

def kick(big=False):
    t = t_axis(0.6 if big else 0.35)
    f = 45 + 110 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (5 if big else 9))
    click = filt(noise(0.01), "highpass", 2000) * 0.3
    body[: len(click)] += click
    return np.tanh(body * 1.6)


def clap():
    t = t_axis(0.25)
    env = np.exp(-t * 22)
    for k in (0.0, 0.011, 0.023):  # three smeared transients
        env += np.where(t >= k, np.exp(-(t - k) * 120), 0) * 0.6
    return filt(noise(0.25), "bandpass", [900, 5000]) * env * 0.5


def hat(open_=False):
    dur = 0.18 if open_ else 0.05
    t = t_axis(dur)
    return filt(noise(dur), "highpass", 7000) * np.exp(-t * (18 if open_ else 80)) * 0.35


def saw(freq, dur, voices=3, detune=0.012):
    t = t_axis(dur)
    out = np.zeros_like(t)
    for v in range(voices):
        f = freq * (1 + detune * (v - (voices - 1) / 2))
        ph = rng.random()
        out += 2 * ((t * f + ph) % 1) - 1
    return out / voices


def bass(midi, dur):
    t = t_axis(dur)
    sig = saw(hz(midi), dur, voices=2, detune=0.004) * 0.6 + np.sin(2 * np.pi * hz(midi) * t)
    sig = filt(sig, "lowpass", 420)
    env = np.minimum(1, t / 0.005) * np.exp(-t * 2.5)
    return np.tanh(sig * env * 1.4) * 0.55


def pluck(midi, dur=0.3):
    t = t_axis(dur)
    sig = saw(hz(midi), dur, voices=2)
    cutoff_env = np.exp(-t * 18)
    sig = filt(sig, "lowpass", 3500) * cutoff_env * 0.7 + np.sin(2 * np.pi * hz(midi) * t) * cutoff_env * 0.3
    return sig * 0.35


def pad(midis, dur):
    t = t_axis(dur)
    sig = sum(saw(hz(m), dur, voices=4, detune=0.008) for m in midis) / len(midis)
    sig = filt(sig, "lowpass", 1400)
    env = np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.3)
    return sig * env * 0.22


def stab(midis, dur=0.22):
    t = t_axis(dur)
    sig = sum(saw(hz(m), dur, voices=3) for m in midis) / len(midis)
    sig = filt(sig, "lowpass", 2600)
    return sig * np.exp(-t * 9) * 0.45


def whoosh(dur, rising=True):
    t = t_axis(dur)
    sig = noise(dur)
    lo, hi = 300, 6000
    out = np.zeros_like(sig)
    steps = 24
    seg = len(sig) // steps
    for s in range(steps):  # stepped band sweep, cheap and smooth enough under the envelope
        p = s / (steps - 1)
        f = lo * (hi / lo) ** (p if rising else 1 - p)
        a, b = s * seg, (s + 1) * seg if s < steps - 1 else len(sig)
        out[a:b] = filt(sig[max(0, a - 2000):b], "bandpass", [f * 0.7, min(f * 1.4, 18000)])[-(b - a):]
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2 if not rising else (t / dur) ** 2
    return out * env * 0.5


def impact():
    t = t_axis(1.6)
    boom = np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-t * 9)) / SR) * np.exp(-t * 2.2)
    crash = filt(noise(1.6), "highpass", 3000) * np.exp(-t * 3.5) * 0.4
    return np.tanh(boom * 1.8) * 0.9 + crash


def riser(dur):
    t = t_axis(dur)
    f = 200 * (1 + 7 * (t / dur) ** 2)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (tone * 0.4 + filt(noise(dur), "highpass", 1500) * 0.5) * (t / dur) ** 2.5 * 0.5


def sidechain(at, depth=0.65, release=0.22):
    t = t_axis(release)
    i = int(at * SR)
    curve = 1 - depth * np.exp(-t * 5 / release)
    j = min(n, i + len(curve))
    duck[i:j] = np.minimum(duck[i:j], curve[: j - i])


# ---- arrangement -------------------------------------------------------------

CHORDS = [[53, 56, 60], [49, 53, 56], [56, 60, 63], [51, 55, 58]]  # Fm Db Ab Eb
ROOTS = [29, 25, 32, 27]  # F1 Db1 Ab1 Eb1
ARP = [[65, 68, 72, 75], [61, 65, 68, 72], [68, 72, 75, 80], [63, 67, 70, 75]]

# Scene A (0-2): impact, then four rising hits under the letters M-O-V-E, slice whoosh.
place(sfx, 0.0, impact(), 0.9)
for k, m in enumerate([60, 63, 67, 72]):
    place(music, k * 0.25, stab([m - 12, m]), 0.9)
place(sfx, 1.45, whoosh(0.55, rising=True), 0.8)

# Scene B (2-4): four bounces, each landing a kick and a rising pluck.
for k in range(4):
    at = 2 + k * BEAT
    place(drums, at, kick(), 0.9)
    sidechain(at)
    place(music, at, pluck(65 + [0, 3, 7, 12][k], 0.45), 1.2)
    place(drums, at + BEAT / 2, hat(), 0.8)
place(sfx, 3.55, whoosh(0.45, rising=True), 0.9)

# Groove (4-12): four-on-the-floor, claps on 2 and 4, sixteenth hats, bass, arps, pad.
for b in range(8, 24):
    at = b * BEAT
    place(drums, at, kick(), 1.0)
    sidechain(at)
    if b % 2 == 1:
        place(drums, at, clap(), 1.0)
    for s in range(4):
        place(drums, at + s * BEAT / 4, hat(open_=(s == 2)), 0.9 if s % 2 == 0 else 0.5)
    bar = (b // 4) % 4
    place(music, at, bass(ROOTS[bar] + 12, BEAT * 0.9))
    if b >= 12:  # arps join with the easing scene
        for s in range(2):
            place(music, at + s * BEAT / 2, pluck(ARP[bar][(b * 2 + s) % 4], 0.25), 0.9)
for bar_start, bar in [(4, 0), (6, 1), (8, 2), (10, 3)]:
    place(music, bar_start, pad(CHORDS[bar], 2.0), 1.0 if bar_start >= 8 else 0.6)
for at in (5.6, 7.6, 9.6):
    place(sfx, at, whoosh(0.4, rising=False), 0.6)

# Build into the montage: riser and snare roll over beats 22-23.
place(sfx, 10.5, riser(1.5), 1.0)
for k in range(8):
    place(drums, 11.0 + k * BEAT / 8 * 2, clap(), 0.35 + k * 0.08)

# Scene G (12-14): double-time, a stab on every cut.
place(sfx, 12.0, impact(), 0.6)
for k in range(8):
    at = 12 + k * BEAT / 2
    place(drums, at, kick(), 0.9 if k % 2 == 0 else 0.6)
    sidechain(at, depth=0.5, release=0.15)
    place(drums, at + BEAT / 4, hat(open_=True), 0.6)
    chord = CHORDS[[0, 0, 1, 1, 2, 2, 3, 3][k]]
    place(music, at, stab([m + 12 for m in chord]), 0.8)
    place(music, at, bass(ROOTS[[0, 0, 1, 1, 2, 2, 3, 3][k]] + 12, BEAT / 2 * 0.9), 0.9)
place(sfx, 13.6, whoosh(0.4, rising=True), 0.9)

# Scene H (14-15): final hit, F minor stab ringing into the reverb.
place(drums, 14.0, kick(big=True), 1.2)
place(sfx, 14.0, impact(), 1.0)
place(music, 14.0, stab([41, 53, 56, 60, 65], dur=1.0), 1.1)

# ---- mix ---------------------------------------------------------------------

def reverb(sig, seconds=1.4, wet=0.22):
    t = t_axis(seconds)
    ir = filt(noise(seconds), "lowpass", 5000) * np.exp(-t * 4.5)
    ir /= np.sqrt(np.sum(ir ** 2))
    return sig + fftconvolve(sig, ir)[: len(sig)] * wet


mix = drums + reverb(music * duck, wet=0.3) + reverb(sfx, wet=0.25)
fade = np.ones(n)
tail = int(0.15 * SR)
fade[-tail:] = np.linspace(1, 0, tail)
mix = np.tanh(mix * 0.9) * fade  # glue + soft clip so the renderer's -14 LUFS target is reachable

stereo = np.stack([mix, mix], axis=1)
out = Path(__file__).with_name("audio.wav")
sf.write(out, stereo.astype(np.float32), SR)
print(f"{out}: {LENGTH}s, peak {np.max(np.abs(mix)):.2f}")
