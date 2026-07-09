#!/usr/bin/env bash
# MeetCheers one-time setup: create the virtual sink + virtual mic, and
# generate the starter sound pack. Idempotent — safe to re-run.
set -euo pipefail

SINK_NAME="meetcheers"
SOURCE_NAME="meetcheers_mic"

echo "== MeetCheers setup =="

if ! command -v pactl >/dev/null 2>&1; then
  echo "ERROR: pactl not found. Install PipeWire (with pulse compat) or PulseAudio:" >&2
  echo "  Debian/Ubuntu: sudo apt install pipewire-pulse   (or pulseaudio-utils)" >&2
  echo "  Fedora:        sudo dnf install pipewire-pulseaudio" >&2
  exit 1
fi

# 1. Virtual sink the app plays into.
if pactl list short sinks | grep -q "\b${SINK_NAME}\b"; then
  echo "• Sink '${SINK_NAME}' already exists — skipping."
else
  pactl load-module module-null-sink \
    sink_name="${SINK_NAME}" \
    sink_properties=device.description=MeetCheers >/dev/null
  echo "• Created sink '${SINK_NAME}'."
fi

# 2. Expose the sink's monitor as a virtual microphone.
if pactl list short sources | grep -q "\b${SOURCE_NAME}\b"; then
  echo "• Source '${SOURCE_NAME}' already exists — skipping."
else
  pactl load-module module-remap-source \
    master="${SINK_NAME}.monitor" \
    source_name="${SOURCE_NAME}" \
    source_properties=device.description=MeetCheers-Mic >/dev/null
  echo "• Created virtual mic 'MeetCheers-Mic'."
fi

# 3. Starter sounds (self-contained; generated, no downloads).
if command -v python3 >/dev/null 2>&1; then
  python3 "$(dirname "$0")/scripts/make_starter_sounds.py"
else
  echo "WARN: python3 not found — starter sounds not generated." >&2
fi

echo
echo "Done. In your meeting app, set microphone = 'MeetCheers-Mic'."
echo "Then launch the app with:  ./run.sh"
echo
echo "NOTE: virtual devices last until logout/reboot. Re-run ./setup.sh after a reboot."
