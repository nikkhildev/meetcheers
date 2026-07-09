#!/usr/bin/env bash
# MeetCheers one-time setup.
#
# Builds a single virtual microphone — "MeetCheers-Mic" — that carries BOTH:
#   • your real microphone (so people hear you talk), AND
#   • the soundboard clips (so people hear the sounds you click).
#
# Also generates the starter sound pack. Idempotent — safe to re-run.
#
# After running, pick "MeetCheers-Mic" as the microphone in your meeting app.
set -euo pipefail

SINK_NAME="meetcheers"          # where the app plays sounds
MIX_SINK="meetcheers_mix"       # voice + sounds are mixed here
MIC_NAME="meetcheers_mic"       # the selectable virtual microphone
MODULE_TAG="meetcheers"         # label so we can find/clean our modules

echo "== MeetCheers setup =="

if ! command -v pactl >/dev/null 2>&1; then
  echo "ERROR: pactl not found. Install PipeWire (with pulse compat) or PulseAudio:" >&2
  echo "  Debian/Ubuntu: sudo apt install pipewire-pulse   (or pulseaudio-utils)" >&2
  echo "  Fedora:        sudo dnf install pipewire-pulseaudio" >&2
  exit 1
fi

# --- clean any previous MeetCheers modules so re-runs don't stack duplicates ---
# (loopbacks/null-sinks tagged with our sink/source names)
for mod in $(pactl list short modules | grep -E "sink_name=(${SINK_NAME}|${MIX_SINK})|source_name=${MIC_NAME}|sink=${MIX_SINK}|source=${SINK_NAME}\.monitor" | awk '{print $1}'); do
  pactl unload-module "$mod" 2>/dev/null || true
done

# --- 1. sink the soundboard app plays into -----------------------------------
pactl load-module module-null-sink \
  sink_name="${SINK_NAME}" \
  sink_properties=device.description=MeetCheers-Sounds >/dev/null
echo "• Created sound sink '${SINK_NAME}'."

# --- 2. mix sink (voice + sounds land here) ----------------------------------
pactl load-module module-null-sink \
  sink_name="${MIX_SINK}" \
  sink_properties=device.description=MeetCheers-Mix >/dev/null
echo "• Created mix sink '${MIX_SINK}'."

# --- 3. pipe your REAL microphone into the mix -------------------------------
REAL_MIC="$(pactl get-default-source 2>/dev/null || true)"
if [ -n "${REAL_MIC}" ] && [ "${REAL_MIC}" != "${MIC_NAME}" ]; then
  pactl load-module module-loopback \
    source="${REAL_MIC}" sink="${MIX_SINK}" latency_msec=30 >/dev/null
  echo "• Routed your real mic (${REAL_MIC}) into the mix."
else
  echo "• WARN: couldn't detect a real mic — sounds will still work, voice won't. Set your input in system settings and re-run." >&2
fi

# --- 4. pipe the soundboard into the mix -------------------------------------
pactl load-module module-loopback \
  source="${SINK_NAME}.monitor" sink="${MIX_SINK}" latency_msec=30 >/dev/null
echo "• Routed the soundboard into the mix."

# --- 5. expose the mix as a selectable microphone ----------------------------
pactl load-module module-remap-source \
  master="${MIX_SINK}.monitor" \
  source_name="${MIC_NAME}" \
  source_properties=device.description=MeetCheers-Mic >/dev/null
echo "• Created virtual mic 'MeetCheers-Mic' (your voice + sounds)."

# --- 5b. also play sounds on YOUR speakers so you can hear them too ----------
# (loops only the soundboard — NOT your mic — to your default output, so you
#  hear the clips but never echo your own voice.)
DEFAULT_SINK="$(pactl get-default-sink 2>/dev/null || true)"
if [ -n "${DEFAULT_SINK}" ] && [ "${DEFAULT_SINK}" != "${SINK_NAME}" ] && [ "${DEFAULT_SINK}" != "${MIX_SINK}" ]; then
  pactl load-module module-loopback \
    source="${SINK_NAME}.monitor" sink="${DEFAULT_SINK}" latency_msec=40 >/dev/null
  echo "• You will also hear clips on your speakers (${DEFAULT_SINK})."
fi

# --- 6. starter sounds (self-contained; generated, no downloads) -------------
if command -v python3 >/dev/null 2>&1; then
  python3 "$(dirname "$0")/scripts/make_starter_sounds.py"
else
  echo "WARN: python3 not found — starter sounds not generated." >&2
fi

echo
echo "Done ✅  In your meeting app, set microphone = 'MeetCheers-Mic'."
echo "It carries BOTH your voice and the soundboard."
echo "Launch the app with:  ./run.sh"
echo
echo "NOTE: virtual devices last until logout/reboot. Re-run ./setup.sh after a reboot."
echo "TIP:  turn OFF the meeting app's noise cancellation so clips aren't muffled."
