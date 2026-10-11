"""One-file launcher for the complete JARVIS desktop assistant.

From the repository root, run:
    py main.py

The launcher loads the project's .env file and starts the same dashboard as
    py -m jarvis
It does not install packages automatically or require Administrator access.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        # The app's own entry point also supports running without python-dotenv.
        pass

    try:
        from jarvis.app import main as run_dashboard
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown package"
        print(f"JARVIS could not start: missing Python module '{missing}'.")
        print("Open PowerShell in the JARVIS repository folder, activate .venv, then run:")
        print("  python -m pip install -r requirements.txt")
        print("For optional offline speech recognition, also run:")
        print("  python -m pip install -r requirements-voice-offline.txt")
        return 1
    except Exception as exc:
        print(f"JARVIS startup failed: {type(exc).__name__}: {exc}")
        print("Run 'python -m compileall -q jarvis' to check Python syntax.")
        return 1

    try:
        run_dashboard()
    except KeyboardInterrupt:
        print("\nJARVIS stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
