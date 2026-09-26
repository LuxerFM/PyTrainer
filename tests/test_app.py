"""Тести точки входу: прапорці командного рядка й чесна підказка без Qt.

`trainer/app.py` — це перший файл, який бачить людина, і саме тому його
найлегше зламати непомітно: тут і шляхи, і тема, і демо-режим, і знімки для
README. Тести запускають справжній `main()` (без екрана) і перевіряють, що
застосунок справді зробив те, що обіцяв прапорець.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from trainer import app as app_module  # noqa: E402
from trainer.ui.theme import Colors, apply_theme, scale, set_scale  # noqa: E402


class EntryPointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.addCleanup(self._restore_theme)

    def tearDown(self):
        self.tmp.cleanup()

    def _restore_theme(self) -> None:
        Colors.use("dark")
        set_scale(1.0)
        apply_theme(self.app)

    def test_missing_pyside_prints_a_helpful_message(self) -> None:
        """Без PySide6 має бути не traceback, а інструкція, що робити."""
        # None у sys.modules змушує `import PySide6.QtWidgets` впасти так само,
        # як на машині без Qt.
        blocker = {name: None for name in
                   ("PySide6", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets")}
        buffer = io.StringIO()
        with mock.patch.dict(sys.modules, blocker), redirect_stdout(buffer):
            code = app_module.main([])

        self.assertEqual(code, 1)
        self.assertIn("pip install -r requirements.txt", buffer.getvalue())

    def test_demo_screenshot_run_works_end_to_end(self) -> None:
        """`--demo --screenshot --theme --scale` у одному запуску.

        Це справжній прогін: застосунок створює вікно на тимчасовій базі,
        застосовує тему й масштаб, робить знімок і сам виходить.
        """
        shot = self.folder / "shot.png"
        code = app_module.main([
            "pytrainer",
            "--demo",
            "--screenshot", str(shot),
            "--theme", "light",
            "--scale", "1.05",
        ])

        self.assertEqual(code, 0)
        self.assertTrue(shot.exists(), "знімок не зроблено")
        self.assertGreater(shot.stat().st_size, 1000)
        self.assertEqual(Colors.name, "light")
        self.assertAlmostEqual(scale(), 1.05, places=2)

    def test_demo_run_does_not_touch_the_real_progress(self) -> None:
        """Демо-режим не має права створити файли поруч із проєктом."""
        before = {path.name for path in ROOT.iterdir()}
        shot = self.folder / "demo.png"

        code = app_module.main(["pytrainer", "--demo", "--screenshot", str(shot)])

        self.assertEqual(code, 0)
        self.assertEqual(before, {path.name for path in ROOT.iterdir()})

    def test_demo_run_leaves_no_temp_folder(self) -> None:
        """Тимчасова база демо прибирається, а не збирається у %TEMP%.

        Демо-режим запускають тести, скрипт знімків і CI — без прибирання
        кожен запуск лишав би по собі теку `pytrainer_demo_*`.
        """
        before = set(Path(tempfile.gettempdir()).glob("pytrainer_demo_*"))
        shot = self.folder / "clean.png"

        code = app_module.main(["pytrainer", "--demo", "--screenshot", str(shot)])

        self.assertEqual(code, 0)
        self.assertEqual(
            set(Path(tempfile.gettempdir()).glob("pytrainer_demo_*")) - before,
            set(),
            "демо-тека лишилась у %TEMP%",
        )

    def test_unknown_flag_is_ignored(self) -> None:
        """Зайвий прапорець не має валити запуск."""
        shot = self.folder / "unknown.png"
        code = app_module.main([
            "pytrainer", "--demo", "--screenshot", str(shot), "--хтозна-що",
        ])
        self.assertEqual(code, 0)
        self.assertTrue(shot.exists())


if __name__ == "__main__":
    unittest.main()
