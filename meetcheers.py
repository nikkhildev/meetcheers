#!/usr/bin/env python3
"""MeetCheers — a tiny Linux soundboard that plays clips into a virtual mic so
everyone in your meeting hears them.

Run:  ./run.sh   (or  python3 meetcheers.py)
Setup (once): ./setup.sh
"""
from __future__ import annotations

import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import library
import player
import routing

COLS = 3  # buttons per row
APP_DIR = Path(__file__).resolve().parent


def ensure_routing() -> None:
    """Run setup.sh if the virtual mic is missing (e.g. after a reboot)."""
    if routing.source_exists():
        return
    setup = APP_DIR / "setup.sh"
    if setup.exists():
        subprocess.run(["bash", str(setup)], cwd=str(APP_DIR),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lib = library.Library()
        self._procs: list = []  # keep Popen handles alive

        root.title("MeetCheers 🎉")
        root.minsize(360, 240)

        # --- status bar ------------------------------------------------
        self.status_var = tk.StringVar()
        status = ttk.Label(root, textvariable=self.status_var, anchor="w", padding=(8, 4))
        status.pack(side="bottom", fill="x")

        # --- toolbar ---------------------------------------------------
        toolbar = ttk.Frame(root, padding=(8, 6))
        toolbar.pack(side="top", fill="x")
        ttk.Button(toolbar, text="＋ Add sound", command=self.add_sound).pack(side="left")
        ttk.Button(toolbar, text="↻ Recheck routing", command=self.refresh_status).pack(side="left", padx=(6, 0))

        # --- scrollable button grid -----------------------------------
        self.grid_frame = ttk.Frame(root, padding=8)
        self.grid_frame.pack(side="top", fill="both", expand=True)

        self.refresh_status()
        self.render_buttons()

        if player.player_available() is None:
            messagebox.showwarning(
                "No audio player found",
                "Could not find pw-play, paplay, or ffplay.\n"
                "Install PipeWire tools:  sudo apt install pipewire-audio-client-libraries\n"
                "or PulseAudio utils:      sudo apt install pulseaudio-utils",
            )

    # ---- rendering ---------------------------------------------------
    def render_buttons(self) -> None:
        for child in self.grid_frame.winfo_children():
            child.destroy()

        if not self.lib.sounds:
            ttk.Label(
                self.grid_frame,
                text="No sounds yet.\nClick “＋ Add sound” to add a clip.",
                anchor="center",
                justify="center",
            ).pack(expand=True)
            return

        for i, snd in enumerate(self.lib.sounds):
            r, c = divmod(i, COLS)
            cell = ttk.Frame(self.grid_frame)
            cell.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            self.grid_frame.columnconfigure(c, weight=1)

            btn = tk.Button(
                cell,
                text=snd.name,
                width=12,
                height=2,
                command=lambda s=snd: self.play(s),
            )
            btn.pack(fill="both", expand=True)
            # Right-click to delete.
            btn.bind("<Button-3>", lambda e, s=snd: self.delete_sound(s))

    # ---- actions -----------------------------------------------------
    def play(self, snd: library.Sound) -> None:
        proc = player.play(snd.path, sink_exists=routing.sink_exists())
        if proc is None:
            self.status_var.set(f"⚠ Could not play {snd.name} (missing file or player)")
            return
        self._procs = [p for p in self._procs if p.poll() is None]
        self._procs.append(proc)
        self.status_var.set(f"▶ Playing: {snd.name}")

    def add_sound(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose a sound clip",
            filetypes=[
                ("Audio", "*.wav *.mp3 *.ogg *.flac *.oga"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            snd = self.lib.add(path)
        except ValueError as e:
            messagebox.showerror("Could not add sound", str(e))
            return
        self.render_buttons()
        self.status_var.set(f"Added: {snd.name}")

    def delete_sound(self, snd: library.Sound) -> None:
        if not messagebox.askyesno("Delete sound", f"Remove “{snd.name}”?"):
            return
        self.lib.remove(snd.id)
        self.render_buttons()
        self.status_var.set(f"Removed: {snd.name}")

    def refresh_status(self) -> None:
        _, msg = routing.status()
        self.status_var.set(msg)


def main() -> None:
    ensure_routing()  # auto-create the virtual mic if a reboot wiped it
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
