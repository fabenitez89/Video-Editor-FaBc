"""Étude for piano and machine: an original 60 s piano score plus sound design, synthesized from physics.

No samples and no pads. Every note is a struck stiff string: inharmonic partials, two or three detuned
unison strings, two-stage decay, velocity-dependent hammer brightness, dampers and sustain pedal, then a
soundboard body and a room. The sound design is built from the same instrument: muted strings, lid
knocks, reversed piano, a tremolo riser.

Usage: python3 films/etude/score.py   (writes audio.wav and notes.js beside this file)
"""
import json
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pyloudnorm
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 96
BEAT = 60 / BPM          # 0.625 s
BAR = 4 * BEAT           # 2.5 s, 24 bars = 60 s
LENGTH = 60.0
HERE = Path(__file__).parent
N = int(SR * LENGTH)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(sig, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=SR, output="sos"), sig, axis=0)


# ==== composition ===========================================================================
# Chords as (low root, third interval).
CHORDS = {"Dm": (38, 3), "Bb": (34, 4), "F": (41, 4), "C": (36, 4), "Gm": (43, 3), "A": (45, 4)}
PROGRESSION = ["Dm", "Bb", "F", "C"] * 3 + ["Gm", "Bb", "Dm", "A"] + ["Dm", "Bb", "F", "C", "Gm", "A"] + ["Dm", "Dm"]
SECTIONS = [  # (first bar, name)
    (0, "intro"), (4, "theme"), (8, "development"), (12, "breakdown"), (16, "climax"), (22, "coda"),
]

notes = []  # beats-based events: b (beat), m (midi), v (velocity 0-1), d (beats held), voice
rng_h = np.random.default_rng(1996)


def add(b, m, v, d, voice, dark=False):
    notes.append({"b": b, "m": int(m), "v": float(v), "d": float(d), "voice": voice, "dark": dark})


def lh_eighths(bar, vel, octave=0):
    r, q = CHORDS[PROGRESSION[bar]]
    r += octave
    pattern = [r, r + 7, r + 12, r + 12 + q, r + 19, r + 12 + q, r + 12, r + 7]
    for i, m in enumerate(pattern):
        accent = 1.12 if i == 0 else 1.0 if i % 2 == 0 else 0.9
        add(bar * 4 + i * 0.5, m, vel * accent, 0.5, "lh")


def arp16(bar, vel, octave=24):
    r, q = CHORDS[PROGRESSION[bar]]
    tones = [r + octave, r + octave + q, r + octave + 7, r + octave + 12, r + octave + 12 + q, r + octave + 19]
    order = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3]
    accents = {0, 3, 6, 8, 11, 14}  # 3+3+2 against the four-square bar
    for i, k in enumerate(order):
        add(bar * 4 + i * 0.25, tones[k], vel * (1.45 if i in accents else 1.0), 0.25, "arp")


# Intro (bars 1-4): a motif on bare roots, one string at a time.
INTRO = [(0, 74, .62), (2.5, 69, .45), (4, 77, .6), (6.5, 74, .45),
         (8, 81, .64), (10.5, 72, .45), (12, 79, .6), (14, 76, .5), (15, 72, .45), (15.5, 69, .5)]
for b, m, v in INTRO:
    add(b, m, v, 1.5 if b % 4 == 0 else 1.0, "motif")
for bar in range(4):
    r, _ = CHORDS[PROGRESSION[bar]]
    add(bar * 4, r, .4, 4, "bass")
    add(bar * 4, r + 12, .34, 4, "bass")

# Theme (bars 5-8).
MELODY = [(0, 74, 1.5), (1.5, 76, .5), (2, 77, 1), (3, 81, 1),
          (4, 79, 1.5), (5.5, 77, .5), (6, 74, 2),
          (8, 72, 1.5), (9.5, 74, .5), (10, 77, 1), (11, 81, 1),
          (12, 79, 1.5), (13.5, 77, .5), (14, 76, 2)]
for b, m, d in MELODY:
    add(16 + b, m, .74 if d >= 1.5 else .64, d, "melody")
for bar in range(4, 8):
    lh_eighths(bar, .42)

# Development (bars 9-12): sixteenths in 3+3+2, bells on the syncopation.
for bar in range(8, 12):
    lh_eighths(bar, .48)
    arp16(bar, .32)
    r, q = CHORDS[PROGRESSION[bar]]
    add(bar * 4, r + 48, .58, 2, "bell")
    add(bar * 4 + 2.5, r + 48 + q, .5, 1.5, "bell")

