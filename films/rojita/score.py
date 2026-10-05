"""Rojita: 30 s of groove and sound design at 120 BPM, plus the cue sheet the film animates to.

Every visual event has a cue here; each cue gets its own synthesized sound, placed on the beat grid.
Usage: python3 films/rojita/score.py   (writes audio.wav and cues.js beside this file)
"""
import json
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 120
BEAT = 60 / BPM          # 0.5 s, one bar = 2 s
LENGTH = 30.0
N = int(SR * LENGTH)
HERE = Path(__file__).parent
rng = np.random.default_rng(30)


def filt(sig, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=SR, output="sos"), sig, axis=0)


def t_ax(dur):
    return np.arange(int(SR * dur)) / SR


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def noise(dur):
    return rng.standard_normal(int(SR * dur))


# ==== cue sheet (seconds, all on the 16th grid) ===============================================
CUES = {
    # Rojita
    "name": 0.0, "name_letters": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25], "name_swoosh": 1.5,
    # Esto que estás viendo / lo creé con Claude.
    "line1": [2.5, 2.75, 3.0, 3.5], "line2": [4.5, 4.75, 5.0], "claude": 5.5,
    # Mira las letras / y lo dinámicas / que se ven.
    "mira": [7.0, 7.25, 7.5], "letras": [7.75, 8.0, 8.125, 8.25, 8.375, 8.5],
    "dinamicas_line": [9.0, 9.25], "dinamicas": [9.5 + 0.125 * i for i in range(9)],
    "seven": [10.75, 11.0, 11.25], "glitch": 11.5,
    # Puedo generar / gráficos en 3D.
    "puedo": [12.0, 12.5], "graficos": [13.0, 13.25, 13.5], "three_d": 13.5, "shapes": [14.0, 14.25, 14.5],
    # Es más, mira este / microscopio en 3D,
    "esmas": [15.0, 15.25, 15.5, 15.75], "micro_title": 16.0, "micro_land": 16.5,
    # que ahora se desarma en partes ...
    "desarma_text": 17.5, "explode": [18.0 + 0.25 * i for i in range(12)], "hold": 21.0,
    # ... y luego se vuelve a construir.
    "construir_text": 21.5, "assemble": [22.0 + 0.125 * i for i in range(12)], "assembled": 24.0,
    # Se ve muy cool, ¿verdad?
    "cool": [24.0, 24.25, 24.5, 24.75], "verdad": 25.5,
    # ¿Qué tienes para decir?
    "que": [27.0, 27.25, 27.5, 27.75], "question": 28.25, "end": 29.25,
}
CUTS = [2.5, 7.0, 12.0, 15.0, 24.0, 27.0]


# ==== instruments ===============================================================================
def mallet(m, dur=0.6, bright=1.0):
    """FM marimba: a 1:4 modulator whose index falls fast gives the woody strike."""
    t = t_ax(dur)
    f = hz(m)
    idx = 3.2 * bright * np.exp(-t * 28)
    sig = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 4 * t))
    sig += 0.25 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 30)
    return sig * np.exp(-t * 7) * np.minimum(1, t / 0.002) * 0.35


def bass_pluck(m, dur=0.45):
    t = t_ax(dur)
    f = hz(m)
    saw = 2 * ((t * f) % 1) - 1
    sub = np.sin(2 * np.pi * f * t)
    cutoff_env = 200 + 1800 * np.exp(-t * 14)
    out = np.zeros_like(t)
    seg = 512
    for i in range(0, len(t), seg):  # time-varying lowpass, block-wise
        out[i:i + seg] = filt(saw[max(0, i - 2048):i + seg], "lowpass", cutoff_env[i])[-len(t[i:i + seg]):]
    return np.tanh((out * 0.7 + sub * 0.6) * np.exp(-t * 4) * 1.5) * 0.45


def kick(v=1.0):
    t = t_ax(0.4)
    body = np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-t * 32)) / SR) * np.exp(-t * 8)
    click = filt(noise(0.006), "highpass", 3000) * 0.4
    body[: len(click)] += click
    return np.tanh(body * 1.7) * v * 0.8


def clap(v=1.0):
    t = t_ax(0.22)
    env = np.exp(-t * 26)
    for k in (0.0, 0.009, 0.019):
        env += np.where(t >= k, np.exp(-(t - k) * 140), 0) * 0.7
    return filt(noise(0.22), "bandpass", [1000, 6000]) * env * 0.4 * v


