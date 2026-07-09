# MeetCheers — Design Spec

**Date:** 2026-07-09
**Owner:** Nikhil
**Status:** Approved design, pre-implementation

## Purpose

A Chrome extension (Manifest V3) that plays sound clips (cheers, applause, drumroll, etc.)
during a video meeting so that **everyone in the meeting hears them** — a soundboard.

The clips are triggered by clicking buttons in the extension popup and are played out
through a user-selected audio output device. On Linux, that device is a PipeWire/PulseAudio
**virtual sink** whose monitor is exposed as a **virtual microphone**, which the meeting app
uses as its mic input. That is how the sound reaches other participants.

## Constraints & key facts

- **Target OS:** Linux (PipeWire/PulseAudio).
- A Chrome extension **cannot** inject audio into a real microphone by itself. The meeting app
  only transmits its selected mic. So a one-time OS-level virtual-audio setup is required.
- **MV3 service workers have no DOM** → audio cannot play in the service worker or reliably in
  the popup (popup closes). Audio MUST play in an **offscreen document**
  (`reasons: ['AUDIO_PLAYBACK']`).
- **Output device selection** uses `HTMLAudioElement.setSinkId(deviceId)`. Reading device
  *labels* via `enumerateDevices()` requires a one-time `getUserMedia({audio:true})` grant.

## One-time OS setup (outside the extension)

```bash
# Virtual sink the extension plays into
pactl load-module module-null-sink \
  sink_name=meetcheers \
  sink_properties=device.description=MeetCheers

# Expose that sink's monitor as a virtual microphone for the meeting app
pactl load-module module-remap-source \
  master=meetcheers.monitor \
  source_name=meetcheers_mic \
  source_properties=device.description=MeetCheers-Mic
```

Then:
- In the meeting app, set **microphone = MeetCheers-Mic**.
- In the extension device picker, set **output = MeetCheers**.

> To also hear yourself, combine your real mic + the sink into a virtual source, or use a
> `module-loopback` — documented as an optional enhancement, not required for v1.

## Architecture

Three components communicating via `chrome.runtime` messaging.

### 1. Popup (`popup.html` / `popup.js`)
- Renders a grid of buttons, one per saved sound.
- "＋ Add sound" button → file input (`.mp3`, `.wav`, `.ogg`) → saves to storage.
- Output-device `<select>` dropdown, populated from `enumerateDevices()`.
- A "Grant device access" affordance that calls `getUserMedia` once to unlock device labels.
- Clicking a sound button → `chrome.runtime.sendMessage({ type: 'play', soundId, sinkId })`.
- Delete affordance per sound.

### 2. Service worker (`background.js`)
- Listens for `{ type: 'play', soundId, sinkId }`.
- Ensures the offscreen document exists (`chrome.offscreen.hasDocument()` →
  `createDocument({ url:'offscreen.html', reasons:['AUDIO_PLAYBACK'], justification:'Soundboard playback' })`).
- Loads the sound's `dataUrl` from `chrome.storage.local` and forwards
  `{ type:'offscreen-play', dataUrl, sinkId }` to the offscreen document.

### 3. Offscreen document (`offscreen.html` / `offscreen.js`)
- Holds one reusable `<audio>` element.
- On `offscreen-play`: `await audio.setSinkId(sinkId)` (skip if empty → default device),
  set `audio.src = dataUrl`, `audio.play()`.
- Reports errors back to the SW/popup.

## Data model

`chrome.storage.local`:
```jsonc
{
  "sounds": [
    { "id": "uuid", "name": "cheers", "dataUrl": "data:audio/wav;base64,..." }
  ],
  "sinkId": "selected-output-device-id"   // remembered across sessions
}
```
Files stored as data URLs (base64). Acceptable for short clips; a size cap (e.g. 5 MB/clip)
guards against `storage.local` quota (default ~10 MB, or `unlimitedStorage` permission if needed).

## Data flow (play)

```
popup click
  → runtime.sendMessage(play, soundId, sinkId)
    → service worker: ensure offscreen doc, load dataUrl
      → offscreen: setSinkId(sinkId) → audio.play()
        → PipeWire "meetcheers" sink
          → meetcheers.monitor → MeetCheers-Mic (virtual mic)
            → meeting app transmits to all participants
```

## Manifest (MV3) — permissions

```jsonc
{
  "manifest_version": 3,
  "name": "MeetCheers",
  "version": "0.1.0",
  "action": { "default_popup": "popup.html" },
  "background": { "service_worker": "background.js", "type": "module" },
  "permissions": ["offscreen", "storage"]
  // getUserMedia device-label grant is a runtime permission prompt, no manifest entry.
  // Add "unlimitedStorage" only if clips exceed the default quota.
}
```

## Error handling

- **No device selected / setSinkId fails** → fall back to default output, show a warning toast
  in the popup ("Playing on default output — pick MeetCheers to route into the meeting").
- **Device labels blank** → prompt user to click "Grant device access" (getUserMedia).
- **Offscreen create/play fails** → surface the error string in the popup.
- **File too large** → reject at upload with a clear message.

## Testing (manual, v1)

1. `chrome://extensions` → Load unpacked → select the folder.
2. Run the two `pactl` commands.
3. Upload a short `.wav`, open popup, grant device access, select **MeetCheers** output.
4. Click the sound; confirm `pactl list sink-inputs` shows a stream on the `meetcheers` sink.
5. Join a test meeting with mic = **MeetCheers-Mic**; a second participant confirms they hear it.

## Out of scope for v1 (YAGNI)

- Keyboard shortcuts / global hotkeys.
- Bundled starter sounds (upload-only).
- Cross-platform (Windows VB-CABLE, macOS BlackHole) — noted for later.
- Volume/fade controls, overlapping playback, waveform trimming.
- Hearing your own clips locally (optional loopback documented, not built).