# Breakdown (bars 13-16): una corda, high register, then an accelerating tremolo into the climax.
for bar in range(12, 15):
    r, q = CHORDS[PROGRESSION[bar]]
    add(bar * 4, r - 12 if r > 40 else r, .3, 4, "bass", dark=True)
    add(bar * 4, r + 12, .26, 4, "bass", dark=True)
    top = r + 48 if r + 48 <= 93 else r + 36
    for b, m, v in [(0, top, .42), (1.5, top - 12 + q + 0, .32), (3, top - 12 + 7, .3)]:
        add(bar * 4 + b, m, v, 1.5, "high", dark=True)
add(60, 33, .4, 4, "bass")
add(60, 45, .34, 4, "bass")
b, step, i = 0.0, 0.5, 0
while b < 3.95:  # tremolo A5/E5, eighths accelerating to thirty-seconds, crescendo
    p = b / 4
    add(60 + b, [81, 76][i % 2], .26 + .7 * p ** 1.8, step, "tremolo")
    b += step
    step = max(0.125, step * 0.86)
    i += 1

# Climax (bars 17-22): octave bass, melody in octaves, sixteenths on top.
CLIMAX = MELODY + [(16, 82, 1.5), (17.5, 81, .5), (18, 79, 1), (19, 74, 1), (20, 73, 1.5), (21.5, 76, .5), (22, 81, 2)]
for b, m, d in CLIMAX:
    add(64 + b, m, .92 if d >= 1.5 else .84, d, "melody")
    add(64 + b, m - 12, .7, d, "melody")
for bar in range(16, 22):
    r, _ = CHORDS[PROGRESSION[bar]]
    for beat in (0, 2):
        add(bar * 4 + beat, r - 12, .8, 2, "bass")
        add(bar * 4 + beat, r, .74, 2, "bass")
    lh_eighths(bar, .5, octave=12 if r < 40 else 0)
    if bar >= 17:
        arp16(bar, .24, octave=36 if r < 40 else 24)

# Coda (bars 23-24): a rolled D minor add9, then one high D left ringing.
for k, m in enumerate([38, 45, 50, 53, 57, 64, 65, 69, 74]):
    add(88 + k * 0.07, m, .72 - k * 0.03, 6, "coda")
add(90, 81, .38, 4, "coda")
add(91, 76, .32, 3, "coda")
add(92, 86, .4, 2, "coda")
add(92, 74, .26, 2, "coda")

# Sustain pedal: changed at each bar line; held through the coda until it is released at 59.2 s.
PEDAL_UP = [bar * BAR - 0.03 for bar in range(1, 23)] + [59.2]


# ==== the instrument ========================================================================
def piano_note(args):
    """One struck note. Returns mono float32 samples starting at the hammer strike."""
    m, v, ring, seed, dark = args
    rng = np.random.default_rng(seed)
    f0 = hz(m)
    key = (m - 21) / 87
    bright = v * (0.72 if dark else 1.0)
    B = 0.00022 if m < 40 else 0.0001 * 2 ** ((m - 60) / 17)          # string stiffness
    sustain = 16 * (1 - key) ** 1.6 + 0.9                                # aftersound of the fundamental, s
    damp_tau = 0.16 if m < 45 else 0.065 if m < 89 else 9.0             # top octaves have no dampers
    L = int(SR * min(ring + 7 * min(damp_tau, sustain), 7 * sustain, 12))
    t = np.arange(L, dtype=np.float32) / SR

    n = np.arange(1, int(min(64, 15000 / f0)) + 1)
    fn = n * f0 * np.sqrt(1 + B * n * n)
    strike = 1 / 8.3                                                     # hammer at 1/8 of the string
    amp = (np.abs(np.sin(np.pi * n * strike)) + 0.05) / n ** (2.35 - 1.05 * bright)
    fc = (650 + 5600 * bright ** 1.6) * (f0 / 262) ** 0.3               # felt hardens with velocity
    amp *= 1 / np.sqrt(1 + (fn / fc) ** 4) * rng.uniform(0.8, 1.2, len(n))
    amp *= 1 / np.sqrt(1 + (140 / fn) ** 4)                             # soundboard barely radiates the low fundamentals
    amp[fn > 18000] = 0
    tau_slow = sustain / (1 + (fn / 1500) ** 1.25)
    tau_fast = tau_slow * 0.11
    prompt = 0.6 + 0.25 * bright                                         # share of the fast first stage
    strings = 1 if m < 32 else 2 if m < 44 else 3
    detune = 2 ** (rng.uniform(-1.4, 1.4, strings) / 1200)

    out = np.zeros(L, dtype=np.float32)
    for i in np.nonzero(amp)[0]:
        env = amp[i] * (prompt * np.exp(-t / tau_fast[i]) + (1 - prompt) * np.exp(-t / tau_slow[i]))
        osc = np.zeros(L, dtype=np.float32)
        for d in detune:
            osc += np.sin(2 * np.pi * fn[i] * d * t + rng.uniform(0, 0.4))
        out += env * osc / strings
    out *= np.minimum(1, t / (0.0012 + 0.004 * (1 - v)))                # hammer contact time
    if ring < t[-1]:
        out *= np.exp(-np.maximum(t - ring, 0) / damp_tau).astype(np.float32)

    k = int(0.014 * SR)                                                  # felt thump and key-bed knock
    thump = rng.standard_normal(k) * np.exp(-np.arange(k) / SR / 0.003)
    out[:k] += filt(thump, "lowpass", 500 + 3500 * v) * 0.05 * v
    return (out * v ** 1.7).astype(np.float32)


