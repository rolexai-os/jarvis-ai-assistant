"""Data-only built-in skill registry. This MVP never imports or executes plugin code."""
from __future__ import annotations

import json
from pathlib import Path

BUILTIN_PLUGINS = [
    {"id": "system-status", "name": "System status", "description": "Show read-only system telemetry", "enabled": True},
    {"id": "web-search", "name": "Web search", "description": "Open a web search in your default browser", "enabled": True},
    {"id": "calculator", "name": "Calculator", "description": "Evaluate basic arithmetic safely", "enabled": True},
]


class PluginRegistry:
    """List and toggle built-in skills; arbitrary Python plugin execution is disabled."""
    def __init__(self, path=None):
        self.path = Path(path) if path else Path.home() / ".jarvis-ai" / "plugins.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.settings = data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            self.settings = {}

    def list_plugins(self):
        return [{**item, "enabled": bool(self.settings.get(item["id"], item["enabled"]))}
                for item in BUILTIN_PLUGINS]

    def is_enabled(self, plugin_id):
        return next((item["enabled"] for item in self.list_plugins() if item["id"] == plugin_id), False)

    def set_enabled(self, plugin_id, enabled):
        valid = {item["id"] for item in BUILTIN_PLUGINS}
        if plugin_id not in valid:
            raise KeyError("Unknown built-in plugin ID")
        self.settings[plugin_id] = bool(enabled)
        self.path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        return bool(enabled)