def hat(v=1.0, open_=False):
    dur = 0.15 if open_ else 0.04
    t = t_ax(dur)
    return filt(noise(dur), "highpass", 8000) * np.exp(-t * (20 if open_ else 90)) * 0.25 * v


# ==== sound effects ===============================================================================
def pop(pitch=1.0):
    t = t_ax(0.12)
    f = 900 * pitch * np.exp(-t * 18) + 220 * pitch
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
    s[:80] += filt(rng.standard_normal(80), "highpass", 2500) * 0.5
    return s * 0.6


def whoosh(dur=0.45, rising=True, gain=0.5):
    t = t_ax(dur)
    sig = noise(dur)
    steps, out = 20, np.zeros(len(t))
    seg = len(t) // steps
    for s in range(steps):
        p = s / (steps - 1)
        f = 250 * (40 ** (p if rising else 1 - p))
        a, b = s * seg, (s + 1) * seg if s < steps - 1 else len(t)
        out[a:b] = filt(sig[max(0, a - 1500):b], "bandpass", [f * 0.6, min(f * 1.6, 19000)])[-(b - a):]
    env = np.sin(np.pi * t / dur) ** 2
    return out * env * gain


def impact(gain=1.0, sub=40):
    t = t_ax(1.2)
    boom = np.sin(2 * np.pi * np.cumsum(sub + 80 * np.exp(-t * 10)) / SR) * np.exp(-t * 3)
    crack = filt(noise(1.2), "highpass", 1500) * np.exp(-t * 14) * 0.5
    return (np.tanh(boom * 2) * 0.8 + crack) * gain


def tick(pitch=1.0):
    t = t_ax(0.03)
    return np.sin(2 * np.pi * 3200 * pitch * t) * np.exp(-t * 260) * 0.5 + filt(noise(0.03), "highpass", 5000) * np.exp(-t * 400) * 0.3


def swish(gain=0.35):
    return whoosh(0.18, rising=True, gain=gain)


def glitch(dur=0.5):
    t = t_ax(dur)
    out = np.zeros(len(t))
    k = 0
    while k < len(t):  # stuttering slices of crushed tones and noise
        L = int(SR * rng.choice([0.015, 0.03, 0.045]))
        f = rng.choice([110, 220, 440, 880, 1760])
        sl = np.sign(np.sin(2 * np.pi * f * t[: L])) * 0.35 if rng.random() < 0.6 else noise(L / SR) * 0.3
        if rng.random() < 0.25:
            sl = sl * 0
        out[k:k + L] = sl[: len(out[k:k + L])]
        k += L
    crushed = np.round(out * 6) / 6
    return filt(crushed, "bandpass", [150, 9000]) * np.exp(-t * 2) * 0.7


def digital_rise(dur=1.0):
    t = t_ax(dur)
    f = 200 * 2 ** (4 * t / dur)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR + 2 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR))
    return s * (t / dur) ** 2 * 0.3


def clink(pitch=1.0, gain=0.5):
    """Small metal part: inharmonic plate modes ringing briefly."""
    t = t_ax(0.5)
    base = 1250 * pitch
    s = sum(a * np.sin(2 * np.pi * base * r * t) * np.exp(-t * d) for r, a, d in [(1, 1, 9), (2.76, .6, 14), (5.4, .35, 22), (8.93, .2, 30)])
    s[:60] += filt(rng.standard_normal(60), "highpass", 4000)
    return s * gain * 0.3


def snap(pitch=1.0):
    """Part seating home: a tight click with a short low thud underneath."""
    t = t_ax(0.18)
    click = filt(noise(0.18), "bandpass", [1800 * pitch, 7000]) * np.exp(-t * 180)
    thud = np.sin(2 * np.pi * (140 * pitch) * t) * np.exp(-t * 35)
    return (click * 0.7 + thud * 0.6) * 0.6


def servo(dur=0.9):
    t = t_ax(dur)
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * t)
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return filt(saw, "bandpass", [300, 2400]) * np.sin(np.pi * t / dur) ** 2 * 0.12


def clunk():
    t = t_ax(0.6)
    body = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 12)
    metal = clink(0.55, 0.9)
    body[: len(metal)] += metal
    return body * 0.8


def sparkle(start=84, n=7, step=0.05):
    out = np.zeros(int(SR * (n * step + 0.8)))
    for i in range(n):
        m = start + [0, 4, 7, 12, 16, 19, 24][i % 7]
        s = mallet(m, 0.6, bright=0.5) * 0.7
        k = int(i * step * SR)
        out[k:k + len(s)] += s
    return out


