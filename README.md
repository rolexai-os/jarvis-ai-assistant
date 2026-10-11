# JARVIS AI Assistant

Free, open-source Windows-first desktop assistant inspired by sci-fi interfaces.

## Current features
- Dark dashboard with system metrics and conversation history.
- Typed commands, optional one-shot speech recognition and spoken replies.
- Safe allowlisted website and Windows application launching.
- System status, arithmetic calculator, local reminders.
- Read-only file search after you explicitly choose a directory.
- Screenshot capture only after a confirmation dialog.
- Optional OpenAI chat adapter, disabled without a local API key.
- Small opt-in plugin interface and unit tests.

Status: early-stage MVP. Features that depend on optional libraries, microphone hardware, network access, or API credentials may require additional setup. This is not an unrestricted autonomous agent.

## Install on Windows 11
1. Install Python 3.11 or 3.12 from python.org. Ensure Tkinter is included.
2. Open PowerShell:
   git clone https://github.com/rolexai-os/jarvis-ai-assistant.git
   cd jarvis-ai-assistant
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   Copy-Item .env.example .env
   python -m jarvis
3. Edit .env only if you want optional AI chat. Local commands work without an API key.

If PowerShell blocks activation, run Set-ExecutionPolicy -Scope Process RemoteSigned in that terminal and activate again.

## Commands
- help, time, system status
- open Google / YouTube / GitHub / Wikipedia / Gmail
- open Notepad / Calculator / Explorer
- search web words
- calculate 12 * (4 + 2)
- remind me to stretch in 10 minutes
- reminders
- search files words (choose a folder using the dashboard first)
- clear, exit

## Tests
Run: python -m unittest discover -s tests -v

## Privacy and safety
JARVIS does not execute arbitrary shell commands or silently capture the screen. File search is read-only and scoped to a folder selected by the user. Screenshot capture requires explicit confirmation. Online speech recognition and cloud AI may transmit data to their providers. Never commit .env or share API keys. Review plugins before using them.

## Roadmap
- [x] Dashboard, typed commands, allowlisted app/site launching
- [x] System metrics, reminders, safe calculator
- [x] Optional voice and AI adapters
- [x] Folder-scoped search and confirmed screenshot capture
- [x] Plugin loading interface
- [ ] Wake-word engine, local model adapter, installer, animated reactor UI

Contributions are welcome. See CONTRIBUTING.md. Licensed under MIT; see LICENSE.