def render_notes(evts):
    jobs = [(e["m"], e["v"], e["ring"], e["seed"], e["dark"]) for e in evts]
    with Pool(os.cpu_count()) as pool:
        return pool.map(piano_note, jobs, chunksize=4)


# ==== timing: beats -> seconds, humanize, pedal =============================================
for i, e in enumerate(notes):
    jitter = 0 if e["voice"] in ("bass", "coda") else rng_h.normal(0, 0.004)
    e["t"] = max(0.0, e["b"] * BEAT + jitter)
    e["v"] = float(np.clip(e["v"] + rng_h.normal(0, 0.025), 0.05, 1.0))
    off = e["t"] + e["d"] * BEAT
    pedal_up = next((p for p in PEDAL_UP if p >= off - 1e-6), LENGTH)
    e["ring"] = pedal_up - e["t"]
    e["seed"] = 1000 + i


# ==== sound design from the same instrument =================================================
rng = np.random.default_rng(60)
t_ax = lambda dur: np.arange(int(SR * dur)) / SR


def muted_kick(v):
    t = t_ax(0.5)
    body = np.sin(2 * np.pi * np.cumsum(42 + 60 * np.exp(-t * 30)) / SR) * np.exp(-t * 7)
    string = piano_note((26, 0.9, 0.0, 7, True))[: len(t)]
    string = np.pad(string, (0, len(t) - len(string)))
    return (filt(np.tanh(body * 1.3), "highpass", 38) * 0.5 + string * 3.0) * v


def lid_knock(v):
    t = t_ax(0.3)
    modes = [(190, .045, 1), (412, .028, .6), (980, .016, .35), (1830, .009, .2)]
    sig = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, d, a in modes)
    click = filt(rng.standard_normal(len(t)), "highpass", 2500) * np.exp(-t / 0.0015) * 0.6
    buzz = filt(rng.standard_normal(len(t)), "bandpass", [1800, 5200]) * (np.sign(np.sin(2 * np.pi * 63 * t)) > 0) * np.exp(-t / 0.05) * 0.18
    return (sig * 0.5 + click + buzz) * v


def string_tick(v):
    t = t_ax(0.08)
    sig = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012) for f in (5230, 7140, 8870, 11320)) / 4
    sig += filt(rng.standard_normal(len(t)), "highpass", 6000) * np.exp(-t / 0.002) * 0.5
    return sig * v * 0.5


def felt_boom(v):
    """Low piano cluster struck with the palm, plus the sub it implies."""
    parts = [piano_note((m, 1.0, 0.9, 50 + m, True)) for m in (21, 26, 33)]
    L = max(len(p) for p in parts)
    cl = sum(np.pad(p, (0, L - len(p))) for p in parts)
    t = np.arange(L) / SR
    sub = np.sin(2 * np.pi * np.cumsum(34 + 26 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.8)
    return (filt(np.tanh(sub * 1.5), "highpass", 30) * 0.45 + cl * 1.4) * v


def pedal_release():
    """Dampers landing on ringing strings: a soft felt slap and a short mechanical rattle."""
    t = t_ax(0.4)
    slap = filt(rng.standard_normal(len(t)), "lowpass", 900) * np.exp(-t / 0.03)
    clunk = np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.04)
    return (slap * 0.25 + clunk * 0.3)


def air(dur, rising=True):
    t = t_ax(dur)
    sig = filt(rng.standard_normal(len(t)), "bandpass", [400, 9000])
    lo = filt(sig, "lowpass", 1200)
    p = t / dur if rising else 1 - t / dur
    shaped = lo * (1 - p) + (sig - lo) * p
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return shaped * env * 0.22


