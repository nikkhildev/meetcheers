# MeetCheers 🎉

A tiny Linux soundboard. Click a button → a sound (cheers, applause, airhorn…)
plays into a **virtual microphone** so **everyone in your meeting hears it**.
Works with any meeting app — Google Meet, Zoom, Teams, Discord — because it lives
at the OS audio layer, not in the browser.

## Requirements

- Linux with **PipeWire** or **PulseAudio** (default on Ubuntu/Fedora desktops)
- **Python 3.8+** with **Tkinter** (`python3-tk`)
- An audio player: `pw-play` (PipeWire) or `paplay` (PulseAudio)

## Install (once — then just click the icon)

```bash
sudo apt install python3-tk    # one-time dependency
./install.sh                   # adds a clickable "MeetCheers" app icon
```

Then **search "MeetCheers" in your apps menu and click it.** The app auto-creates
the virtual mic on launch (even after a reboot), so you never touch the terminal
again. In your meeting app, set the microphone to **MeetCheers-Mic**.

_(No icon? You can still run `./run.sh` — it does the same auto-setup.)_

That's it. Click a button and your whole meeting hears it — and **MeetCheers-Mic
carries your voice too**, so you don't need to switch mics to talk.

> **After a reboot/logout** the virtual devices are gone — just run `./setup.sh` again.

> **Muffled sounds?** Turn OFF your meeting app's *noise cancellation* — it treats
> clips/music as background noise and suppresses them.

## Using it

- **Play:** click a sound button.
- **Add your own:** click **＋ Add sound**, pick a `.wav/.mp3/.ogg` — it's copied into
  `sounds/` and remembered.
- **Delete:** right-click a button.
- **Routing status** is shown at the bottom. If it says "run ./setup.sh", do that.

## Your voice + the sounds (how the mic works)

`setup.sh` builds **one** virtual mic — `MeetCheers-Mic` — that mixes:

- your **real microphone** (people hear you talk normally), and
- the **soundboard** (people hear the clips you click).

So you select `MeetCheers-Mic` once and never switch back and forth.

## Hearing the clips yourself (optional)

The mic goes to the meeting, not your speakers. To also hear clips locally, add a
loopback while the app is running:

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
