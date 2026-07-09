#!/usr/bin/env python3
"""Generate self-contained starter WAV clips (no external assets/deps).

Creates cheers/applause/airhorn as short synthesized clips so the app ships
with working buttons on any machine. Only used at setup time; runtime never
depends on this.
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SR = 44100
SOUNDS_DIR = Path(__file__).resolve().parent.parent / "sounds"


def _write(name: str, samples: list[float]) -> None:
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    peak = max(1e-6, max(abs(s) for s in samples))
    frames = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, s / peak)) * 32767 * 0.9))
        for s in samples
    )
    with wave.open(str(SOUNDS_DIR / name), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(frames)


def airhorn(dur: float = 1.2) -> list[float]:
    n = int(SR * dur)
    out = []
    for i in range(n):
        t = i / SR
        # Two detuned saw-ish tones for that horn blare.
        v = 0.0
        for f in (233.0, 311.0, 466.0):
            v += math.sin(2 * math.pi * f * t) + 0.5 * math.sin(4 * math.pi * f * t)
        env = min(1.0, t / 0.03) * min(1.0, (dur - t) / 0.1)
        out.append(v * env)
    return out


def applause(dur: float = 2.0) -> list[float]:
    rng = random.Random(42)
    n = int(SR * dur)
    out = [0.0] * n
    # Sum of many short noise bursts = clapping crowd.
    for _ in range(1400):
        start = rng.randint(0, n - 1)
        length = rng.randint(200, 600)
        amp = rng.uniform(0.3, 1.0)
        for j in range(length):
            if start + j >= n:
                break
            out[start + j] += amp * (rng.uniform(-1, 1)) * math.exp(-j / (length / 3))
    env = [min(1.0, i / (SR * 0.1)) * min(1.0, (n - i) / (SR * 0.3)) for i in range(n)]
    return [o * e for o, e in zip(out, env)]


def cheers(dur: float = 2.0) -> list[float]:
    rng = random.Random(7)
    n = int(SR * dur)
    out = [0.0] * n
    # Crowd "wooo" = filtered noise + rising vowel-ish formants.
    for i in range(n):
        t = i / SR
        base = 0.4 * rng.uniform(-1, 1)
        vowel = 0.6 * (math.sin(2 * math.pi * (300 + 120 * t) * t)
                       + 0.5 * math.sin(2 * math.pi * (900 + 200 * t) * t))
        out[i] = base + vowel
    env = [min(1.0, i / (SR * 0.15)) * min(1.0, (n - i) / (SR * 0.4)) for i in range(n)]
    return [o * e for o, e in zip(out, env)]


def main() -> None:
    targets = {
        "cheers.wav": cheers,
        "applause.wav": applause,
        "airhorn.wav": airhorn,
    }
    for fname, fn in targets.items():
        dest = SOUNDS_DIR / fname
        if dest.exists():
            continue  # don't overwrite user-kept files
        _write(fname, fn())
        print(f"created {dest}")


if __name__ == "__main__":
    main()
