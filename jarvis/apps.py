"""Discover and launch installed Windows apps through Start Menu shortcuts.

This deliberately does not run arbitrary shell commands. It only opens a shortcut
whose displayed name matches the user's requested application name.
"""
from __future__ import annotations

import os
import platform
import re
from pathlib import Path


def _shortcut_roots():
    roots = []
    appdata = os.getenv("APPDATA")
    programdata = os.getenv("PROGRAMDATA", r"C:\ProgramData")
    if appdata:
        roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    roots.append(Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    userprofile = os.getenv("USERPROFILE")
    if userprofile:
        roots.append(Path(userprofile) / "Desktop")
    public = os.getenv("PUBLIC")
    if public:
        roots.append(Path(public) / "Desktop")
    return [p for p in roots if p.exists()]


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def discover_apps(limit: int = 600) -> list[dict[str, str]]:
    """Return app display names and shortcut paths found in common Windows menus."""
    if platform.system() != "Windows":
        return []
    found = {}
    for root in _shortcut_roots():
        try:
            for path in root.rglob("*.lnk"):
                try:
                    name = path.stem.strip()
                    if name and not name.startswith(("Uninstall", "Readme")):
                        found.setdefault(_normalise(name), {"name": name, "path": str(path)})
                    if len(found) >= limit:
                        return sorted(found.values(), key=lambda item: item["name"].casefold())
                except OSError:
                    continue
        except OSError:
            continue
    return sorted(found.values(), key=lambda item: item["name"].casefold())


def open_installed_app(name: str) -> str:
    if platform.system() != "Windows":
        return "Installed-app discovery is currently supported on Windows only."
    requested = _normalise(name)
    if not requested:
        return "Tell me which installed app to open."
    apps = discover_apps()
    exact = [item for item in apps if _normalise(item["name"]) == requested]
    matches = exact or [item for item in apps if requested in _normalise(item["name"])]
    if len(matches) == 1:
        try:
            os.startfile(matches[0]["path"])
            return f"Opening {matches[0]['name']}."
        except OSError as exc:
            return f"Windows couldn't open {matches[0]['name']}: {exc}"
    if len(matches) > 1:
        names = ", ".join(item["name"] for item in matches[:8])
        return f"More than one app matches '{name}': {names}. Say a more specific name."
    return (f"I couldn't find a Start Menu shortcut for '{name}'. "
            "Install the app normally or use its Start Menu shortcut, then try again.")


def list_installed_apps(limit: int = 40) -> list[str]:
    return [item["name"] for item in discover_apps(limit=600)[:limit]]
