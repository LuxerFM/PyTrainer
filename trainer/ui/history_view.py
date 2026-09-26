""""Історія" ("History") tab: the task's attempt strip.

Extracted from `TaskPanel` (split slice 5, module 4). The controller holds a
pointer to the panel (`p`) — the tab's widgets stay in the panel.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidgetItem

from .hints_view import format_time
from .theme import Colors

if TYPE_CHECKING:
    from .task_panel import TaskPanel


def _tr(text: str) -> str:
    return QCoreApplication.translate("HistoryView", text)


class HistoryView:
    """History-tab renderer."""

    def __init__(self, panel: TaskPanel) -> None:
        self.p = panel

    def set_history(self, rows, *, solved: bool, best_xp: int, hints_used: int,
                    active_seconds: float) -> None:
        p = self.p
        p.history_list.clear()
        if not rows:
            p.history_summary.setText(_tr("Ще жодного запуску цієї задачі."))
            return

        status = _tr("здано ✓") if solved else _tr("ще не здана")
        p.history_summary.setText(
            _tr("Задача: {status} · XP: {xp} · підказок відкрито: {hints} · "
                "час над задачею: {time}").format(
                    status=status, xp=best_xp, hints=hints_used,
                    time=format_time(active_seconds))
        )
        for row in rows:
            when = row["created_at"][:16].replace("T", " ")
            if not row["with_checks"]:
                # plain run: not a failure, just a code tryout
                item = QListWidgetItem(f"{when} · ▸ {_tr('запуск')}")
                item.setForeground(QColor(Colors.muted))
            else:
                mark = "✓" if row["ok"] else "✕"
                xp = f' · +{row["xp"]} XP' if row["xp"] else ""
                item = QListWidgetItem(f"{when} · {mark} {_tr('перевірка')}{xp}")
                item.setForeground(
                    QColor(Colors.success if row["ok"] else Colors.error)
                )
            p.history_list.addItem(item)


__all__ = ["HistoryView"]
