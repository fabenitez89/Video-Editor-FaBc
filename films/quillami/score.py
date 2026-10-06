"""Quillami Car Wash: 25 s at 90 BPM, a dark low-end bed with sound design per shot, plus the cue sheet.

Follows docs/style_guide.md §9: heavy 40-300 Hz bed, dense transient hits, a riser with tonal pings
(about 1.8 kHz and 4.3 kHz) into the whiteout, then hits thin out and the track fades under the hold.
Usage: python3 films/quillami/score.py   (writes audio.wav and cues.js beside this file)
"""
import json
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 90
BEAT = 60 / BPM            # 0.667 s
BAR = 4 * BEAT
LENGTH = 25.0
N = int(SR * LENGTH)
HERE = Path(__file__).parent
rng = np.random.default_rng(25)
b = lambda n: round(n * BEAT, 4)   # beat number -> seconds


def filt(sig, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=SR, output="sos"), sig, axis=0)


def t_ax(dur):
    return np.arange(int(SR * dur)) / SR


def noise(n):
    return rng.standard_normal(int(n))


# ==== cue sheet (docs/shotlist.md) ==============================================================
CUES = {
    "flick": 0.0, "ignite": b(0.5), "drop": b(1),
    "hook": [b(2), b(3), b(4)], "orbit": [b(5), b(6)],
    "lavado": b(7), "lavado_label": b(8), "beads": [b(9), b(10), b(11)], "whip1": [b(11), b(12)],
    "brillado": b(13), "brillado_label": b(14), "crest": b(15), "whip2": [b(16), b(17)],
    "polichado": b(18), "polichado_label": b(19), "orbits": [b(18), b(19), b(20), b(21)], "whip3": [b(21), b(22)],
    "polarizados": b(23), "polarizados_label": b(24), "tint": [b(22.4), b(24)], "smear": [b(26), b(27)],
    "ymas": b(28), "build": [b(28.35), b(30)], "peak": b(30),
    "wordmark": [b(30), b(30.9)], "carwash": b(31), "whatsapp": b(32), "phone": b(33), "handle": b(34),
    "hold": b(34), "fade": [b(35), 25.0],
}
SHOTS = [0.0, b(6), b(12), b(17), b(22), b(27), b(30)]


# ==== instruments ===================================================================================
def kick(v=1.0):
    t = t_ax(0.5)
    body = np.sin(2 * np.pi * np.cumsum(42 + 130 * np.exp(-t * 30)) / SR) * np.exp(-t * 6.5)
    click = filt(noise(300), "highpass", 2500) * 0.35
    body[:300] += click
    return np.tanh(body * 2.0) * v * 0.85


def rim(v=1.0):
    t = t_ax(0.12)
    tone = np.sin(2 * np.pi * 1650 * t) * np.exp(-t * 70) + np.sin(2 * np.pi * 520 * t) * np.exp(-t * 50) * 0.6
    return (tone + filt(noise(len(t)), "bandpass", [2000, 7000]) * np.exp(-t * 120) * 0.5) * v * 0.3


def clap(v=1.0):
    t = t_ax(0.25)
    env = np.exp(-t * 20)
    for k in (0.0, 0.01, 0.021):
        env += np.where(t >= k, np.exp(-(t - k) * 130), 0) * 0.7
    return filt(noise(len(t)), "bandpass", [900, 5500]) * env * 0.38 * v


def hat(v=1.0, open_=False):
    dur = 0.18 if open_ else 0.045
    t = t_ax(dur)
    return filt(noise(len(t)), "highpass", 7500) * np.exp(-t * (16 if open_ else 85)) * 0.22 * v


def bass(f, dur):
    t = t_ax(dur)
    saw = 2 * ((t * f) % 1) - 1
    sub = np.sin(2 * np.pi * f * t)
    body = filt(saw, "lowpass", 260) * 0.55 + sub
    env = np.minimum(1, t / 0.008) * np.exp(-t * 3.2)
    return np.tanh(body * env * 1.6) * 0.55


