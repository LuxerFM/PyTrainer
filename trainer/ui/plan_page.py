"""Сторінка «План»: що робити сьогодні, у якому порядку й скільки часу.

Головна проблема будь-якого самотнього навчання — не брак матеріалу, а питання
«з чого почати?». Тому замість списку з 47 задач тут кілька кроків на один
вечір: спершу те, що забувається, потім слабке місце, далі нове.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.plan import DailyPlan
from .theme import Colors

KIND_COLOUR = {
    "review": Colors.warn,
    "weak": Colors.error,
    "new": Colors.success,
}
KIND_LABEL = {
    "review": "повторення",
    "weak": "слабке місце",
    "new": "нова задача",
}


def _human_minutes(minutes: int) -> str:
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} год {rest} хв"
    if hours:
        return f"{hours} год"
    return f"{rest} хв"


class PlanPage(QWidget):
    """Короткий план на день: клікабельні кроки."""

    task_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(6)

        self.summary = QLabel("План на сьогодні")
        self.summary.setObjectName("TaskTitle")
        self.summary.setWordWrap(True)
        box.addWidget(self.summary)

        self.note = QLabel("")
        self.note.setObjectName("Subtle")
        self.note.setWordWrap(True)
        box.addWidget(self.note)

        self.steps = QListWidget()
        self.steps.setWordWrap(True)
        self.steps.itemClicked.connect(self._on_clicked)
        box.addWidget(self.steps, 1)

        self.empty = QLabel(
            "Усе написане вже здано 🎉 Наступні блоки плану ще в розробці — "
            "а поки що повертайся до слабких тем, щоб не втратити форму."
        )
        self.empty.setObjectName("Subtle")
        self.empty.setWordWrap(True)
        box.addWidget(self.empty)

    def set_plan(self, plan: DailyPlan) -> None:
        """Малює план: кількість кроків, оцінку часу й самі кроки."""
        self.steps.clear()
        self.empty.setVisible(plan.empty)

        if plan.empty:
            self.summary.setText("План на сьогодні порожній")
            self.note.setText(
                "Це не помилка: або все здано, або черга повторень порожня."
            )
            self.note.setVisible(True)
            return

        self.summary.setText(
            f"План на сьогодні · {len(plan.steps)} кроків · "
            f"≈{_human_minutes(plan.minutes)}"
        )
        self.note.setText(
            "Порядок не випадковий: спершу те, що ось-ось забудеться, потім "
            "слабке місце, і аж потім нове."
        )
        self.note.setVisible(True)

        for index, step in enumerate(plan.steps, start=1):
            item = QListWidgetItem(
                f"{index}. {step.title}\n"
                f"{KIND_LABEL.get(step.kind, step.kind)} · ~{step.minutes} хв"
            )
            item.setData(Qt.ItemDataRole.UserRole, step.task_id)
            item.setForeground(QColor(KIND_COLOUR.get(step.kind, Colors.text)))
            item.setToolTip(f"{step.reason}\n{step.topic}")
            self.steps.addItem(item)

    def _on_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_selected.emit(task_id)
