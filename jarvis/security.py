"""Local JSONL audit trail for user-visible assistant actions."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock

_lock = Lock()


def audit_event(action: str, outcome: str = "recorded", details: str = "", path=None):
    """Append a minimal local event. Never store secrets or prompt contents."""
    target = Path(path) if path else Path.home() / ".jarvis-ai" / "security.log.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "action": str(action)[:80],
        "outcome": str(outcome)[:40],
        "details": str(details).replace("\n", " ")[:240],
    }
    with _lock:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_audit_log(limit=100, path=None):
    target = Path(path) if path else Path.home() / ".jarvis-ai" / "security.log.jsonl"
    if not target.exists():
        return []
    limit = max(1, min(int(limit), 500))
    rows = []
    for line in target.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
        except json.JSONDecodeError:
            continue
    return rows
