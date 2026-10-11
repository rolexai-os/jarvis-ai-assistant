import tempfile
import unittest
from pathlib import Path
from jarvis.core import handle_command, safe_calculate
from jarvis.reminders import ReminderStore


class CoreTests(unittest.TestCase):
    def test_calculate(self):
        self.assertEqual(safe_calculate("2 + 3 * 4"), 14)
        self.assertEqual(safe_calculate("-(5 - 8)"), 3)

    def test_reject_python_code(self):
        with self.assertRaises(ValueError):
            safe_calculate("__import__('os').system('whoami')")

    def test_help(self):
        self.assertIn("Commands:", handle_command("help"))

    def test_reminder(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ReminderStore(Path(folder) / "reminders.json")
            result = handle_command("remind me to test in 10 minutes", {"reminders": store})
            self.assertIn("Reminder saved", result)
            self.assertEqual(len(store.list_items()), 1)


if __name__ == "__main__":
    unittest.main()