def rumble(dur):
    """The engine bed: a detuned low saw cluster under filtered noise, slowly breathing."""
    t = t_ax(dur)
    f = 36.7
    saw = sum(2 * (((t * f * d) + ph) % 1) - 1 for d, ph in [(1, 0), (1.007, .3), (0.994, .6)]) / 3
    lo = filt(saw, "lowpass", 140, order=4)
    rum = filt(noise(len(t)), "lowpass", 220, order=4) * 0.8
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.35 * t)
    return np.tanh((lo * 1.2 + rum) * lfo * 1.2) * 0.32


# ==== sound effects ==================================================================================
def tick(v=1.0, f=4200):
    t = t_ax(0.04)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 220) + filt(noise(len(t)), "highpass", 6000) * np.exp(-t * 300) * 0.4) * v * 0.45


def whoosh(dur, rising=True, gain=0.4):
    t = t_ax(dur)
    sig = noise(len(t))
    out = np.zeros(len(t))
    steps, seg = 24, len(t) // 24
    for s in range(steps):
        p = s / (steps - 1)
        fc = 220 * (45 ** (p if rising else 1 - p))
        a, z = s * seg, (s + 1) * seg if s < steps - 1 else len(t)
        out[a:z] = filt(sig[max(0, a - 1500):z], "bandpass", [fc * 0.6, min(fc * 1.7, 19000)])[-(z - a):]
    return out * np.sin(np.pi * t / dur) ** 2 * gain


def low_hit(v=1.0):
    t = t_ax(0.9)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t * 14)) / SR) * np.exp(-t * 4.5)
    body = filt(noise(len(t)), "bandpass", [80, 900]) * np.exp(-t * 22) * 0.6
    return np.tanh((boom + body) * 1.8) * v * 0.7


def condense(dur=0.35):
    """Light gathering into a shape: a short reversed shimmer that lands on the hit."""
    t = t_ax(dur)
    s = sum(np.sin(2 * np.pi * f * t) for f in (2400, 3600, 5100)) / 3
    s += filt(noise(len(t)), "highpass", 5000) * 0.6
    return (s * np.exp(-t * 9))[::-1] * 0.16


def spray(dur):
    t = t_ax(dur)
    base = filt(noise(len(t)), "bandpass", [1500, 9000]) * 0.5
    grains = np.zeros(len(t))
    for _ in range(int(dur * 90)):  # droplets
        k = rng.integers(0, len(t) - 400)
        f = rng.uniform(2500, 6000)
        g = t_ax(0.008)
        grains[k:k + len(g)] += np.sin(2 * np.pi * f * g) * np.exp(-g * 600) * rng.uniform(0.2, 0.7)
    env = np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.4)
    return (base + grains) * env * 0.16


def plink(f=2400):
    t = t_ax(0.25)
    f_t = f * (1 + 0.6 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f_t) / SR) * np.exp(-t * 18) * 0.28


def shimmer(dur):
    t = t_ax(dur)
    f = 1600 * 2 ** (1.2 * t / dur)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return s * (t / dur) ** 1.5 * np.exp(-np.maximum(0, t - dur * 0.85) * 20) * 0.08


def ting(f=3520):
    t = t_ax(1.4)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in [(1, 1, 3), (2.76, .5, 6), (5.4, .25, 10)])
    return s * 0.18


def hum(dur):
    t = t_ax(dur)
    f = 85 + 90 * (t / dur)
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    am = 0.7 + 0.3 * np.sin(2 * np.pi * (1 / BEAT) * t)
    return filt(saw, "bandpass", [120, 1400]) * am * np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.3) * 0.11


def film(dur):
    """Tint film sliding over glass: a band of noise sweeping down with a crinkle on top."""
    t = t_ax(dur)
    hiss = whoosh(dur, rising=False, gain=0.35)
    crinkle = filt(noise(len(t)), "highpass", 4000) * (rng.random(len(t)) < 0.004) * 3
    return hiss + filt(crinkle, "lowpass", 9000) * np.sin(np.pi * t / dur) * 0.15


