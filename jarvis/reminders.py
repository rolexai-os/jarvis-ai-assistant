"""JSON-backed local reminders."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock


class ReminderStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path.home() / ".jarvis-ai" / "reminders.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.items = data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            self.items = []

    def _save(self):
        self.path.write_text(json.dumps(self.items, indent=2), encoding="utf-8")

    def add(self, task, seconds):
        due = datetime.now().astimezone() + timedelta(seconds=seconds)
        item = {"task": task, "due": due.isoformat(timespec="seconds"), "created": datetime.now().astimezone().isoformat(timespec="seconds")}
        with self.lock:
            self.items.append(item)
            self._save()
        return item

    def list_items(self):
        with self.lock:
            return list(self.items)

    def due_items(self):
        now = datetime.now().astimezone()
        due, pending = [], []
        with self.lock:
            for item in self.items:
                try:
                    (due if datetime.fromisoformat(item["due"]) <= now else pending).append(item)
                except (ValueError, KeyError):
                    pending.append(item)
            if len(due) != 0:
                self.items = pending
                self._save()
        return due
