"""Тести теки даних: де лежить прогрес і як він переїжджає зі старої теки.

Це не дрібниця. База з багатомісячним прогресом не має лежати в теці, яку
синхронізує хмара: вона читає файл тоді, коли їй захочеться, і може зробити це
посеред запису — саме так SQLite і псують. І переїзд не має права нічого
втратити, тому перевіряємо й сам перенос, і те, що старий файл лишається.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from trainer import paths
from trainer.core.db import Database


class DataFolderTests(unittest.TestCase):
    def test_env_variable_overrides_the_default(self) -> None:
        with mock.patch.dict(os.environ, {paths.DATA_ENV: str(Path("C:/Portable"))}):
            self.assertEqual(paths.data_folder(), Path("C:/Portable"))
            self.assertEqual(paths.database_path(),
                             Path("C:/Portable") / "pytrainer.db")

    def test_default_folder_is_named_and_outside_the_project(self) -> None:
        """Типова тека — службова, а не поруч із проєктом чи .exe."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(paths.DATA_ENV, None)
            folder = paths.data_folder()

        self.assertEqual(folder.name, paths.APP_NAME)
        self.assertNotIn(paths.app_folder(), folder.parents)

    def test_human_files_stay_next_to_the_app(self) -> None:
        """Роадмап і progress.json — текстові, їм синхронізація не шкодить."""
        self.assertEqual(paths.app_folder() / "Python-Roadmap.md",
                         paths.app_folder() / "Python-Roadmap.md")
        self.assertNotEqual(paths.database_path().parent, paths.app_folder())

    def test_apply_data_dir_reads_the_flag(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(paths.DATA_ENV, None)
            self.addCleanup(lambda: os.environ.pop(paths.DATA_ENV, None))

            value = paths.apply_data_dir(["main.py", "--data-dir", "D:\\PyTrainer"])

            self.assertEqual(value, "D:\\PyTrainer")
            self.assertEqual(paths.data_folder(), Path("D:\\PyTrainer"))

    def test_apply_data_dir_without_a_value_changes_nothing(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(paths.DATA_ENV, None)
            self.assertIsNone(paths.apply_data_dir(["main.py", "--data-dir"]))
            self.assertIsNone(paths.apply_data_dir(["main.py"]))
            self.assertNotIn(paths.DATA_ENV, os.environ)


class AtomicWriteTests(unittest.TestCase):
    """Атомарний запис: читач бачить або старий файл цілком, або новий."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name) / "progress.json"

    def test_writes_content(self):
        paths.atomic_write_text(self.target, '{"a": 1}')
        self.assertEqual(self.target.read_text(encoding="utf-8"), '{"a": 1}')

    def test_overwrite_leaves_no_tmp_files(self):
        paths.atomic_write_text(self.target, "старе")
        paths.atomic_write_text(self.target, "нове")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "нове")
        leftovers = list(Path(self.tmp.name).glob("progress.json.*.tmp"))
        self.assertEqual(leftovers, [])


class MigrationTests(unittest.TestCase):
    """Перенос бази й копій зі старої теки в теку даних."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.legacy = self.root / "legacy"          # умовна тека поруч із .exe
        self.target = self.root / "data"
        self.legacy.mkdir()

        db = Database(self.legacy / "pytrainer.db")
        db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100, clean=True)
        db.mark_solved("w1-hello", 100)
        db.close()

        backups = self.legacy / paths.BACKUP_FOLDER
        backups.mkdir()
        for name in ("pytrainer-20260101-101010-00.db",
                     "pytrainer-20260102-101010-00.db"):
            (backups / name).write_bytes(b"kopiya")

    def test_database_moves_and_the_old_file_stays_as_moved(self) -> None:
        moved = paths.migrate_data(self.target, self.legacy)

        self.assertIn("pytrainer.db", moved)
        new_db = Database(self.target / "pytrainer.db")
        self.addCleanup(new_db.close)
        self.assertEqual(new_db.total_xp(), 100)
        self.assertEqual(new_db.status("w1-hello"), "done")

        self.assertFalse((self.legacy / "pytrainer.db").exists())
        self.assertTrue((self.legacy / "pytrainer.db.moved").exists(),
                        "старий файл має лишитись як страховка")

    def test_backups_move_too(self) -> None:
        moved = paths.migrate_data(self.target, self.legacy)

        self.assertTrue(any(paths.BACKUP_FOLDER in item for item in moved))
        copied = sorted(item.name for item in
                        (self.target / paths.BACKUP_FOLDER).glob("*.db"))
        self.assertEqual(copied, ["pytrainer-20260101-101010-00.db",
                                  "pytrainer-20260102-101010-00.db"])
        self.assertTrue((self.legacy / "backups.moved").is_dir())

    def test_second_run_does_nothing(self) -> None:
        paths.migrate_data(self.target, self.legacy)
        self.assertEqual(paths.migrate_data(self.target, self.legacy), [])

    def test_nothing_to_move_is_not_an_error(self) -> None:
        empty = self.root / "empty"
        empty.mkdir()
        self.assertEqual(paths.migrate_data(self.root / "nowhere", empty), [])
        self.assertFalse((self.root / "nowhere").exists())

    def test_existing_target_is_never_overwritten(self) -> None:
        """Якщо в новій теці вже є база — вона головніша за стару."""
        self.target.mkdir()
        fresh = Database(self.target / "pytrainer.db")
        fresh.record_attempt("w1-vars", ok=True, with_checks=True, xp=50)
        fresh.close()

        moved = paths.migrate_data(self.target, self.legacy)

        self.assertNotIn("pytrainer.db", moved)
        self.assertIn("pytrainer.db.moved", moved)      # старій базі дали спокій
        check = Database(self.target / "pytrainer.db")
        self.addCleanup(check.close)
        self.assertEqual(check.attempts_count("w1-vars"), 1)


if __name__ == "__main__":
    unittest.main()