def riser(dur):
    t = t_ax(dur)
    f = 180 * 2 ** (5.4 * (t / dur) ** 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    air = filt(noise(len(t)), "highpass", 2500) * (t / dur) ** 2
    return (tone * 0.35 + air * 0.4) * (t / dur) ** 2.2 * 0.5


def pings(dur):
    t = t_ax(dur)
    s = np.zeros(len(t))
    for f, rate, ph in [(1800, 9, 0), (4300, 13, 1.1), (2700, 11, 2.2)]:
        trem = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t + ph)
        s += np.sin(2 * np.pi * f * t) * trem
    env = np.minimum(1, t / 0.1) * np.exp(-np.maximum(0, t - dur * 0.55) * 4)
    return s * env * 0.06


def peak_hit():
    t = t_ax(2.2)
    boom = np.sin(2 * np.pi * np.cumsum(33 + 90 * np.exp(-t * 9)) / SR) * np.exp(-t * 2.2)
    crash = filt(noise(len(t)), "highpass", 3000) * np.exp(-t * 2.8) * 0.45
    return np.tanh(boom * 2.2) * 0.9 + crash


# ==== arrangement ====================================================================================
drums = np.zeros((N, 2))
music = np.zeros((N, 2))
sfx = np.zeros((N, 2))
duck = np.ones(N)


def place(bus, at, sig, pan=0.0, gain=1.0):
    i = int(round(at * SR))
    if i >= N:
        return
    j = min(N, i + len(sig))
    l, r = np.cos((pan + 1) * np.pi / 4) * 1.41, np.sin((pan + 1) * np.pi / 4) * 1.41
    bus[i:j, 0] += sig[: j - i] * gain * l
    bus[i:j, 1] += sig[: j - i] * gain * r


def sidechain(at, depth=0.55, rel=0.25):
    t = t_ax(rel)
    i = int(at * SR)
    c = 1 - depth * np.exp(-t * 5 / rel)
    j = min(N, i + len(c))
    duck[i:j] = np.minimum(duck[i:j], c[: j - i])


ROOTS = [36.71, 29.14, 24.50, 27.50]  # D1 Bb0 G0 A0 (one per bar), heard mostly through harmonics
bed = rumble(LENGTH - 0.3)
place(music, 0.3, bed * np.minimum(1, t_ax(LENGTH - 0.3) / 1.2))