PERC = []   # (time, kind, velocity)
SFX = []    # (time, kind, extra)
for bar in list(range(8, 12)) + list(range(16, 22)):
    t0 = bar * BAR
    climax = bar >= 16
    for b in ([0, 1.5, 2.5] if not climax else [0, 1.5, 2, 3.5]):
        PERC.append((t0 + b * BEAT, "kick", .9 if b == 0 else .7))
    for b in (1, 3):
        PERC.append((t0 + b * BEAT, "knock", .8 if climax else .65))
    for s in range(16):
        PERC.append((t0 + s * BEAT / 4, "tick", (.55 if s % 2 else .3) * (1.2 if climax else 1)))
for at, v in [(0.0, .7), (4 * BAR, .55), (8 * BAR, .8), (16 * BAR, 1.0), (22 * BAR, .7)]:
    SFX.append((at, "boom", v))
SFX.append((59.2, "pedal", 1.0))
for at, dur, rising in [(27.0, 1.2, True), (49.2, 0.8, True)]:
    SFX.append((at, "air", (dur, rising)))
SWELLS = [(4 * BAR, 1.6, [62, 69, 74, 77], .7), (16 * BAR, 2.6, [38, 50, 57, 62, 65, 69, 74], 1.0), (8 * BAR, 1.2, [62, 65, 69, 74], .6)]


# ==== space =================================================================================
def body_ir():
    r = np.random.default_rng(5)
    t = t_ax(0.18)
    f = np.exp(r.uniform(np.log(90), np.log(4500), 70))
    d = r.uniform(0.008, 0.06, 70)
    a = r.choice([-1, 1], 70) * r.uniform(0.5, 1.0, 70) / np.sqrt(d / 0.02)  # equal energy per mode
    ir = (a[:, None] * np.sin(2 * np.pi * f[:, None] * t) * np.exp(-t / d[:, None])).sum(0)
    # Flatten the average response so the body adds grain and bloom, not an EQ tilt.
    nfft = 1 << 15
    H = np.fft.rfft(ir, nfft)
    mag = np.abs(H)
    smooth = np.exp(np.convolve(np.log(mag + 1e-9), np.ones(301) / 301, mode="same"))
    ir = np.fft.irfft(H / smooth, nfft)[: len(t)] * np.hanning(2 * len(t))[len(t):]
    return ir / np.sqrt(np.sum(ir ** 2))


