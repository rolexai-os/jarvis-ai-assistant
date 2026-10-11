import unittest
from jarvis.terminal import is_blocked_command


class TerminalSafetyTests(unittest.TestCase):
    def test_blocks_diskpart_and_format(self):
        self.assertTrue(is_blocked_command("diskpart"))
        self.assertTrue(is_blocked_command("format E:"))

    def test_blocks_bulk_delete(self):
        self.assertTrue(is_blocked_command("Remove-Item C:\\Temp -Recurse -Force"))
        self.assertTrue(is_blocked_command("del /s /q C:\\Temp"))

    def test_allows_read_only_and_development_commands(self):
        self.assertFalse(is_blocked_command("Get-ComputerInfo"))
        self.assertFalse(is_blocked_command("python --version"))
        self.assertFalse(is_blocked_command("git status"))


if __name__ == "__main__":
    unittest.main()