def chime(m=88):
    t = t_ax(1.6)
    s = sum(a * np.sin(2 * np.pi * hz(m) * r * t) * np.exp(-t * d) for r, a, d in [(1, 1, 2.2), (2.0, .5, 3), (3.0, .3, 4.5), (4.2, .2, 6)])
    return s * 0.22


def boing(dur=0.6):
    t = t_ax(dur)
    f = 180 * 2 ** (1.6 * t / dur) * (1 + 0.08 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 3))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2) * 0.45


def typekey():
    t = t_ax(0.05)
    return (filt(noise(0.05), "bandpass", [1500, 6000]) * np.exp(-t * 160) + np.sin(2 * np.pi * 420 * t) * np.exp(-t * 90) * 0.4) * 0.35


# ==== arrangement ===================================================================================
music = np.zeros((N, 2))
drums = np.zeros((N, 2))
sfx = np.zeros((N, 2))
duck = np.ones(N)


def place(bus, at, sig, pan=0.0, gain=1.0):
    i = int(round(at * SR))
    if i >= N:
        return
    j = min(N, i + len(sig))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i:j, 0] += sig[: j - i] * gain * l * 1.41
    bus[i:j, 1] += sig[: j - i] * gain * r * 1.41


def sidechain(at, depth=0.6, rel=0.2):
    t = t_ax(rel)
    i = int(at * SR)
    c = 1 - depth * np.exp(-t * 5 / rel)
    j = min(N, i + len(c))
    duck[i:j] = np.minimum(duck[i:j], c[: j - i])


CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
ROOTS = [45, 41, 36, 43]
groove_bars = {b: "full" for b in range(1, 6)}          # 2-12 s
groove_bars.update({6: "half", 7: "light", 8: "light", 9: "light", 10: "light", 11: "light"})
groove_bars.update({12: "full", 13: "outro", 14: "outro"})
for bar in range(15):
    t0 = bar * 2.0
    mode = groove_bars.get(bar)
    chord, root = CHORDS[bar % 4], ROOTS[bar % 4]
    if bar == 0:
        continue
    if mode in ("full", "light", "half"):
        for b in range(4):
            if mode == "half" and b % 2:
                continue
            place(drums, t0 + b * BEAT, kick(1.0 if mode != "light" else .75))
            sidechain(t0 + b * BEAT)
        if mode == "full":
            for b in (1, 3):
                place(drums, t0 + b * BEAT, clap())
        for s in range(8):
            place(drums, t0 + s * BEAT / 2, hat(.8 if s % 2 else .4, open_=(s % 4 == 2)), pan=0.3)
    if mode in ("full", "light", "half"):
        for s in range(8):  # bass on eighths, octave jump on the "and"
            if mode == "light" and s % 2:
                continue
            place(music, t0 + s * BEAT / 2, bass_pluck(root + (12 if s % 4 == 3 else 0)), gain=.9)
    if mode in ("full", "outro"):
        for s in (1, 3, 4, 6):  # syncopated mallet chords
            for k, m in enumerate(chord):
                place(music, t0 + s * BEAT / 2 + k * 0.012, mallet(m + 12, 0.5, bright=0.55), pan=-0.3 + 0.3 * k, gain=.42)
    if mode == "outro":
        place(music, t0, bass_pluck(root, 1.4), gain=.7)

# Hook: name letters.
place(sfx, 0.0, impact(0.8))
for i, at in enumerate(CUES["name_letters"]):
    place(sfx, at, pop(1 + i * 0.12), pan=-0.5 + i * 0.2)
    place(music, at, mallet(76 + [0, 3, 5, 7, 10, 12][i], 0.5), gain=.8)
place(sfx, CUES["name_swoosh"] - 0.1, whoosh(0.4, gain=.35))
place(sfx, 2.0, whoosh(0.5, gain=.4))

for i, at in enumerate(CUES["line1"] + CUES["line2"]):
    place(sfx, at - 0.06, swish(.3), pan=(-1) ** i * 0.5)
place(sfx, CUES["claude"], impact(1.0, sub=38))
place(sfx, CUES["claude"], sparkle(88, 5, 0.04), gain=.6)

for i, at in enumerate(CUES["mira"]):
    place(sfx, at, pop(1.3), pan=-0.4 + 0.4 * i)
for i, at in enumerate(CUES["letras"]):
    place(sfx, at, tick(1 + 0.1 * i), pan=-0.6 + 0.24 * i)
