"""Explicit, visible PowerShell / Command Prompt mode for JARVIS."""
from __future__ import annotations

import re
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# These operations are intentionally blocked in the embedded terminal to reduce
# the chance of accidental disk, boot, registry, or bulk-delete damage.
_BLOCKED_PATTERNS = [
    r"\bformat(?:\.com)?\b",
    r"\bdiskpart\b",
    r"\b(clear-disk|initialize-disk|remove-partition|clean all)\b",
    r"\b(bcdedit|bootrec|diskshadow)\b",
    r"\b(shutdown|restart-computer|stop-computer)\b",
    r"\breg(?:\.exe)?\s+delete\b",
    r"\b(remove-item|ri|del|erase|rmdir|rd)\b.{0,100}(-recurse|-r\b|/s\b|/q\b)",
    r"\b(del|erase|rmdir|rd)\s+/[a-z]*[sq][a-z]*\b",
]

def is_blocked_command(command: str) -> bool:
    """Return True for high-risk destructive commands blocked by embedded mode."""
    return any(re.search(pattern, command, flags=re.IGNORECASE) for pattern in _BLOCKED_PATTERNS)


class TerminalWindow:
    """A visible, non-elevated shell window requiring per-command confirmation."""

    def __init__(self, parent: tk.Misc, log_callback=None):
        self.parent = parent
        self.log_callback = log_callback or (lambda _message: None)
        self.window = tk.Toplevel(parent)
        self.window.title("JARVIS — Terminal Mode")
        self.window.geometry("900x620")
        self.window.minsize(680, 440)
        self.window.configure(bg="#050d18")

        header = tk.Frame(self.window, bg="#050d18", padx=12, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="TERMINAL MODE", bg="#050d18", fg="#35d9f2",
                 font=("Consolas", 13, "bold")).pack(side="left")
        tk.Label(header, text="Runs as your current Windows user • never elevated",
                 bg="#050d18", fg="#86a8bf", font=("Segoe UI", 9)).pack(side="right")

        controls = tk.Frame(self.window, bg="#0b1c2b", padx=10, pady=8)
        controls.pack(fill="x", padx=10)
        tk.Label(controls, text="Shell:", bg="#0b1c2b", fg="#e8f5ff").pack(side="left")
        self.shell = tk.StringVar(value="PowerShell")
        self.shell_box = ttk.Combobox(controls, textvariable=self.shell,
                                      values=("PowerShell", "Command Prompt"),
                                      state="readonly", width=20)
        self.shell_box.pack(side="left", padx=8)
        tk.Button(controls, text="Clear output", command=self.clear_output,
                  bg="#123047", fg="#e8f5ff", relief="flat").pack(side="right")

        self.output = tk.Text(self.window, bg="#040a12", fg="#d8f5ff",
                              insertbackground="#35d9f2", relief="flat",
                              wrap="word", font=("Consolas", 10), padx=10, pady=10)
        self.output.pack(fill="both", expand=True, padx=10, pady=(8, 8))
        self.output.insert("end", "Commands run in this visible window, in the project folder.\\n"
                                  "Every command requires confirmation. High-risk destructive commands are blocked.\\n\\n")

        row = tk.Frame(self.window, bg="#050d18", padx=10, pady=8)
        row.pack(fill="x")
        self.command = tk.Entry(row, bg="#040a12", fg="#e8f5ff",
                                insertbackground="#35d9f2", relief="flat",
                                font=("Consolas", 10))
        self.command.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 8))
        self.command.bind("<Return>", lambda _event: self.run_command())
        self.run_button = tk.Button(row, text="RUN COMMAND", command=self.run_command,
                                     bg="#35d9f2", fg="#00131c", relief="flat", padx=12, pady=7)
        self.run_button.pack(side="right")
        self.command.focus_set()

    def write(self, text: str):
        try:
            self.output.insert("end", text)
            self.output.see("end")
        except tk.TclError:
            pass

    def clear_output(self):
        self.output.delete("1.0", "end")

    def run_command(self):
        command = self.command.get().strip()
        if not command:
            return
        if is_blocked_command(command):
            self.write(f"\\n[BLOCKED] This embedded terminal blocks high-risk destructive commands:\\n{command}\\n")
            messagebox.showwarning(
                "Command blocked",
                "This command matches a high-risk disk, boot, registry, shutdown, or bulk-delete pattern. "
                "Run sensitive maintenance manually outside JARVIS only after checking the command and backups.",
                parent=self.window,
            )
            return
        shell_name = self.shell.get()
        if not messagebox.askyesno(
            "Confirm shell command",
            f"Run this command in {shell_name}?\\n\\n{command}\\n\\n"
            "It runs as your current Windows user, not as Administrator. "
            "Commands can still change files or settings.",
            parent=self.window,
        ):
            self.write(f"\\n[cancelled] {command}\\n")
            return
        self.command.delete(0, "end")
        self.run_button.configure(state="disabled")
        self.write(f"\\n> {command}\\n")
        threading.Thread(target=self._execute, args=(shell_name, command), daemon=True).start()

    def _execute(self, shell_name: str, command: str):
        try:
            if shell_name == "PowerShell":
                args = ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]
            else:
                args = ["cmd.exe", "/d", "/s", "/c", command]
            completed = subprocess.run(
                args, cwd=str(PROJECT_ROOT), capture_output=True, text=True,
                errors="replace", timeout=60, shell=False,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
            if output:
                output += "" if output.endswith("\\n") else "\\n"
            output += f"[exit code: {completed.returncode}]\\n"
        except subprocess.TimeoutExpired:
            output = "[ERROR] Command timed out after 60 seconds.\\n"
        except FileNotFoundError as exc:
            output = f"[ERROR] Shell not found: {exc}\\n"
        except Exception as exc:
            output = f"[ERROR] {exc}\\n"
        try:
            self.window.after(0, lambda value=output: self._finish(value, command))
        except tk.TclError:
            pass

    def _finish(self, output: str, command: str):
        self.write(output + "\\n")
        self.run_button.configure(state="normal")
        self.command.focus_set()
        self.log_callback(f"{command} (terminal command completed; see Terminal Mode for output)")