for beat in range(37):
    t0 = b(beat)
    bar_pos = beat % 4
    root = ROOTS[(beat // 4) % 4]
    full = 2 <= beat < 28 and not (24 <= beat < 27)        # shot 5 thins to sub only
    sub_only = 24 <= beat < 27
    if 2 <= beat < 28 or beat in (30, 33):
        if bar_pos in (0, 2) or beat in (30, 33):
            place(drums, t0, kick(1.0 if bar_pos == 0 else .85))
            sidechain(t0)
        if full and bar_pos == 3:
            place(drums, t0 + BEAT * 0.75, kick(.6))
    if full:
        if bar_pos in (1, 3):
            place(drums, t0, clap())
        for e in range(2):
            place(drums, t0 + e * BEAT / 2, hat(.9 if e else .5, open_=(bar_pos == 3 and e == 1)), pan=0.35)
        place(drums, t0 + BEAT * 0.75, rim(.7), pan=-0.4)
    if (full or sub_only) and beat < 28:
        for e in range(2):  # bass pulses on eighths
            place(music, t0 + e * BEAT / 2, bass(root * 2, BEAT / 2 * 0.95), gain=.9 if e == 0 else .6)

# Build: hats accelerate under the riser.
k, step = b(28), BEAT / 2
while k < b(30) - 0.03:
    place(drums, k, hat(0.5 + 0.6 * (k - b(28)) / (b(30) - b(28))), pan=0.3)
    k += step
    step = max(BEAT / 8, step * 0.82)

# Shot 1.
place(sfx, CUES["flick"], tick(1.0, 5200), pan=-0.4)
place(sfx, CUES["flick"], whoosh(0.35, gain=.25), pan=-0.6)
place(sfx, CUES["ignite"] - 0.2, whoosh(1.0, rising=True, gain=.35))
for i, at in enumerate(CUES["hook"]):
    place(sfx, at - 0.35, condense())
    place(sfx, at, low_hit(.9 + .1 * i))
place(sfx, CUES["orbit"][0], whoosh(b(1.2), gain=.5), pan=-0.7)
place(sfx, CUES["orbit"][0] + 0.25, whoosh(b(0.9), gain=.4), pan=0.7)

# Shot 2: water.
place(sfx, b(6), spray(b(6)), gain=1.0)
place(sfx, CUES["lavado"] - 0.35, condense()); place(sfx, CUES["lavado"], low_hit(.9))
place(sfx, CUES["lavado_label"], tick(.7, 3600))
for i, at in enumerate(CUES["beads"]):
    place(sfx, at, plink(2200 + 400 * i), pan=-0.3 + 0.3 * i)
place(sfx, CUES["whip1"][0], whoosh(b(1), gain=.55), pan=0.5)

# Shot 3: gloss.
place(sfx, b(12), shimmer(b(3)))
place(sfx, CUES["brillado"] - 0.35, condense()); place(sfx, CUES["brillado"], low_hit(.9))
place(sfx, CUES["brillado_label"], tick(.7, 3600))
place(sfx, CUES["crest"], ting())
place(sfx, CUES["whip2"][0], whoosh(b(1), gain=.55), pan=-0.5)

# Shot 4: polish.
place(sfx, b(17), hum(b(5)))
place(sfx, CUES["polichado"] - 0.35, condense()); place(sfx, CUES["polichado"], low_hit(.9))
place(sfx, CUES["polichado_label"], tick(.7, 3600))
for i, at in enumerate(CUES["orbits"]):
    place(sfx, at, whoosh(BEAT * 0.9, gain=.16), pan=[-0.6, 0.6][i % 2])
place(sfx, CUES["whip3"][0], whoosh(b(1), gain=.55), pan=0.5)

# Shot 5: tint.
place(sfx, CUES["tint"][0], film(CUES["tint"][1] - CUES["tint"][0]), pan=-0.2)
place(sfx, CUES["polarizados"] - 0.35, condense()); place(sfx, CUES["polarizados"], low_hit(.9))
place(sfx, CUES["polarizados_label"], tick(.7, 3600))
place(sfx, CUES["smear"][0], whoosh(b(1), gain=.4))

# Shot 6: build and whiteout.
place(sfx, b(27), riser(b(3)))
place(sfx, CUES["ymas"] - 0.35, condense()); place(sfx, CUES["ymas"], low_hit(.8))
place(sfx, 19.4, pings(1.4))
place(sfx, CUES["peak"], peak_hit())

# Shot 7: lockup.
place(sfx, CUES["carwash"], tick(.6, 3000))
place(sfx, CUES["whatsapp"], tick(.6, 3300))
place(sfx, CUES["phone"], low_hit(.6))
place(sfx, CUES["handle"], tick(.6, 3600))


# ==== mix ============================================================================================
def room_ir(seconds=1.8):
    r = np.random.default_rng(3)
    t = t_ax(seconds)
    ir = np.stack([filt(r.standard_normal(len(t)), "lowpass", 7000) * np.exp(-t * 3.6) for _ in range(2)], 1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def limit(x, ceiling=0.79):
    k = int(0.004 * SR)
    env = uniform_filter1d(maximum_filter1d(np.max(np.abs(x), axis=1), size=2 * k + 1), size=k)
    return x * np.minimum(1, ceiling / np.maximum(env, 1e-9))[:, None]


if __name__ == "__main__":
    ir = room_ir()
    send = sfx * 0.35 + drums * 0.08
    verb = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], 1)
    mix = (music * duck[:, None]) + drums * 0.9 + sfx + verb * 0.4
    mix = filt(mix, "highpass", 28, order=4)
    f0, f1 = int(CUES["fade"][0] * SR), N
    mix[f0:f1] *= (np.linspace(1, 0, f1 - f0) ** 1.6)[:, None]
    meter = pyloudnorm.Meter(SR)
    for _ in range(4):
        mix *= 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
        mix = limit(mix)
    sf.write(HERE / "audio.wav", mix.astype(np.float32), SR)
    (HERE / "cues.js").write_text("window.CUES = " + json.dumps({**CUES, "shots": SHOTS, "bpm": BPM, "beat": BEAT}) + ";\n")
    print(f"LUFS {meter.integrated_loudness(mix):.1f}, peak {20 * np.log10(np.max(np.abs(mix))):.1f} dBFS")
