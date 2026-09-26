"""Вкладка «Історія»: стрічка спроб задачі.

Витягнуто з `TaskPanel` (зріз 5 розпилу, модуль 4). Контролер тримає
вказівник на панель (`p`) — віджети вкладки лишаються у панелі.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidgetItem

from .hints_view import format_time
from .theme import Colors

if TYPE_CHECKING:
    from .task_panel import TaskPanel


class HistoryView:
    """Рендер вкладки історії спроб."""

    def __init__(self, panel: TaskPanel) -> None:
        self.p = panel

    def set_history(self, rows, *, solved: bool, best_xp: int, hints_used: int,
                    active_seconds: float) -> None:
        p = self.p
        p.history_list.clear()
        if not rows:
            p.history_summary.setText("Ще жодного запуску цієї задачі.")
            return

        p.history_summary.setText(
            f"Задача: {'здано ✓' if solved else 'ще не здана'} · "
            f"XP: {best_xp} · підказок відкрито: {hints_used} · "
            f"час над задачею: {format_time(active_seconds)}"
        )
        for row in rows:
            when = row["created_at"][:16].replace("T", " ")
            if not row["with_checks"]:
                # звичайний запуск: не невдача, просто проба коду
                item = QListWidgetItem(f"{when} · ▸ запуск")
                item.setForeground(QColor(Colors.muted))
            else:
                mark = "✓" if row["ok"] else "✕"
                xp = f' · +{row["xp"]} XP' if row["xp"] else ""
                item = QListWidgetItem(f"{when} · {mark} перевірка{xp}")
                item.setForeground(
                    QColor(Colors.success if row["ok"] else Colors.error)
                )
            p.history_list.addItem(item)


__all__ = ["HistoryView"]
