# MeetCheers — Design Spec

**Date:** 2026-07-09
**Owner:** Nikhil
**Status:** Approved design, pre-implementation
**Build:** Local Python + Tkinter desktop soundboard (Linux / PipeWire)

## Purpose

A small desktop soundboard app. Click a button → a sound clip (cheers, applause, airhorn)
plays into a **virtual microphone** so that **everyone in the meeting hears it**. Works with
ANY meeting app (Google Meet, Zoom, Teams, Discord) because it operates at the OS audio layer,
not inside the browser.

## Why not a Chrome extension

The extension only plays audio and would still need the identical Linux virtual-mic setup —
so it adds Chrome/MV3 friction and works only for browser-based meetings, while buying nothing
the routing didn't already provide. A local GUI app is simpler, meeting-app-agnostic, and just
as shareable.

## Constraints & key facts

- **Target OS:** Linux with PipeWire (or PulseAudio compatibility layer). Default on modern
  Ubuntu/Fedora.
- A soundboard cannot inject audio into a real mic. The meeting app only transmits its selected
  mic. So a one-time OS-level virtual-audio setup is required (scripted, see below).
- The app plays a clip to a chosen **output device** = the virtual sink. The sink's monitor is
  exposed as a **virtual mic** the meeting app selects.
- **Zero heavy deps:** Tkinter ships with Python 3. Audio playback + device targeting done via
  a PipeWire/Pulse-aware player (`paplay`/`pw-play`, already present on target systems) so the
  app can direct a clip to a specific sink by name.

## One-time OS setup — scripted (`setup.sh`)

`setup.sh` runs these (idempotent — checks before re-adding):

```bash
# Virtual sink the app plays into
pactl load-module module-null-sink \
  sink_name=meetcheers \
  sink_properties=device.description=MeetCheers

# Expose that sink's monitor as a virtual microphone for the meeting app
pactl load-module module-remap-source \
  master=meetcheers.monitor \
  source_name=meetcheers_mic \
  source_properties=device.description=MeetCheers-Mic
```

Then in the meeting app: set **microphone = MeetCheers-Mic**.

> Optional (documented, not built for v1): a `module-loopback` from the sink to your real output
> so you also hear the clips yourself.

## Architecture

Single Python process, three logical parts.

### 1. GUI (`meetcheers.py` — Tkinter)
- A resizable window with a **grid of buttons**, one per sound.
- **"＋ Add sound"** button → native file picker (`.wav`, `.mp3`, `.ogg`) → copies file into the
  app's `sounds/` dir and adds a button.
- **Delete** affordance per sound (right-click or a small ✕).
- A **status line** showing the target sink and whether it exists ("Routing: MeetCheers ✅"
  or a warning + hint to run `setup.sh`).
- Clicking a button triggers playback (part 3). Non-blocking (UI stays responsive).

### 2. Sound library (`library.py`)
- Manages the `sounds/` folder + a small `sounds.json` manifest
  (`[{ "name": "cheers", "file": "cheers.wav" }]`).
- On first run, seeds from the bundled **starter pack** if `sounds.json` is absent.
- Add / remove / list operations used by the GUI.

### 3. Player (`player.py`)
- Plays a file into the `meetcheers` sink using the system player, e.g.
  `pw-play --target=meetcheers <file>` (fallback `paplay --device=meetcheers <file>`).
- Runs in a background thread / subprocess so clicks don't freeze the UI.
- Overlapping clicks: v1 plays them concurrently (each spawns its own subprocess) — simplest,
  matches soundboard expectations.

## Starter pack (ships with the app)

A `sounds/` folder committed with a few royalty-free clips: `cheers`, `applause`, `airhorn`.
Auto-loaded on first run so a fresh install (yours or a colleague's) has working buttons
immediately. Users add their own on top.

## Data flow (play)

```
Click "Cheers"
  → player.py: pw-play --target=meetcheers cheers.wav
    → PipeWire "meetcheers" sink
      → meetcheers.monitor → MeetCheers-Mic (virtual mic)
        → meeting app transmits to all participants → 🎉
```

## Sharing / distribution

- **How a colleague installs (Linux):**
  1. Unzip the folder (or `git clone`).
  2. `./setup.sh` — creates the virtual sink + mic.
  3. `./run.sh` — launches the app (checks Python 3, runs `meetcheers.py`).
  4. In the meeting, set mic = **MeetCheers-Mic**.
- **Handoff:** zip the project folder and send it, or push to a Git repo for updates.
- **Starter sounds travel with the folder** (they live in `sounds/`), so the board is usable on
  first launch. User-added sounds also live in `sounds/`, so backing up = copying the folder.
- **`run.sh`** verifies `python3` and required player (`pw-play`/`paplay`) exist; prints a clear
  message if `setup.sh` hasn't been run yet.

## Requirements (target machine)

- Linux + PipeWire (or PulseAudio). `pactl` + `pw-play`/`paplay` present (standard on Ubuntu/
  Fedora desktops).
- Python 3.8+ with Tkinter (`python3-tk` on Debian/Ubuntu — `run.sh` detects & instructs if missing).

## Error handling

- **Virtual sink missing** → status line warns + says "run ./setup.sh"; buttons still play to
  default output so nothing hard-crashes.
- **Player binary missing** → `run.sh` / startup check prints the exact `apt`/`dnf` install line.
- **Bad/corrupt sound file on add** → reject with a message, don't add the button.
- **Playback subprocess error** → non-fatal; log to status line, keep the app running.

## Testing (manual, v1)

1. `./setup.sh` → confirm `pactl list short sinks` shows `meetcheers` and
   `pactl list short sources` shows `meetcheers_mic`.
2. `./run.sh` → window opens with starter buttons.
3. Click "Cheers" → confirm `pactl list sink-inputs` shows a stream on `meetcheers`.
4. Join a test meeting, mic = **MeetCheers-Mic**; a second participant confirms they hear it.
5. Add a custom `.wav`, confirm it persists after restart (file in `sounds/`, entry in
   `sounds.json`).

## Out of scope for v1 (YAGNI)

- Keyboard / global hotkeys.
- Volume sliders, fade, trimming, waveform editing.
- Windows / macOS support (routing differs — VB-CABLE / BlackHole; noted for later).
- Hearing your own clips locally (optional loopback documented, not built).
- Packaging as a single binary (PyInstaller) — folder + `run.sh` is enough for v1.