for i, at in enumerate(CUES["dinamicas_line"]):
    place(sfx, at - 0.05, swish(.28))
for i, at in enumerate(CUES["dinamicas"]):
    place(sfx, at, [pop(1.6 + 0.08 * i), tick(1.3), swish(.2)][i % 3], pan=-0.8 + 0.2 * i, gain=.9)
for at in CUES["seven"]:
    place(sfx, at, pop(0.9))
place(sfx, CUES["glitch"], glitch(0.5), gain=.9)
place(sfx, 11.6, whoosh(0.4, rising=True, gain=.45))

place(sfx, 12.0, digital_rise(1.5), gain=1.0)
for at in CUES["puedo"]:
    place(sfx, at, swish(.3))
place(sfx, CUES["three_d"], impact(0.9, sub=34))
for i, at in enumerate(CUES["shapes"]):
    place(sfx, at, mallet(84 + 3 * i, 0.4), pan=-0.5 + 0.5 * i)
    place(sfx, at, whoosh(0.25, gain=.2))
place(sfx, 14.6, whoosh(0.45, gain=.45))

for i, at in enumerate(CUES["esmas"]):
    place(sfx, at, typekey(), pan=-0.3 + 0.2 * i)
place(sfx, CUES["micro_title"] - 0.4, whoosh(0.5, rising=False, gain=.5))
place(sfx, CUES["micro_land"], impact(0.7, sub=50))
place(sfx, CUES["micro_land"], clunk(), gain=.8)
for i in range(18):  # caption typing
    place(sfx, CUES["desarma_text"] + i * 0.03, typekey(), gain=.5)
for i, at in enumerate(CUES["explode"]):
    place(sfx, at, clink(1.6 - i * 0.07, 0.8), pan=(-1) ** i * 0.6)
    place(sfx, at, whoosh(0.22, gain=.18), pan=(-1) ** i * 0.6)
place(sfx, 20.9, servo(1.2), gain=.9)
for i in range(18):
    place(sfx, CUES["construir_text"] + i * 0.03, typekey(), gain=.5)
for i, at in enumerate(CUES["assemble"]):
    place(sfx, at, snap(1.0 + 0.05 * i), pan=(-1) ** i * 0.5)
place(sfx, CUES["assembled"], clunk(), gain=1.0)
place(sfx, CUES["assembled"], sparkle(84), gain=.8)

for i, at in enumerate(CUES["cool"]):
    place(sfx, at, pop(1.2 + 0.1 * i))
place(sfx, CUES["verdad"], chime(88))
place(sfx, CUES["verdad"], chime(95), gain=.6)
place(sfx, 26.6, whoosh(0.4, gain=.4))
for i, at in enumerate(CUES["que"]):
    place(sfx, at, typekey(), gain=.9)
    place(sfx, at, pop(1.0 + 0.1 * i), gain=.5)
place(sfx, CUES["question"], boing(0.7))
place(sfx, CUES["end"], chime(81), gain=1.2)
place(sfx, CUES["end"], chime(88), gain=.7)


# ==== mix ============================================================================================
def room_ir(seconds=1.6):
    r = np.random.default_rng(4)
    t = t_ax(seconds)
    ir = np.stack([filt(r.standard_normal(len(t)), "lowpass", 6000) * np.exp(-t * 4.2) for _ in range(2)], 1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def limit(x, ceiling=0.79):
    k = int(0.004 * SR)
    env = uniform_filter1d(maximum_filter1d(np.max(np.abs(x), axis=1), size=2 * k + 1), size=k)
    return x * np.minimum(1, ceiling / np.maximum(env, 1e-9))[:, None]


if __name__ == "__main__":
    ir = room_ir()
    bed = music * duck[:, None] + drums
    send = music * 0.25 + sfx * 0.3
    verb = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], 1)
    mix = bed * 0.8 + sfx + verb * 0.35
    mix = filt(mix, "highpass", 25, order=4)
    tail = int(0.3 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)[:, None] ** 2
    meter = pyloudnorm.Meter(SR)
    for _ in range(4):
        mix *= 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
        mix = limit(mix)
    sf.write(HERE / "audio.wav", mix.astype(np.float32), SR)
    (HERE / "cues.js").write_text("window.CUES = " + json.dumps({**CUES, "cuts": CUTS, "bpm": BPM}) + ";\n")
    print(f"LUFS {meter.integrated_loudness(mix):.1f}, peak {20 * np.log10(np.max(np.abs(mix))):.1f} dBFS")
