#!/usr/bin/env python3
"""Generate the game's sound effects + a looping music bed as 16-bit mono WAVs
in `sfx/`.

Pure standard library (procedural synth + a hand-written WAV header), so it runs
anywhere with no pip installs. Run from this directory:

    python3 gen_sfx.py

The client embeds each WAV via include_bytes! and plays them with macroquad's
audio. Keep them short — they're uncompressed and ship inside the wasm module.
Tweak the synth params below and rerun to redraw the soundscape.
"""

import math
import os
import random
import struct

RATE = 22050  # sound effects
MUSIC_RATE = 11025  # music is longer; a lower rate keeps the WAV small


def write_wav(path, samples, rate=RATE):
    data = bytearray()
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * 32767)
        data += struct.pack("<h", v)
    n = len(data)
    hdr = b"RIFF" + struct.pack("<I", 36 + n) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    hdr += b"data" + struct.pack("<I", n)
    with open(path, "wb") as f:
        f.write(hdr + bytes(data))


def wave_at(phase, kind):
    p = phase % 1.0
    if kind == "sine":
        return math.sin(2 * math.pi * p)
    if kind == "square":
        return 1.0 if p < 0.5 else -1.0
    if kind == "saw":
        return 2.0 * p - 1.0
    if kind == "tri":
        return 4.0 * abs(p - 0.5) - 1.0
    return random.uniform(-1.0, 1.0)  # noise


def tone(freq, dur, kind="square", vol=0.5, decay=5.0, f_end=None, rate=RATE):
    """A single oscillator note with exponential decay and click-free edges."""
    n = int(dur * rate)
    out = [0.0] * n
    phase = 0.0
    fade = max(1, int(0.005 * rate))
    for i in range(n):
        t = i / rate
        f = freq if f_end is None else freq + (f_end - freq) * (i / n)
        phase += f / rate
        env = math.exp(-t * decay)
        edge = min(1.0, i / fade) * min(1.0, (n - i) / fade)
        out[i] = wave_at(phase, kind) * vol * env * edge
    return out


def pad(freq, dur, vol=0.18, rate=MUSIC_RATE):
    """An airy lead voice: a sine+triangle blend with gentle vibrato and a soft
    attack / slow release, for an ephemeral, floating melody."""
    n = int(dur * rate)
    out = [0.0] * n
    phase = 0.0
    atk = max(1, int(0.05 * rate))
    rel = max(1, int(0.18 * rate))
    for i in range(n):
        vib = 1.0 + 0.004 * math.sin(2 * math.pi * 5.0 * (i / rate))
        phase += (freq * vib) / rate
        s = 0.7 * math.sin(2 * math.pi * phase) + 0.3 * (4.0 * abs((phase % 1.0) - 0.5) - 1.0)
        env = min(1.0, i / atk) * min(1.0, (n - i) / rel)
        out[i] = s * vol * env
    return out


def noise(dur, vol=0.6, decay=7.0, lp=0.25, rate=RATE):
    """Low-passed white noise burst (the body of an explosion)."""
    n = int(dur * rate)
    out = [0.0] * n
    y = 0.0
    for i in range(n):
        y += lp * (random.uniform(-1.0, 1.0) - y)
        out[i] = y * vol * math.exp(-(i / rate) * decay)
    return out


def echo(track, delay, decay, rate):
    """Mix in one delayed, attenuated copy for a spacious tail."""
    d = int(delay * rate)
    out = list(track) + [0.0] * d
    for i, v in enumerate(track):
        out[i + d] += v * decay
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def add_into(dst, src, offset):
    for i, v in enumerate(src):
        j = offset + i
        if 0 <= j < len(dst):
            dst[j] += v


def seq(*notes):
    out = []
    for nlist in notes:
        out.extend(nlist)
    return out


# --- one-shot effects ------------------------------------------------------
def sfx_place():
    return mix(tone(240, 0.13, "square", 0.5, 22.0, f_end=110), noise(0.03, 0.25, 30.0))


def sfx_explode():
    return mix(
        noise(0.55, 0.7, 6.5, lp=0.18),
        tone(80, 0.5, "sine", 0.8, 6.0, f_end=38),
        tone(160, 0.2, "saw", 0.3, 14.0, f_end=60),
    )


def sfx_pickup():
    return seq(tone(660, 0.07, "square", 0.4, 9.0), tone(990, 0.11, "square", 0.4, 7.0))


