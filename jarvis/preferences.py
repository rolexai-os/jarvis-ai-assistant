"""Small, validated local preferences stored outside the repository."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULTS = {"assistant_name": "JARVIS", "theme": "dark", "speech_rate": 175, "voice_enabled": True}


class Preferences:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path.home() / ".jarvis-ai" / "preferences.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.values = dict(DEFAULTS)
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.values.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        except (OSError, json.JSONDecodeError):
            pass
        self._validate()

    def _validate(self):
        name = self.values.get("assistant_name")
        self.values["assistant_name"] = name.strip()[:32] if isinstance(name, str) and name.strip() else DEFAULTS["assistant_name"]
        if self.values.get("theme") not in {"dark", "light"}:
            self.values["theme"] = "dark"
        try:
            self.values["speech_rate"] = max(100, min(250, int(self.values["speech_rate"])))
        except (TypeError, ValueError):
            self.values["speech_rate"] = DEFAULTS["speech_rate"]
        self.values["voice_enabled"] = bool(self.values.get("voice_enabled"))

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        if key not in DEFAULTS:
            raise KeyError(f"Unsupported preference: {key}")
        old = self.values.get(key)
        self.values[key] = value
        self._validate()
        self.save()
        return self.values.get(key, old)

    def save(self):
        self._validate()
        self.path.write_text(json.dumps(self.values, indent=2), encoding="utf-8")
