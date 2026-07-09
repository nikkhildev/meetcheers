"""Audio playback: plays a file into the MeetCheers virtual sink.

Uses PipeWire's pw-play when available, falling back to PulseAudio's paplay.
Each play spawns its own subprocess so clicks are non-blocking and overlapping
sounds are allowed (typical soundboard behaviour).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SINK_NAME = "meetcheers"


def player_available() -> str | None:
    """Return the name of an available player binary, or None."""
    for binary in ("pw-play", "paplay", "ffplay"):
        if shutil.which(binary):
            return binary
    return None


def _command(binary: str, file: Path, target_sink: bool) -> list[str]:
    if binary == "pw-play":
        cmd = ["pw-play"]
        if target_sink:
            cmd += [f"--target={SINK_NAME}"]
        cmd += [str(file)]
        return cmd
    if binary == "paplay":
        cmd = ["paplay"]
        if target_sink:
            cmd += [f"--device={SINK_NAME}"]
        cmd += [str(file)]
        return cmd
    # ffplay: no reliable device targeting; plays to default. Used only as a
    # last-resort fallback so the app still makes noise.
    return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(file)]


def play(file: str | Path, sink_exists: bool = True) -> subprocess.Popen | None:
    """Play `file`. Targets the MeetCheers sink when it exists; otherwise plays
    to the default output so the app never hard-fails. Returns the Popen handle
    (or None if no player is installed / file missing)."""
    file = Path(file)
    if not file.is_file():
        return None
    binary = player_available()
    if binary is None:
        return None
    cmd = _command(binary, file, target_sink=sink_exists and binary in ("pw-play", "paplay"))
    try:
        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