def sfx_death():
    return mix(tone(440, 0.5, "saw", 0.5, 4.5, f_end=90), noise(0.25, 0.2, 9.0))


def sfx_beep():
    return tone(720, 0.10, "square", 0.45, 11.0)


def sfx_go():
    return tone(660, 0.22, "square", 0.5, 4.0, f_end=1320)


def sfx_win():
    return seq(
        tone(523, 0.12, "square", 0.45, 4.0),
        tone(659, 0.12, "square", 0.45, 4.0),
        tone(784, 0.12, "square", 0.45, 4.0),
        tone(1047, 0.30, "square", 0.5, 3.0),
    )


def sfx_ready():
    """A bright two-note up-chime for readying up in the lobby."""
    return seq(tone(587, 0.05, "square", 0.4, 9.0), tone(880, 0.11, "square", 0.4, 7.0))


def sfx_unready():
    """A short down-blip for un-readying."""
    return tone(523, 0.11, "square", 0.35, 9.0, f_end=311)


# --- music -----------------------------------------------------------------
A4, B4, C5, D5, E5, F5, G5, A5 = 440, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99, 880.0


def music():
    """A continuously looping chiptune. The chord bed (triangle bass + light
    square arpeggio) runs the whole time; an airy lead melody fades in after two
    cycles, plays a long through-composed line over the next three, then drops
    out for a cycle before the whole ~31s track loops."""
    R = MUSIC_RATE
    beat = 0.16
    bar = beat * 8
    cycle = bar * 4  # one chord progression (Am-F-C-G)
    reps = 6
    total = cycle * reps
    out = [0.0] * int(total * R)

    chords = [
        (110.0, [220.0, 261.63, 329.63]),  # Am
        (87.31, [174.61, 220.0, 261.63]),  # F
        (130.81, [261.63, 329.63, 392.0]),  # C
        (98.0, [196.0, 246.94, 293.66]),  # G
    ]
    # Bed on every cycle (always running).
    for rep in range(reps):
        bed = []
        for root, tones in chords:
            bass = tone(root, bar, "tri", 0.15, 0.7, rate=R)
            arp = []
            for k in range(8):
                arp.extend(tone(tones[k % len(tones)], beat, "square", 0.07, 6.0, rate=R))
            bed.extend(mix(bass, arp))
        add_into(out, bed, int(rep * cycle * R))

    # A 12-bar (3-cycle) through-composed melody; each bar sums to 8 sixteenths.
    # `None` is a rest. Long notes + rests + the airy pad voice give it space.
    melody = [
        (E5, 4), (None, 2), (A5, 2),   # Am
        (G5, 4), (F5, 4),              # F
        (E5, 4), (G5, 2), (None, 2),   # C
        (D5, 8),                       # G
        (C5, 2), (E5, 2), (A5, 4),     # Am
        (None, 2), (F5, 4), (E5, 2),   # F
        (G5, 4), (E5, 4),              # C
        (D5, 4), (B4, 2), (None, 2),   # G
        (A5, 8),                       # Am
        (G5, 4), (A5, 4),              # F
        (G5, 2), (E5, 2), (C5, 4),     # C
        (D5, 8),                       # G
    ]
    mel = []
    for freq, length in melody:
        if freq is None:
            mel.extend([0.0] * int(length * beat * R))
        else:
            mel.extend(pad(freq, length * beat, 0.18, R))
    mel = echo(mel, 0.22, 0.4, R)
    add_into(out, mel, int(2 * cycle * R))  # melody enters after two cycles
    return out, R


# --- write -----------------------------------------------------------------
EFFECTS = {
    "place": sfx_place,
    "explode": sfx_explode,
    "pickup": sfx_pickup,
    "death": sfx_death,
    "beep": sfx_beep,
    "go": sfx_go,
    "win": sfx_win,
    "ready": sfx_ready,
    "unready": sfx_unready,
}

os.makedirs("sfx", exist_ok=True)
for name, fn in EFFECTS.items():
    samples = fn()
    write_wav(os.path.join("sfx", name + ".wav"), samples, RATE)
    print(f"wrote sfx/{name}.wav  {len(samples) / RATE:.2f}s  {len(samples) * 2} bytes")

m, mr = music()
write_wav("sfx/music.wav", m, mr)
print(f"wrote sfx/music.wav  {len(m) / mr:.2f}s  {len(m) * 2} bytes @ {mr}Hz")
