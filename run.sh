#!/usr/bin/env bash
# Launch MeetCheers. Checks prerequisites and gives clear fixes.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3." >&2
  exit 1
fi

# Tkinter check (packaged separately on Debian/Ubuntu).
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "ERROR: Python Tkinter is missing." >&2
  echo "  Debian/Ubuntu: sudo apt install python3-tk" >&2
  echo "  Fedora:        sudo dnf install python3-tkinter" >&2
  exit 1
fi

# Audio player check (warn only — app still opens).
if ! command -v pw-play >/dev/null 2>&1 \
   && ! command -v paplay >/dev/null 2>&1 \
   && ! command -v ffplay >/dev/null 2>&1; then
  echo "WARN: no audio player (pw-play/paplay/ffplay) found — playback will fail." >&2
  echo "  Debian/Ubuntu: sudo apt install pulseaudio-utils   (paplay)" >&2
fi

# Routing check (warn only).
if command -v pactl >/dev/null 2>&1; then
  if ! pactl list short sinks | grep -q "\bmeetcheers\b"; then
    echo "WARN: virtual sink not found — run ./setup.sh first so the meeting can hear you." >&2
  fi
fi

exec python3 meetcheers.py
