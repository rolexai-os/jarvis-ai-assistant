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
- Screenshot capture only after a confirmation dialog; Windows lock action.
- Dedicated PowerShell / Command Prompt window with per-command confirmation, visible output and timeout.
- Embedded terminal blocks common high-risk disk, boot, registry, shutdown and bulk-delete command patterns.
- PowerShell updater checks GitHub, fast-forward updates a clean `main` checkout and refreshes dependencies while preserving `.env`.
- Optional OpenAI cloud chat or local Ollama chat with bounded in-memory conversation context.
- Optional offline one-shot speech recognition via Vosk and a user-downloaded local model.
- Local personalization for assistant name, speech rate and spoken responses.
- Local JSONL security/audit log, viewed in the dashboard Security Center.
- Built-in skill registry with persistent enable/disable preferences; arbitrary third-party Python plugins are not executed.
- User-triggered web research that returns DuckDuckGo result snippets and source URLs.
- Expanded CPU, RAM, disk, process-count, battery and uptime telemetry where supported.
- Unit tests, MIT license and GitHub Actions test workflow.

**Status:** early-stage MVP. The wake-word listener still uses online Google speech recognition. Offline voice is an optional one-shot mode, not an offline wake-word engine. Web research sends the search query to DuckDuckGo. This is not an unrestricted autonomous agent.

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

## Optional offline voice (Vosk)

The normal `requirements.txt` does not install Vosk or a language model. For offline one-shot speech recognition:

1. Activate the project's virtual environment.
2. Run `pip install -r requirements-voice-offline.txt`.
3. Download a Vosk model for your language from the official Vosk model page and extract it to a folder you control.
4. Set `JARVIS_VOSK_MODEL_PATH` in your local `.env` to that extracted folder path, for example `C:\\Users\\YOUR_NAME\\vosk-model-small-en-us-0.15`.
5. Restart JARVIS and click **Voice input (offline)**.

This offline mode does not upload microphone audio for recognition. Wake-word mode remains online in this version. Make sure Windows microphone permissions allow desktop apps to access the microphone.

## Security log, personalization and plugins

- Security Center stores a minimal local audit trail at `%USERPROFILE%\\.jarvis-ai\\security.log.jsonl`; it omits full prompts and secret values.
- Preferences are stored at `%USERPROFILE%\\.jarvis-ai\\preferences.json`.
- Built-in plugin toggles are stored at `%USERPROFILE%\\.jarvis-ai\\plugins.json`. The plugin MVP is a reviewed allowlist; it deliberately does not execute arbitrary plugin scripts.
- AI chat context is held in memory for the current process only and is discarded when JARVIS exits.
- `research web <topic>` fetches a few DuckDuckGo HTML search results and displays their snippets and URLs. Search content is untrusted; open and verify original sources. `search web <topic>` continues to open a browser search page.

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

## Update an existing installation

Close JARVIS before a manual update. From the repository folder in PowerShell:

```powershell
.\scripts\update.ps1
```

Or double-click `scripts\update.bat`. The GUI also has **Update JARVIS…**, and the command `update` opens the updater. It checks that this is a Git clone on `main`, refuses to proceed if the working tree contains local changes, fetches `origin/main`, uses a fast-forward-only merge (never a hard reset), and refreshes dependencies in `.venv` when available. It does not replace `.env`. Restart JARVIS after updating. If local changes are reported, commit or back them up before trying again.

## Terminal Mode

Use **Terminal Mode…** in the dashboard or type `open terminal`. Select PowerShell or Command Prompt, enter a command, and confirm each run. Commands run visibly in the project folder as your current Windows user (not Administrator), with a 60-second timeout. Common destructive disk, boot, registry, shutdown, and bulk-delete patterns are blocked. This pattern check is only a guardrail, not a complete security boundary; review every command before approving it.

## Tests
`python -m unittest discover -s tests -v`

## Safety limitations
JARVIS does not execute shell commands from ordinary chat or voice intents. Terminal Mode is separate, visible, and requires per-command confirmation; it is not a complete security boundary. JARVIS does not silently capture screenshots. Installed-app launching only opens a matching shortcut discovered in common Start Menu/Desktop locations; apps without shortcuts may not appear. Do not install untrusted plugins. This project has not been verified on every Windows PC.

## Roadmap
- [x] Animated arc-reactor dashboard
- [x] Opt-in wake-word listener and clap detection
- [x] Start Menu/Desktop shortcut discovery and app launching
- [x] System metrics, reminders, safe calculator, manual screenshot capture
- [x] Optional cloud/local AI adapters
- [x] Visible PowerShell / Command Prompt mode with confirmation and output
- [x] GitHub fast-forward updater with local-change protection
- [ ] Offline wake-word engine, window/app lifecycle controls, configurable themes, full browser research summarization, installer and signed release

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under MIT; see [LICENSE](LICENSE).
