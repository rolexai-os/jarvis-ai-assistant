"""JARVIS dark desktop dashboard."""
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
from jarvis.core import APPS, handle_command
from jarvis.reminders import ReminderStore
from jarvis.system_info import get_system_status
from jarvis.voice import listen_once, speak

BG, PANEL, CYAN, TEXT, MUTED = "#07111f", "#0c1b2b", "#37d8f2", "#e8f5ff", "#8aa6bc"


class JarvisApp:
    def __init__(self, root):
        self.root = root
        root.title("J.A.R.V.I.S. — Desktop Assistant")
        root.geometry("1000x680")
        root.minsize(780, 540)
        root.configure(bg=BG)
        self.reminders = ReminderStore()
        self.search_root = None
        self.voice_enabled = os.getenv("JARVIS_VOICE_ENABLED", "true").lower() == "true"
        self.speech_rate = int(os.getenv("JARVIS_SPEECH_RATE", "175"))
        self._build()
        self.log_line("JARVIS", "Systems online. How can I help?")
        self.refresh_metrics()
        root.after(1000, self.check_reminders)

    def _build(self):
        header = tk.Frame(self.root, bg=BG, padx=22, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="J.A.R.V.I.S.", bg=BG, fg=CYAN, font=("Segoe UI", 23, "bold")).pack(side="left")
        tk.Label(header, text="PERSONAL ASSISTANT / LOCAL CONTROL", bg=BG, fg=MUTED,
                 font=("Consolas", 9)).pack(side="left", padx=18, pady=(8, 0))
        self.clock = tk.Label(header, text="", bg=BG, fg=TEXT, font=("Consolas", 11))
        self.clock.pack(side="right")
        body = tk.Frame(self.root, bg=BG, padx=18, pady=4)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=PANEL, padx=14, pady=14)
        left.pack(side="left", fill="y", padx=(0, 12))
        tk.Label(left, text="SYSTEM STATUS", bg=PANEL, fg=CYAN, font=("Consolas", 10, "bold")).pack(anchor="w")
        self.metrics = tk.Label(left, text="Loading…", justify="left", anchor="nw", bg=PANEL, fg=TEXT,
                                font=("Consolas", 10), width=25)
        self.metrics.pack(fill="x", pady=(12, 20))
        tk.Label(left, text="QUICK ACTIONS", bg=PANEL, fg=CYAN, font=("Consolas", 10, "bold")).pack(anchor="w")
        actions = [
            ("System status", lambda: self.submit("system status")),
            ("Search files…", self.choose_search_folder),
            ("Capture screenshot…", self.capture_screenshot),
            ("Voice input", self.start_voice),
            ("Help", lambda: self.submit("help")),
        ]
        for label, callback in actions:
            tk.Button(left, text=label, command=callback, bg="#123047", fg=TEXT, activebackground="#1d526c",
                      activeforeground="white", relief="flat", padx=8, pady=7).pack(fill="x", pady=4)
        right = tk.Frame(body, bg=PANEL, padx=14, pady=14)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="MISSION LOG", bg=PANEL, fg=CYAN, font=("Consolas", 10, "bold")).pack(anchor="w")
        self.log = tk.Text(right, bg="#06101b", fg=TEXT, insertbackground=CYAN, relief="flat",
                           wrap="word", font=("Consolas", 10), padx=12, pady=12, state="disabled")
        self.log.pack(fill="both", expand=True, pady=(10, 12))
        row = tk.Frame(right, bg=PANEL)
        row.pack(fill="x")
        self.entry = tk.Entry(row, bg="#06101b", fg=TEXT, insertbackground=CYAN, relief="flat", font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self.entry.bind("<Return>", lambda _event: self.submit_entry())
        tk.Button(row, text="EXECUTE", command=self.submit_entry, bg=CYAN, fg="#00131c",
                  activebackground="#9af1ff", relief="flat", padx=16, pady=8).pack(side="right")
        tk.Label(self.root, text="Safety mode: allowlisted actions only • microphone starts only on request",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=22, pady=(5, 10))

    def log_line(self, who, message):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {who}: {message}\n\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def submit_entry(self):
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
        self.submit(command)

    def submit(self, command):
        self.log_line("YOU", command)
        services = {
            "reminders": self.reminders,
            "system_status": get_system_status,
            "launch_app": self.launch_app,
            "search_files": self.search_files,
            "clear": self.clear_log,
            "exit": self.root.destroy,
            "ai_chat": ai_chat if os.getenv("OPENAI_API_KEY", "").strip() else None,
        }
        answer = handle_command(command, services)
        self.log_line("JARVIS", answer)
        if self.voice_enabled and answer:
            threading.Thread(target=self.speak_safely, args=(answer,), daemon=True).start()
        self.refresh_metrics()

    def speak_safely(self, text):
        try:
            speak(text[:900], self.speech_rate)
        except Exception:
            pass

    def launch_app(self, name):
        if platform.system() != "Windows":
            return "These app shortcuts are configured for Windows."
        try:
            subprocess.Popen(APPS[name], shell=False)
            return f"Opening {name.title()}."
        except (OSError, KeyError) as exc:
            return f"Could not open {name.title()}: {exc}"

    def start_voice(self):
        if not self.voice_enabled:
            messagebox.showinfo("Voice disabled", "Enable JARVIS_VOICE_ENABLED in your local .env file.")
            return
        self.log_line("JARVIS", "Listening once. Speak now.")
        def worker():
            try:
                heard = listen_once()
                self.root.after(0, lambda: self.submit(heard))
            except Exception as exc:
                self.root.after(0, lambda: self.log_line("VOICE", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def choose_search_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to search (read-only)")
        if folder:
            self.search_root = Path(folder)
            self.log_line("JARVIS", f"File search scope set to: {self.search_root}")
            self.entry.delete(0, "end")
            self.entry.insert(0, "search files ")
            self.entry.focus_set()

    def search_files(self, query):
        if not self.search_root:
            return "Click Search files and choose a directory first."
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
            messagebox.showerror("Screenshot unavailable", f"Install Pillow and check desktop permissions.\n{exc}")

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

    def check_reminders(self):
        try:
            for item in self.reminders.due_items():
                messagebox.showinfo("JARVIS reminder", item.get("task", "Reminder"))
                self.log_line("REMINDER", item.get("task", "Reminder"))
        finally:
            self.root.after(15000, self.check_reminders)


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
