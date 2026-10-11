# JARVIS AI Assistant

Free, open-source Windows-first desktop assistant inspired by sci-fi interfaces.

## Features
- Animated cyan arc-reactor dashboard, system telemetry and conversation log.
- Typed commands, optional one-shot voice input and spoken responses.
- **Opt-in wake-word listening**: enable it in the GUI, then say "JARVIS open Chrome" or "JARVIS what time is it".
- **Opt-in clap detection**: enable it in the GUI; a loud clap brings JARVIS to the foreground and announces readiness. Claps do not execute PC commands.
- Discover and launch third-party Windows apps that have Start Menu or Desktop shortcuts. Use "Installed apps list" to inspect discovered shortcuts, then say/type "open <app name>".
- Built-in shortcuts for Notepad, Calculator, Explorer and approved websites.
- System status, safe arithmetic, local reminders, web search and read-only file search in a selected folder.
- Screenshot capture only after a confirmation dialog; Windows lock action.\n- Dedicated PowerShell / Command Prompt window with per-command confirmation, visible output and timeout.\n- Embedded terminal blocks common high-risk disk, boot, registry, shutdown and bulk-delete command patterns.\n- PowerShell updater checks GitHub, fast-forward updates a clean `main` checkout and refreshes dependencies while preserving `.env`.
- Optional OpenAI cloud chat or local Ollama chat.
- Unit tests, MIT license and GitHub Actions test workflow.

**Status:** early-stage MVP. Wake-word recognition currently uses the online Google speech-recognition endpoint; it is not offline wake-word detection. This is not an unrestricted autonomous agent.

## Install on Windows 11
Install Python 3.11 or 3.12, then run in PowerShell:

```powershell
git clone https://github.com/rolexai-os/jarvis-ai-assistant.git
cd jarvis-ai-assistant
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m jarvis
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process RemoteSigned` in that terminal, then activate again.

## Voice setup and privacy
1. Start JARVIS and click **Enable wake word** or **Enable clap detection**. Neither listener starts automatically.
2. For wake word, say "JARVIS" followed by a command. If you say only "JARVIS", speak a command within about eight seconds.
3. For clap detection, adjust `JARVIS_CLAP_THRESHOLD` in `.env` if the room is noisy or claps are missed.
4. Click the matching Disable button to stop monitoring. Closing JARVIS also stops listeners.

Wake-word mode continuously samples microphone audio while enabled and sends audio snippets for online speech recognition. Avoid it if you do not want audio sent to that service. Clap detection processes microphone levels locally. Check Windows microphone privacy settings. Only one listener is enabled at a time by the GUI.

## Commands
- `help`, `time`, `system status`
- `open Google`, `open YouTube`, `open GitHub`
- `open Notepad`, `open Calculator`, `open Explorer`
- `open Chrome` or `open <installed app name>` for apps with Start Menu/Desktop shortcuts
- `search web <words>`
- `calculate 12 * (4 + 2)`
- `remind me to stretch in 10 minutes`, `reminders`
- `search files <words>` (choose a folder with the dashboard button first)
- `lock PC`, `open terminal`, `update`, `clear`, `exit`

## Optional AI
Set `JARVIS_AI_PROVIDER=openai` and provide `OPENAI_API_KEY` for cloud AI. For a local Ollama server, set `JARVIS_AI_PROVIDER=ollama`, set `OLLAMA_MODEL` to an installed model, and start Ollama first. Cloud AI sends prompts to its provider. Keep `.env` private.

## Tests
`python -m unittest discover -s tests -v`

## Safety limitations
JARVIS does not run arbitrary terminal commands, change security settings, or silently capture screenshots. Installed-app launching only opens a matching shortcut discovered in common Start Menu/Desktop locations; apps without shortcuts may not appear. Do not install untrusted plugins. This project has not been verified on every Windows PC.

## Roadmap
- [x] Animated arc-reactor dashboard
- [x] Opt-in wake-word listener and clap detection
- [x] Start Menu/Desktop shortcut discovery and app launching
- [x] System metrics, reminders, safe calculator, manual screenshot capture
- [x] Optional cloud/local AI adapters
- [ ] Offline wake-word engine, more granular app lifecycle/window controls, installer and signed release

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under MIT; see [LICENSE](LICENSE).
