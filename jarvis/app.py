"""Animated JARVIS dashboard with explicit voice and PC-control toggles."""
from __future__ import annotations

import os
import platform
import subprocess
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from jarvis.ai import chat as ai_chat
from jarvis.apps import list_installed_apps, open_installed_app
from jarvis.core import APPS, handle_command
from jarvis.reminders import ReminderStore
from jarvis.system_info import get_system_status
from jarvis.voice import VoiceController, listen_once, speak

BG, PANEL, CYAN, TEXT, MUTED = "#050d18", "#0b1c2b", "#35d9f2", "#e8f5ff", "#86a8bf"
BUTTON, BUTTON_HI = "#123047", "#1a536a"


class JarvisApp:
    def __init__(self, root):
        self.root = root
        root.title("J.A.R.V.I.S. — Desktop Assistant")
        root.geometry("1120x760")
        root.minsize(850, 620)
        root.configure(bg=BG)
        self.reminders = ReminderStore()
        self.search_root = None
        self.voice_enabled = os.getenv("JARVIS_VOICE_ENABLED", "true").lower() == "true"
        self.speech_rate = int(os.getenv("JARVIS_SPEECH_RATE", "175"))
        self.voice = VoiceController(
            wake_word=os.getenv("JARVIS_WAKE_WORD", "jarvis"),
            clap_threshold=float(os.getenv("JARVIS_CLAP_THRESHOLD", "0.18")),
            clap_cooldown=float(os.getenv("JARVIS_CLAP_COOLDOWN", "1.2")),
        )
        self._phase = 0
        self._build()
        self.log_line("JARVIS", "Core online. Voice listeners are OFF until you enable them.")
        self.refresh_metrics()
        self.animate_reactor()
        root.after(1000, self.check_reminders)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self):
        header = tk.Frame(self.root, bg=BG, padx=22, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="J.A.R.V.I.S.", bg=BG, fg=CYAN, font=("Segoe UI", 24, "bold")).pack(side="left")
        tk.Label(header, text="PERSONAL ASSISTANT  /  SYSTEM INTERFACE", bg=BG, fg=MUTED,
                 font=("Consolas", 9)).pack(side="left", padx=18, pady=(8, 0))
        self.clock = tk.Label(header, text="", bg=BG, fg=TEXT, font=("Consolas", 11))
        self.clock.pack(side="right")

        body = tk.Frame(self.root, bg=BG, padx=16, pady=4)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=PANEL, padx=12, pady=12, width=250)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        tk.Label(left, text="ARC REACTOR", bg=PANEL, fg=CYAN, font=("Consolas", 10, "bold")).pack()
        self.reactor = tk.Canvas(left, width=210, height=190, bg=PANEL, highlightthickness=0)
        self.reactor.pack(pady=(4, 12))
        tk.Label(left, text="LIVE SYSTEM TELEMETRY", bg=PANEL, fg=CYAN,
                 font=("Consolas", 9, "bold")).pack(anchor="w")
        self.metrics = tk.Label(left, text="Loading…", justify="left", anchor="nw", bg=PANEL, fg=TEXT,
                                font=("Consolas", 9), wraplength=220)
        self.metrics.pack(fill="x", pady=(8, 12))

        tk.Label(left, text="VOICE & CONTROLS", bg=PANEL, fg=CYAN,
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.wake_button = self._button(left, "Enable wake word", self.toggle_wake)
        self.clap_button = self._button(left, "Enable clap detection", self.toggle_clap)
        self._button(left, "Voice input (once)", self.start_voice)
        self._button(left, "Installed apps list", self.show_apps)
        self._button(left, "Search files…", self.choose_search_folder)
        self._button(left, "Screenshot…", self.capture_screenshot)
        self._button(left, "Lock PC", self.confirm_lock)

        right = tk.Frame(body, bg=PANEL, padx=14, pady=14)
        right.pack(side="left", fill="both", expand=True)
        top = tk.Frame(right, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text="MISSION LOG", bg=PANEL, fg=CYAN,
                 font=("Consolas", 10, "bold")).pack(side="left")
        tk.Label(top, text="ANIMATED UI  •  VOICE COMMANDS", bg=PANEL, fg=MUTED,
                 font=("Consolas", 8)).pack(side="right")
        self.log = tk.Text(right, bg="#040a12", fg=TEXT, insertbackground=CYAN, relief="flat",
                           wrap="word", font=("Consolas", 10), padx=12, pady=12, state="disabled")
        self.log.pack(fill="both", expand=True, pady=(10, 12))
        row = tk.Frame(right, bg=PANEL)
        row.pack(fill="x")
        self.entry = tk.Entry(row, bg="#040a12", fg=TEXT, insertbackground=CYAN, relief="flat",
                              font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 8))
        self.entry.bind("<Return>", lambda _event: self.submit_entry())
        tk.Button(row, text="EXECUTE", command=self.submit_entry, bg=CYAN, fg="#00131c",
                  activebackground="#a4f5ff", relief="flat", padx=18, pady=8).pack(side="right")
        tk.Label(self.root,
                 text="PRIVACY: microphone monitoring is opt-in • wake recognition may use online speech service",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=22, pady=(5, 10))

    def _button(self, parent, text, callback):
        button = tk.Button(parent, text=text, command=callback, bg=BUTTON, fg=TEXT,
                           activebackground=BUTTON_HI, activeforeground="white", relief="flat",
                           padx=7, pady=6, anchor="w")
        button.pack(fill="x", pady=2)
        return button

    def log_line(self, who, message):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {who}: {message}\n\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def submit_entry(self):
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
        self.submit(command)

    def _services(self):
        return {
            "reminders": self.reminders,
            "system_status": get_system_status,
            "launch_app": self.launch_app,
            "open_app": open_installed_app,
            "search_files": self.search_files,
            "clear": self.clear_log,
            "exit": self.close,
            "lock_pc": self.lock_pc,
            "ai_chat": ai_chat if (os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("JARVIS_AI_PROVIDER", "").lower() == "ollama") else None,
        }

    def submit(self, command):
        if command == "__WAKE__":
            self.log_line("JARVIS", "I'm awake. Say a command now.")
            threading.Thread(target=self.speak_safely, args=("I'm listening.",), daemon=True).start()
            return
        if not command:
            return
        self.log_line("YOU", command)
        answer = handle_command(command, self._services())
        self.log_line("JARVIS", answer)
        if self.voice_enabled and answer:
            threading.Thread(target=self.speak_safely, args=(answer,), daemon=True).start()
        self.refresh_metrics()

    def speak_safely(self, text):
        try:
            speak(text[:700], self.speech_rate)
        except Exception:
            pass

    def launch_app(self, name):
        if platform.system() != "Windows":
            return "These built-in app shortcuts are configured for Windows."
        try:
            subprocess.Popen(APPS[name], shell=False)
            return f"Opening {name.title()}."
        except (OSError, KeyError) as exc:
            return f"Could not open {name.title()}: {exc}"

    def start_voice(self):
        if not self.voice_enabled:
            messagebox.showinfo("Voice disabled", "Enable JARVIS_VOICE_ENABLED in .env.")
            return
        self.log_line("JARVIS", "Listening once…")
        def worker():
            try:
                heard = listen_once()
                self.root.after(0, lambda: self.submit(heard))
            except Exception as exc:
                self.root.after(0, lambda: self.log_line("VOICE", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def toggle_wake(self):
        if self.voice.wake_active:
            self.voice.stop_wake_word(lambda msg: self.root.after(0, lambda: self.log_line("VOICE", msg)))
            self.wake_button.configure(text="Enable wake word")
        else:
            if self.voice.clap_active:
                self.voice.stop_clap_detection()
                self.clap_button.configure(text="Enable clap detection")
            self.wake_button.configure(text="Disable wake word")
            self.voice.start_wake_word(
                lambda cmd: self.root.after(0, lambda: self.submit(cmd)),
                lambda msg: self.root.after(0, lambda: self.log_line("VOICE", msg)),
            )

    def toggle_clap(self):
        if self.voice.clap_active:
            self.voice.stop_clap_detection(lambda msg: self.root.after(0, lambda: self.log_line("VOICE", msg)))
            self.clap_button.configure(text="Enable clap detection")
        else:
            if self.voice.wake_active:
                self.voice.stop_wake_word()
                self.wake_button.configure(text="Enable wake word")
            self.clap_button.configure(text="Disable clap detection")
            self.voice.start_clap_detection(
                lambda: self.root.after(0, self.clap_detected),
                lambda msg: self.root.after(0, lambda: self.log_line("VOICE", msg)),
            )

    def clap_detected(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(800, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        self.log_line("SENSOR", "Clap detected — JARVIS is here.")
        if self.voice_enabled:
            threading.Thread(target=self.speak_safely, args=("At your service.",), daemon=True).start()

    def show_apps(self):
        names = list_installed_apps(limit=80)
        if not names:
            messagebox.showinfo("Installed apps", "No Start Menu shortcuts found. This feature currently supports Windows.")
            return
        window = tk.Toplevel(self.root)
        window.title("Detected Windows applications")
        window.geometry("520x560")
        window.configure(bg=BG)
        tk.Label(window, text="Say or type: open <app name>", bg=BG, fg=CYAN,
                 font=("Consolas", 11, "bold")).pack(anchor="w", padx=12, pady=10)
        listing = tk.Listbox(window, bg="#040a12", fg=TEXT, selectbackground=BUTTON_HI,
                             font=("Segoe UI", 10), relief="flat")
        listing.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        for name in names:
            listing.insert("end", name)
        listing.bind("<Double-Button-1>", lambda _event: self.submit("open " + listing.get(listing.curselection()[0])) if listing.curselection() else None)

    def choose_search_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to search (read-only)")
        if folder:
            self.search_root = Path(folder)
            self.log_line("JARVIS", f"Search scope set to: {self.search_root}")
            self.entry.delete(0, "end")
            self.entry.insert(0, "search files ")
            self.entry.focus_set()

    def search_files(self, query):
        if not self.search_root:
            return "Choose a directory first with Search files."
        if not query:
            return "Enter a filename fragment after search files."
        found = []
        try:
            for path in self.search_root.rglob("*"):
                try:
                    if path.is_file() and query.casefold() in path.name.casefold():
                        found.append(str(path))
                        if len(found) >= 30:
                            break
                except OSError:
                    continue
        except OSError as exc:
            return f"Search stopped: {exc}"
        return "Matches:\n" + "\n".join(found) if found else "No matching files found."

    def capture_screenshot(self):
        if not messagebox.askyesno("Capture screenshot", "Save a screenshot to Pictures/JARVIS?"):
            return
        try:
            from PIL import ImageGrab
            target = Path.home() / "Pictures" / "JARVIS"
            target.mkdir(parents=True, exist_ok=True)
            filename = target / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            ImageGrab.grab().save(filename)
            self.log_line("JARVIS", f"Screenshot saved: {filename}")
        except Exception as exc:
            messagebox.showerror("Screenshot unavailable", str(exc))

    def confirm_lock(self):
        if messagebox.askyesno("Lock this PC", "Lock your Windows session now?"):
            self.log_line("JARVIS", self.lock_pc())

    def lock_pc(self):
        if platform.system() != "Windows":
            return "Lock PC is available on Windows only."
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "Locking Windows session."
        except Exception as exc:
            return f"Could not lock PC: {exc}"

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def refresh_metrics(self):
        self.clock.configure(text=datetime.now().astimezone().strftime("%a %d %b  %H:%M:%S"))
        try:
            self.metrics.configure(text=get_system_status())
        except Exception as exc:
            self.metrics.configure(text=f"Status unavailable\n{exc}")
        self.root.after(5000, self.refresh_metrics)

    def animate_reactor(self):
        canvas = self.reactor
        canvas.delete("all")
        cx, cy = 105, 92
        self._phase = (self._phase + 1) % 120
        pulse = 4 * (1 + __import__("math").sin(self._phase * 0.13))
        for radius in (72, 59, 45, 31):
            canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                               outline="#14536c" if radius > 45 else CYAN, width=1)
        canvas.create_oval(cx-22-pulse/2, cy-22-pulse/2, cx+22+pulse/2, cy+22+pulse/2,
                           fill="#0e5570", outline="#a3f6ff", width=2)
        canvas.create_oval(cx-12, cy-12, cx+12, cy+12, fill="#b9faff", outline="white")
        for index in range(12):
            import math
            angle = (self._phase * 0.035) + index * math.tau / 12
            x1, y1 = cx + 48*math.cos(angle), cy + 48*math.sin(angle)
            x2, y2 = cx + 66*math.cos(angle), cy + 66*math.sin(angle)
            canvas.create_line(x1, y1, x2, y2, fill=CYAN, width=2)
        canvas.create_text(cx, 174, text="CORE ONLINE", fill=CYAN, font=("Consolas", 9, "bold"))
        self.root.after(70, self.animate_reactor)

    def check_reminders(self):
        try:
            for item in self.reminders.due_items():
                messagebox.showinfo("JARVIS reminder", item.get("task", "Reminder"))
                self.log_line("REMINDER", item.get("task", "Reminder"))
        finally:
            if self.root.winfo_exists():
                self.root.after(15000, self.check_reminders)

    def close(self):
        self.voice.stop_wake_word()
        self.voice.stop_clap_detection()
        self.root.destroy()


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    root = tk.Tk()
    JarvisApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
