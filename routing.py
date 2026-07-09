"""Detects whether the MeetCheers virtual sink/source exist."""
from __future__ import annotations

import shutil
import subprocess

SINK_NAME = "meetcheers"
SOURCE_NAME = "meetcheers_mic"


def _pactl_list(kind: str) -> str:
    """Return `pactl list short <kind>` output, or '' on any failure."""
    if not shutil.which("pactl"):
        return ""
    try:
        out = subprocess.run(
            ["pactl", "list", "short", kind],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def sink_exists() -> bool:
    return SINK_NAME in _pactl_list("sinks")


def source_exists() -> bool:
    return SOURCE_NAME in _pactl_list("sources")


def status() -> tuple[bool, str]:
    """Return (ok, human message) describing routing readiness."""
    if not shutil.which("pactl"):
        return False, "pactl not found — is PipeWire/PulseAudio installed?"
    have_sink = sink_exists()
    have_source = source_exists()
    if have_sink and have_source:
        return True, "Routing: MeetCheers ✅  (set meeting mic = MeetCheers-Mic)"
    if not have_sink and not have_source:
        return False, "Routing not set up — run ./setup.sh"
    return False, "Routing incomplete — re-run ./setup.sh"