def room_ir(seconds=3.4):
    r = np.random.default_rng(9)
    t = t_ax(seconds)
    ir = np.zeros((len(t), 2))
    for ch in range(2):
        for lo, hi, rt in [(60, 250, 2.9), (250, 900, 2.5), (900, 2800, 2.0), (2800, 7000, 1.3), (7000, 16000, .6)]:
            band = filt(r.standard_normal(len(t)), "bandpass", [lo, hi])
            ir[:, ch] += band * np.exp(-6.9 * t / rt)
        for _ in range(14):  # early reflections
            k = int(r.uniform(0.006, 0.07) * SR)
            ir[k, ch] += r.uniform(0.3, 1.0) * r.choice([-1, 1]) * 4
    pre = int(0.014 * SR)
    ir = np.concatenate([np.zeros((pre, 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def place(bus, at, sig, gains=(1.0, 1.0)):
    i = int(round(at * SR))
    if i >= len(bus):
        return
    j = min(len(bus), i + len(sig))
    bus[i:j, 0] += sig[: j - i] * gains[0]
    bus[i:j, 1] += sig[: j - i] * gains[1]


def pan(m):
    p = np.clip((m - 64) / 44, -1, 1) * 0.45   # player's perspective: bass left, treble right
    return (np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4))


def compress(x, thresh_db=-20, ratio=2.2, attack=0.01, release=0.18):
    level = np.sqrt(np.maximum(filt(np.mean(x ** 2, axis=1), "lowpass", 8), 0))
    level_db = 20 * np.log10(np.maximum(level, 1e-6))
    gain_db = np.minimum(0, (thresh_db - level_db) * (1 - 1 / ratio))
    # smooth gain with attack/release one-pole filters
    g = np.empty_like(gain_db)
    a_a, a_r, prev = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR)), 0.0
    for i, target in enumerate(gain_db):
        coef = a_a if target < prev else a_r
        prev = coef * prev + (1 - coef) * target
        g[i] = prev
    return x * (10 ** (g / 20))[:, None]


def limit(x, ceiling=0.89, look=0.004):
    k = int(look * SR)
    peak = np.max(np.abs(x), axis=1)
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    env = maximum_filter1d(peak, size=2 * k + 1)
    env = uniform_filter1d(env, size=k)
    env = np.maximum(env, 1e-9)
    gain = np.minimum(1, ceiling / env)
    return x * gain[:, None]


if __name__ == "__main__":
    piano = np.zeros((N, 2))
    for e, sig in zip(notes, render_notes(notes)):
        place(piano, e["t"], sig, pan(e["m"]))

    # Reversed swells: the target chord's reverb, played backwards, landing on the downbeat.
    room = room_ir()
    sfx = np.zeros((N, 2))
    for target, dur, chord, v in SWELLS:
        sigs = [piano_note((m, .8, 6, 300 + m, False)) for m in chord]
        L = max(len(s) for s in sigs)
        mono = sum(np.pad(s, (0, L - len(s))) for s in sigs)
        wet = np.stack([fftconvolve(mono, room[:, c])[: int(dur * SR)] for c in range(2)], 1)[::-1]
        wet *= (np.linspace(0, 1, len(wet)) ** 2.2)[:, None]
        wet /= np.max(np.abs(wet)) + 1e-9
        i = int(target * SR) - len(wet)
        sfx[max(0, i): i + len(wet)] += wet[max(0, -i):] * 0.32 * v

    perc = np.zeros((N, 2))
    cache = {}
    for at, kind, v in PERC:
        if kind not in cache:
            cache[kind] = {"kick": lambda: muted_kick(1.0), "knock": lambda: lid_knock(1.0), "tick": lambda: string_tick(1.0)}[kind]()
        sig = cache[kind] * v
        g = {"kick": (0.7, 0.7), "knock": (0.62, 0.78), "tick": (0.8, 0.55)}[kind]
        place(perc, at, sig, g)

    for at, kind, extra in SFX:
        if kind == "boom":
            place(sfx, at, felt_boom(extra) * 0.55)
        elif kind == "pedal":
            place(sfx, at, pedal_release())
        elif kind == "air":
            dur, rising = extra
            sig = air(dur, rising)
            place(sfx, at, sig, (0.45, 0.25))
            place(sfx, at + 0.012, sig, (0.2, 0.45))  # a small Haas offset gives it width

    body = body_ir()
    piano = piano * 0.75 + np.stack([fftconvolve(piano[:, c], body)[:N] for c in range(2)], 1) * 0.3
    send = piano * 0.3 + perc * 0.12 + sfx * 0.4
    verb = np.zeros((N, 2))
    for c in range(2):
        verb[:, c] = fftconvolve(send[:, c], room[:, c])[:N]
    mix = piano + perc * 0.55 + sfx + verb * 0.55
    if os.environ.get("STEMS"):  # per-bus files for mix analysis
        import soundfile as sf
        for name, bus in [("piano", piano), ("perc", perc * 0.55), ("sfx", sfx), ("verb", verb * 0.55)]:
            sf.write(HERE / f"stem-{name}.wav", bus.astype(np.float32), SR)

    tail = int(0.4 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)[:, None] ** 2
    mix = filt(mix, "highpass", 28, order=4)
    mix -= 0.3 * filt(mix, "lowpass", 90)  # gentle low shelf, about -3 dB below 90 Hz
    mix = compress(mix)
    meter = pyloudnorm.Meter(SR)
    mix *= 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
    for _ in range(3):  # limiting lowers loudness a little; converge on -14 LUFS
        mix = limit(mix)
        mix *= 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
    mix = limit(mix)

    import soundfile as sf
    sf.write(HERE / "audio.wav", mix.astype(np.float32), SR)

    # Score for the film: every note and hit, in seconds.
    film = {
        "bpm": BPM, "beat": BEAT, "bar": BAR,
        "sections": [{"bar": b, "t": b * BAR, "name": n} for b, n in SECTIONS],
        "chords": PROGRESSION,
        "notes": [{"t": round(e["t"], 4), "m": e["m"], "v": round(e["v"], 3), "end": round(e["t"] + e["ring"], 4),
                   "d": round(e["d"] * BEAT, 4), "voice": e["voice"]} for e in notes],
        "perc": [{"t": round(a, 4), "kind": k, "v": round(v, 3)} for a, k, v in PERC],
        "sfx": [{"t": round(a, 4), "kind": k} for a, k, _ in SFX] + [{"t": round(s[0] - s[1], 4), "kind": "swell", "end": s[0]} for s in SWELLS],
    }
    (HERE / "notes.js").write_text("window.SCORE = " + json.dumps(film) + ";\n")
    print(f"{len(notes)} notes, {len(PERC)} hits; LUFS {meter.integrated_loudness(mix):.1f}, peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS")
