import json
import tempfile
import unittest
from pathlib import Path

from jarvis.preferences import Preferences
from jarvis.plugins import PluginRegistry
from jarvis.security import audit_event, read_audit_log


class FoundationTests(unittest.TestCase):
    def test_preferences_validate_and_persist(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prefs.json"
            prefs = Preferences(path)
            prefs.set("assistant_name", "  ALFRED  ")
            prefs.set("speech_rate", 999)
            self.assertEqual(prefs.get("assistant_name"), "ALFRED")
            self.assertEqual(prefs.get("speech_rate"), 250)
            self.assertEqual(Preferences(path).get("assistant_name"), "ALFRED")
            with self.assertRaises(KeyError):
                prefs.set("unsafe_key", "value")

    def test_plugins_are_data_only_and_toggle(self):
        with tempfile.TemporaryDirectory() as folder:
            registry = PluginRegistry(Path(folder) / "plugins.json")
            self.assertTrue(registry.is_enabled("calculator"))
            registry.set_enabled("calculator", False)
            self.assertFalse(PluginRegistry(Path(folder) / "plugins.json").is_enabled("calculator"))
            with self.assertRaises(KeyError):
                registry.set_enabled("arbitrary-python", True)

    def test_audit_log_does_not_break_on_bad_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "audit.jsonl"
            audit_event("test", "success", "safe details", path=path)
            with path.open("a", encoding="utf-8") as handle:
                handle.write("not json\\n")
            rows = read_audit_log(path=path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["action"], "test")


if __name__ == "__main__":
    unittest.main()
