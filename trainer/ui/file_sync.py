"""Disk mirrors of the progress: roadmap, progress.json, export, rollback.

Extracted from `MainWindow` so the window does not grow with every file
feature. The controller holds a pointer to the window (`w`) and uses its
`db`, `session`, paths and status bar — so after a database rollback the
window sees the new database with no extra wiring.

Mirrors are not the source of truth (SQLite is), so background writes go at
most every `FILES_WRITE_INTERVAL`, while explicit actions (closing, rollback,
import, the "Refresh" button) always write.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from curriculum import study_tasks
from curriculum.roadmap_md import write as write_roadmap

from ..core.db import Database, list_backups, restore_backup
from ..paths import atomic_write_text

if TYPE_CHECKING:
    from .main_window import MainWindow

FILES_WRITE_INTERVAL = 180.0


def _tr(text: str) -> str:
    return QCoreApplication.translate("FileSync", text)


class FileSync:
    """Window file operations."""

    def __init__(self, window: MainWindow) -> None:
        self.w = window
        self._last_write: float | None = None

    # -- throttling --

    def due(self, force: bool) -> bool:
        """Whether mirrors are due on disk (or an explicit `force=True` action).

        The first write is always allowed: `monotonic()` in a fresh container
        may be smaller than the interval (it counts from system start, not
        the epoch) — otherwise the file would never be created at all.
        """
        if force or self._last_write is None:
            return True
        return time.monotonic() - self._last_write >= FILES_WRITE_INTERVAL

    # -- mirrors --

    def rewrite_roadmap(self, silent: bool = False, force: bool = False) -> None:
        if not self.due(force):
            return
        db = self.w.db
        write_roadmap(
            self.w.roadmap_path,
            db.statuses(),
            {"xp": db.total_xp(), "streak": db.streak()},
        )
        self._last_write = time.monotonic()
        if not silent:
            self.w.status_msg.setText(
                _tr("Роадмап оновлено: {name}").format(name=self.w.roadmap_path.name))

    def write_progress(self, silent: bool = False, force: bool = False) -> None:
        """Writes progress.json — keepable in Git and portable across machines."""
        if not self.due(force):
            return
        atomic_write_text(
            self.w.progress_path,
            json.dumps(self.w.db.snapshot(), ensure_ascii=False, indent=2),
        )
        self._last_write = time.monotonic()
        if not silent:
            self.w.status_msg.setText(
                _tr("Прогрес збережено: {name}").format(name=self.w.progress_path.name))

    # -- export / import --

    def export_progress(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self.w, _tr("Експортувати прогрес"), "progress.json", "JSON (*.json)"
        )
        if not path:
            return
        atomic_write_text(
            path,
            json.dumps(self.w.db.snapshot(), ensure_ascii=False, indent=2),
        )
        self.w.status_msg.setText(_tr("Прогрес експортовано: {name}").format(
            name=Path(path).name))

    def import_progress(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self.w, _tr("Імпортувати прогрес"), "progress.json", "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.warning(self.w, _tr("Не вдалося прочитати"),
                                _tr("Файл не схожий на progress.json.\n\n{err}").format(err=error))
            return

        restored = self.w.db.restore(data)
        self.w._refresh_all()
        self.w.rewrite_roadmap(silent=True, force=True)
        self.w._write_progress(silent=True, force=True)
        QMessageBox.information(
            self.w, _tr("Готово"),
            _tr("Відновлено задач: {n}.\n"
                "Якщо задача вже була здана — її XP і черга повторень теж підтягнулись.").format(n=restored),
        )

    def restore_from_backup(self) -> None:
        """Rolls the database back to one of the `backups/` auto-copies.

        Current state is not lost: before replacing it is saved as
        `*-pre-restore-*.db` in the same copies folder.
        """
        backups = list_backups(db_path=self.w.db.path)
        if not backups:
            QMessageBox.information(
                self.w, _tr("Немає копій"),
                _tr("Тека копій порожня — відкочувати нічого.\n"
                     "Копії робляться самі при кожному запуску."),
            )
            return

        labels = [
            f"{item['name']} — {item['mtime']:%d.%m.%Y %H:%M} — "
            f"{item['size'] / 1024:.0f} КБ"
            for item in backups
        ]
        label, ok = QInputDialog.getItem(
            self.w, _tr("Відновити з копії"), _tr("Копія:"), labels, 0, False,
        )
        if not ok:
            return
        chosen = backups[labels.index(label)]

        answer = QMessageBox.question(
            self.w, _tr("Підтвердити відкат"),
            _tr("Поточна база буде замінена копією:\n{name}\n\n"
                "Прогрес, зроблений після цієї копії, зникне з вікна — але "
                "спершу він збережеться як окрема страхова копія, "
                "її можна повернути так само.\n\nПродовжити?").format(name=chosen['name']),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        task_id = self.w._task.id if self.w._task is not None else None
        self.w._save_current_code()
        db_path = self.w.db.path
        self.w.db.close()
        try:
            safety = restore_backup(chosen["path"], db_path)
            self.w.db = Database(db_path)
            self.w.session.db = self.w.db
        except (OSError, ValueError, sqlite3.DatabaseError) as error:
            try:
                self.w.db = Database(db_path)
                self.w.session.db = self.w.db
            except (OSError, sqlite3.DatabaseError):
                pass
            QMessageBox.critical(
                self.w, _tr("Не вдалося відновити"),
                _tr("База не чіпалась.\n\n{err}").format(err=error))
            return

        self.w._refresh_all()
        self.w.rewrite_roadmap(silent=True, force=True)
        self.w._write_progress(silent=True, force=True)
        if task_id is not None:
            self.w.open_task(task_id)
        QMessageBox.information(
            self.w, _tr("Готово"),
            _tr("Базу відновлено з копії:\n{name}\n").format(name=chosen['name'])
            + (_tr("Поточний стан перед відкатом збережено як:\n{name}").format(name=safety.name)
               if safety is not None else ""),
        )

    def export_solutions(self) -> None:
        """Lays solved tasks out into files — a portfolio draft already."""
        db = self.w.db
        done = [task for task in study_tasks()
                if db.status(task.id) == "done" and db.saved_code(task.id)]
        if not done:
            QMessageBox.information(
                self.w, _tr("Немає що експортувати"),
                _tr("Спершу здай хоча б одну задачу з тестами — і її код буде "
                     "що експортувати."),
            )
            return

        folder = QFileDialog.getExistingDirectory(
            self.w, _tr("Куди зберегти розв'язані задачі"))
        if not folder:
            return

        target = Path(folder)
        index_lines = [
            "# Мої розв'язані задачі",
            "",
            "Код із тренажера PyTrainer. Кожен файл — окрема задача: "
            "запусти будь-який із них командою `python <файл>`.",
            "",
        ]
        written = 0
        for task in done:
            code = db.saved_code(task.id)
            if not code:
                continue
            header = (f'"""Задача «{task.title}» ({task.level}) — '
                      'тренажер PyTrainer."""\n\n')
            atomic_write_text(target / f"{task.id}.py", header + code)
            written += 1
            index_lines.append(
                f"- [x] {task.title} — `{task.id}.py` · {task.base_xp} XP"
            )

        index_lines += [
            "",
            f"Здано задач: {written} · XP: {db.total_xp()} · "
            f"серія днів: {db.streak()}",
        ]
        atomic_write_text(target / "README.md", "\n".join(index_lines))

        self.w.status_msg.setText(_tr("Експортовано {n} задач у {name}").format(
            n=written, name=target.name))
        QMessageBox.information(
            self.w, _tr("Готово"),
            _tr("Збережено {n} файлів і README.md у папку:\n{folder}\n\n"
                "Наступний крок із роадмапу — викласти це на GitHub.").format(
                    n=written, folder=target),
        )


__all__ = ["FILES_WRITE_INTERVAL", "FileSync"]
