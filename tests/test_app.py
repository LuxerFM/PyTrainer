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


class BrokenDatabaseTests(unittest.TestCase):
    """Побитий файл бази не має перетворюватись у «застосунок не працює».

    Файл міг побитися від вимкнення живлення або від синхронізації з хмарою.
    Головне — не втратити його остаточно: відсуваємо вбік і починаємо нову
    базу, а тиха копія попереднього запуску лежить поруч у `backups/`.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def test_healthy_base_opens_without_notes(self) -> None:
        from trainer.core.db import Database

        database, note = app_module.open_database(Database, self.folder / "ok.db")
        self.addCleanup(database.close)
        self.assertEqual(note, "")
        self.assertTrue(database.quick_check())

    def test_broken_file_is_moved_aside_and_a_fresh_base_starts(self) -> None:
        from trainer.core.db import Database

        target = self.folder / "pytrainer.db"
        target.write_text("це взагалі не база", encoding="utf-8")

        database, note = app_module.open_database(Database, target)
        self.addCleanup(database.close)

        self.assertIn("пошкоджена", note)
        self.assertEqual(database.status("w1-hello"), "todo")   # нова база жива
        broken = list(self.folder.glob("pytrainer.db.broken-*"))
        self.assertEqual(len(broken), 1, "побитий файл має лишитись на диску")
        self.assertIn("не база", broken[0].read_text(encoding="utf-8"))


class InstanceGuardTests(unittest.TestCase):
    """Дві копії на одній базі — це два різні прогреси, які затирають один одного."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def folder(self) -> Path:
        """Тимчасова тека. Прибирання — після того, як замки відпущено."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def guard(self, folder: Path) -> "app_module.InstanceGuard":
        """Замок, який тест відпустить сам (LIFO: спершу замок, потім тека)."""
        guard = app_module.InstanceGuard(folder)
        self.addCleanup(guard.release)
        return guard

    def test_first_run_claims_the_place_and_the_second_steps_aside(self) -> None:
        folder = self.folder()
        first = self.guard(folder)
        self.assertTrue(first.claim(), "перший запуск має зайняти місце")
        self.assertTrue(first.path.exists(), "замок має лежати у теці даних")

        second = self.guard(folder)
        self.assertFalse(second.claim(), "другий запуск має поступитися")
        self.assertIn("PID", second.holder)   # видно, хто тримає базу

    def test_released_lock_lets_the_next_run_in(self) -> None:
        """Закрив застосунок — наступний запуск не бачить жодного замка."""
        folder = self.folder()
        first = self.guard(folder)
        self.assertTrue(first.claim())
        first.release()

        second = self.guard(folder)
        self.assertTrue(second.claim())

    def test_different_data_folders_do_not_conflict(self) -> None:
        """Портативний режим на іншій теці — це інший застосунок."""
        folder = self.folder()
        one = self.guard(folder / "a")
        two = self.guard(folder / "b")
        self.assertTrue(one.claim())
        self.assertTrue(two.claim())

    def test_broken_lock_file_does_not_lock_the_app_out_forever(self) -> None:
        """Сміттєвий замок — це не «вже запущено»: інакше застосунок більше
        ніколи не відкриється, бо про живий процес у такому замку нічого немає."""
        folder = self.folder()
        (folder / "pytrainer.lock").write_bytes(b"\x00\x00\x00 not-a-number\n")

        guard = self.guard(folder)
        self.assertTrue(guard.claim(), "замок без PID має бути прибраний")
        self.assertTrue(guard.recovered, "людина має дізнатись, що замок був сміттям")
        self.assertIn(str(os.getpid()), (folder / "pytrainer.lock").read_text(encoding="utf-8"))

    def test_live_lock_is_never_taken_away(self) -> None:
        """Замок живої копії не можна відібрати — навіть коли дуже хочеться."""
        from PySide6.QtCore import QLockFile

        folder = self.folder()
        holder = QLockFile(str(folder / "pytrainer.lock"))
        self.addCleanup(holder.unlock)
        self.assertTrue(holder.tryLock(200), "тест має тримати справжній замок")

        guard = self.guard(folder)
        self.assertFalse(guard.claim(), "другий запуск має поступитися")
        self.assertFalse(guard.recovered, "живий замок не можна вважати сміттям")
        self.assertTrue((folder / "pytrainer.lock").exists(), "файл живої копії має лишитись")
        self.assertIn("PID", guard.holder)

        holder.unlock()
        third = self.guard(folder)
        self.assertTrue(third.claim(), "після закриття вікна запуск має відкритись")


if __name__ == "__main__":
    unittest.main()
