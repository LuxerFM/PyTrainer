"""Dialog windows: digest, help, folders, "about the trainer".

Extracted from `MainWindow` (split slice 4). The controller holds a pointer
to the window (`w`) — digest-dialog state (`digest_dialog`, `_digest`) stays
in the window, since the refresh controller touches it too.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from ..core.crashlog import log_folder, version_line
from ..paths import data_folder
from .digest_page import DigestDialog

if TYPE_CHECKING:
    from .main_window import MainWindow


def _tr(text: str) -> str:
    return QCoreApplication.translate("Dialogs", text)


class Dialogs:
    """Window dialogs and outward jumps."""

    def __init__(self, window: MainWindow) -> None:
        self.w = window

    def show_digest(self) -> None:
        """Opens the weekly digest (menu, Ctrl+Shift+W or the "Прогрес" page)."""
        w = self.w
        w._refresh_digest()
        if w.digest_dialog is None:
            dialog = DigestDialog(w._digest, w)
            dialog.task_selected.connect(self.open_from_digest)
            dialog.finished.connect(self.forget_digest)
            w.digest_dialog = dialog
        w.digest_dialog.show()
        w.digest_dialog.raise_()
        w.digest_dialog.activateWindow()

    def forget_digest(self, _result: int) -> None:
        self.w.digest_dialog = None

    def open_from_digest(self, task_id: str) -> None:
        self.w.open_task(task_id)
        self.w.sidebar.select(task_id)

    def show_shortcuts(self) -> None:
        QMessageBox.information(
            self.w, _tr("Гарячі клавіші"),
            _tr("Ctrl+Enter — запустити код\n"
                "F5 — перевірити прихованими тестами\n"
                "F6 — розібрати свій код (рев'ю)\n"
                "Ctrl+N — наступна незавершена задача\n"
                "Ctrl+L — план на сьогодні\n"
                "Ctrl+R — черга повторень\n"
                "Ctrl+Shift+R — холодне повторення випадкової задачі\n"
                "Ctrl+P — прогрес і слабкі місця\n"
                "Ctrl+Shift+W — тижневий огляд\n"
                "Ctrl+F — пошук задачі\n"
                "Ctrl+D — темна / світла тема\n"
                "Ctrl++ / Ctrl+- / Ctrl+0 — розмір шрифту\n"
                "Вкладка «Довідка» — шпаргалка з теми задачі\n"
                "Tab / Shift+Tab — відступ / зменшити відступ\n"
                "Ctrl+S — зберегти код у файл\n"
                "F1 — ця довідка"),
        )

    def open_data_folder(self) -> None:
        """Opens the folder holding the database, copies and settings.

        The human must see where their progress is: the first question that
        comes up when a copy, a move to another machine, or showing the file
        to someone else is needed.
        """
        folder = data_folder()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        self.w.status_msg.setText(_tr("Тека даних: {folder}").format(folder=folder))

    def open_log_file(self) -> None:
        target = log_folder() / "pytrainer.log"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        self.w.status_msg.setText(_tr("Журнал: {target}").format(target=target))

    def show_about(self) -> None:
        w = self.w
        QMessageBox.information(
            w, _tr("Про тренажер"),
            _tr("{ver} — тренажер Python з перевіркою коду.\n\n"
                "Твій код виконується в окремому процесі Python із таймаутом 5 с і "
                "лімітом виводу, тому навіть while True і print у циклі не "
                "зашкодять програмі.\n\n"
                "Прогрес, XP, підказки й черга повторень зберігаються в SQLite "
                "({dbname}), а Python-Roadmap.md і progress.json "
                "оновлюються самі.\n\n"
                "Тека даних: {datafolder}\n"
                "Вона лежить поза синхронізованими теками (OneDrive, Dropbox), бо "
                "хмара посеред запису псує базу SQLite. Відкрити її можна з меню "
                "«Файл».\n\n"
                "Розміри вікон, тема, масштаб шрифту й остання задача "
                "запам'ятовуються між запусками (pytrainer.ini).\n\n"
                "Журнал і креш-логи: {logfolder}\n"
                "Якщо вікно «просто закрилось» — останній crash-*.log там.").format(
                    ver=version_line(), dbname=Path(w.db.path).name,
                    datafolder=data_folder(), logfolder=log_folder()),
        )


__all__ = ["Dialogs"]
