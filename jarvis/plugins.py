"""Minimal opt-in plugin discovery. Only install plugins you trust."""
import importlib.util
from pathlib import Path


def load_plugins(directory=None):
    folder = Path(directory) if directory else Path.home() / ".jarvis-ai" / "plugins"
    if not folder.exists():
        return []
    plugins = []
    for path in sorted(folder.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location("jarvis_plugin_" + path.stem, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if callable(getattr(module, "register", None)):
                plugins.append(module)
    return plugins
