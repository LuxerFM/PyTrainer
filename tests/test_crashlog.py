"""Тести версії й креш-логу: користувач має бачити, що саме впало і де."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trainer import __version__  # noqa: E402
from trainer.cli import main as cli_main  # noqa: E402
from trainer.core import crashlog  # noqa: E402


class CrashlogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(crashlog.reset_for_tests)
        crashlog.reset_for_tests()

    def test_version_matches_package(self):
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")
        self.assertIn(__version__, crashlog.version_line())

    def test_cli_version_flag(self):
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli_main(["pytrainer", "--version"])
        self.assertEqual(code, 0)
        self.assertIn(__version__, buffer.getvalue())

    def test_setup_writes_log_in_given_folder(self):
        folder = Path(self.tmp.name) / "logs"
        log = crashlog.setup_crashlog(folder)
        self.assertTrue(log.exists())
        self.assertIn("PyTrainer", log.read_text(encoding="utf-8"))

    def test_unhandled_exception_lands_in_crash_file(self):
        folder = Path(self.tmp.name) / "logs"
        crashlog.setup_crashlog(folder)
        try:
            raise ValueError("тестовий бум")
        except ValueError:
            kind, value, tb = sys.exc_info()
            crashlog._excepthook(kind, value, tb)
        crashes = list(folder.glob("crash-*.log"))
        self.assertEqual(len(crashes), 1)
        text = crashes[0].read_text(encoding="utf-8")
        self.assertIn("тестовий бум", text)
        self.assertIn(__version__, text)

    def test_build_info_defaults_to_code(self):
        self.assertTrue(crashlog.build_info())


if __name__ == "__main__":
    unittest.main()
