"""Дзеркала прогресу на диск: роадмап, progress.json, експорт, відкат.

Витягнуто з `MainWindow`, щоб вікно не росло на кожній файловій фічі.
Контролер тримає вказівник на вікно (`w`) і користується його `db`,
`session`, шляхами й статус-баром — тому вікно після відкату бази бачить
нову базу без додаткових зв'язків.

Дзеркала — не джерело правди (ним є SQLite), тому фонові записи йдуть не
частіше раза на `FILES_WRITE_INTERVAL`, а явні дії (закривання, відкат,
імпорт, кнопка «Оновити») пишуть завжди.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from curriculum import study_tasks
from curriculum.roadmap_md import write as write_roadmap

from ..core.db import Database, list_backups, restore_backup
from ..paths import atomic_write_text

if TYPE_CHECKING:
    from .main_window import MainWindow

FILES_WRITE_INTERVAL = 180.0


class FileSync:
    """Файлові операції вікна."""

    def __init__(self, window: MainWindow) -> None:
        self.w = window
        self._last_write = 0.0

    # -- тротлінг --

    def due(self, force: bool) -> bool:
        """Чи час писати дзеркала на диск (або явна дія з `force=True`)."""
        if force:
            return True
        return time.monotonic() - self._last_write >= FILES_WRITE_INTERVAL

    # -- дзеркала --

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
                f"Роадмап оновлено: {self.w.roadmap_path.name}")

    def write_progress(self, silent: bool = False, force: bool = False) -> None:
        """Пише progress.json — його можна тримати в Git і переносити між машинами."""
        if not self.due(force):
            return
        atomic_write_text(
            self.w.progress_path,
            json.dumps(self.w.db.snapshot(), ensure_ascii=False, indent=2),
        )
        self._last_write = time.monotonic()
        if not silent:
            self.w.status_msg.setText(
                f"Прогрес збережено: {self.w.progress_path.name}")

    # -- експорт / імпорт --

    def export_progress(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self.w, "Експортувати прогрес", "progress.json", "JSON (*.json)"
        )
        if not path:
            return
        atomic_write_text(
            path,
            json.dumps(self.w.db.snapshot(), ensure_ascii=False, indent=2),
        )
        self.w.status_msg.setText(f"Прогрес експортовано: {Path(path).name}")

    def import_progress(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self.w, "Імпортувати прогрес", "progress.json", "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.warning(self.w, "Не вдалося прочитати",
                                f"Файл не схожий на progress.json.\n\n{error}")
            return

        restored = self.w.db.restore(data)
        self.w._refresh_all()
        self.w.rewrite_roadmap(silent=True, force=True)
        self.w._write_progress(silent=True, force=True)
        QMessageBox.information(
            self.w, "Готово",
            f"Відновлено задач: {restored}.\n"
            "Якщо задача вже була здана — її XP і черга повторень теж підтягнулись.",
        )

    def restore_from_backup(self) -> None:
        """Відкочує базу до однієї з авто-копій із `backups/`.

        Поточний стан не губиться: перед заміною він зберігається як
        `*-pre-restore-*.db` у тій самій теці копій.
        """
        backups = list_backups(db_path=self.w.db.path)
        if not backups:
            QMessageBox.information(
                self.w, "Немає копій",
                "Тека копій порожня — відкочувати нічого.\n"
                "Копії робляться самі при кожному запуску.",
            )
            return

        labels = [
            f"{item['name']} — {item['mtime']:%d.%m.%Y %H:%M} — "
            f"{item['size'] / 1024:.0f} КБ"
            for item in backups
        ]
        label, ok = QInputDialog.getItem(
            self.w, "Відновити з копії", "Копія:", labels, 0, False,
        )
        if not ok:
            return
        chosen = backups[labels.index(label)]

        answer = QMessageBox.question(
            self.w, "Підтвердити відкат",
            f"Поточна база буде замінена копією:\n{chosen['name']}\n\n"
            "Прогрес, зроблений після цієї копії, зникне з вікна — але "
            "спершу він збережеться як окрема страхова копія, "
            "її можна повернути так само.\n\nПродовжити?",
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
                self.w, "Не вдалося відновити",
                f"База не чіпалась.\n\n{error}")
            return

        self.w._refresh_all()
        self.w.rewrite_roadmap(silent=True, force=True)
        self.w._write_progress(silent=True, force=True)
        if task_id is not None:
            self.w.open_task(task_id)
        QMessageBox.information(
            self.w, "Готово",
            f"Базу відновлено з копії:\n{chosen['name']}\n"
            + (f"Поточний стан перед відкатом збережено як:\n{safety.name}"
               if safety is not None else ""),
        )

    def export_solutions(self) -> None:
        """Складає розв'язані задачі у файли — це вже заготовка портфоліо."""
        db = self.w.db
        done = [task for task in study_tasks()
                if db.status(task.id) == "done" and db.saved_code(task.id)]
        if not done:
            QMessageBox.information(
                self.w, "Немає що експортувати",
                "Спершу здай хоча б одну задачу з тестами — і її код буде "
                "що експортувати.",
            )
            return

        folder = QFileDialog.getExistingDirectory(
            self.w, "Куди зберегти розв'язані задачі")
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

        self.w.status_msg.setText(f"Експортовано {written} задач у {target.name}")
        QMessageBox.information(
            self.w, "Готово",
            f"Збережено {written} файлів і README.md у папку:\n{target}\n\n"
            "Наступний крок із роадмапу — викласти це на GitHub.",
        )


__all__ = ["FILES_WRITE_INTERVAL", "FileSync"]
