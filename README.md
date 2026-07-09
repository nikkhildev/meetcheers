# MeetCheers 🎉

A tiny Linux soundboard. Click a button → a sound (cheers, applause, airhorn…)
plays into a **virtual microphone** so **everyone in your meeting hears it**.
Works with any meeting app — Google Meet, Zoom, Teams, Discord — because it lives
at the OS audio layer, not in the browser.

## Requirements

- Linux with **PipeWire** or **PulseAudio** (default on Ubuntu/Fedora desktops)
- **Python 3.8+** with **Tkinter** (`python3-tk`)
- An audio player: `pw-play` (PipeWire) or `paplay` (PulseAudio)

## Install (3 steps)

```bash
# 1. one-time: create the virtual sink + mic and generate starter sounds
./setup.sh

# 2. launch the app
./run.sh

# 3. in your meeting app, set the microphone to:  MeetCheers-Mic
```

That's it. Click a button and your whole meeting hears it.

> **After a reboot/logout** the virtual devices are gone — just run `./setup.sh` again.

## Using it

- **Play:** click a sound button.
- **Add your own:** click **＋ Add sound**, pick a `.wav/.mp3/.ogg` — it's copied into
  `sounds/` and remembered.
- **Delete:** right-click a button.
- **Routing status** is shown at the bottom. If it says "run ./setup.sh", do that.

## Hearing the clips yourself (optional)

By default the sound goes only to the meeting (the virtual mic). To also hear it on
your own speakers, add a loopback while the app is running:

```bash
pactl load-module module-loopback source=meetcheers.monitor
```

## Sharing with a colleague (Linux)

1. Zip this whole folder (`zip -r meetcheers.zip meetcheers/`) and send it — **or** push to a Git repo.
2. They unzip / clone, then run `./setup.sh` and `./run.sh`.
3. Starter sounds are included, so their board works immediately.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Meeting can't hear the sound | Set the meeting mic to **MeetCheers-Mic**; run `./setup.sh` if it's missing. |
| "python3-tk missing" | `sudo apt install python3-tk` (Debian/Ubuntu) / `sudo dnf install python3-tkinter` (Fedora). |
| No sound at all | Install a player: `sudo apt install pulseaudio-utils` (gives `paplay`). |
| Devices vanished | You rebooted — re-run `./setup.sh`. |

## How it works

```
Click "Cheers"
  → pw-play --target=meetcheers cheers.wav
    → "meetcheers" virtual sink
      → meetcheers.monitor → MeetCheers-Mic (virtual mic)
        → meeting app sends it to everyone 🎉
```

## Files

| File | Purpose |
| --- | --- |
| `meetcheers.py` | Tkinter GUI (buttons, add/delete, status). |
| `library.py` | Manages `sounds/` + `sounds.json`. |
| `player.py` | Plays a clip into the virtual sink. |
| `routing.py` | Detects whether the virtual sink/mic exist. |
| `setup.sh` | Creates the virtual devices + starter sounds (one-time). |
| `run.sh` | Prereq checks + launches the app. |
| `scripts/make_starter_sounds.py` | Generates the starter WAVs (self-contained). |
