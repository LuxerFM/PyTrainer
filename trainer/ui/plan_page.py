"""The "План" ("Plan") page: what to do today, in what order, how long.

The main problem of any solo learning is not lacking material but the "where
to start?" question. So instead of a 47-task list there are a few steps for
one evening: first what is being forgotten, then the weak spot, then new.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, Qt, Signal
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


def _tr(text: str) -> str:
    return QCoreApplication.translate("PlanPage", text)


KIND_COLOUR = {
    "review": Colors.warn,
    "weak": Colors.error,
    "new": Colors.success,
}


def _kind_label(kind: str) -> str:
    # Literals sit inside translate() calls so lupdate can extract them.
    return {
        "review": _tr("повторення"),
        "weak": _tr("слабке місце"),
        "new": _tr("нова задача"),
    }.get(kind, kind)


def _human_minutes(minutes: int) -> str:
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return _tr("{h} год {m} хв").format(h=hours, m=rest)
    if hours:
        return _tr("{h} год").format(h=hours)
    return _tr("{m} хв").format(m=rest)


class PlanPage(QWidget):
    """Short day plan: clickable steps."""

    task_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(6)

        self.summary = QLabel(_tr("План на сьогодні"))
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
            _tr("Усе написане вже здано 🎉 Наступні блоки плану ще в розробці — "
                "а поки що повертайся до слабких тем, щоб не втратити форму.")
        )
        self.empty.setObjectName("Subtle")
        self.empty.setWordWrap(True)
        box.addWidget(self.empty)

    def set_plan(self, plan: DailyPlan) -> None:
        """Draws the plan: step count, time estimate and the steps."""
        self.steps.clear()
        self.empty.setVisible(plan.empty)

        if plan.empty:
            self.summary.setText(_tr("План на сьогодні порожній"))
            self.note.setText(
                _tr("Це не помилка: або все здано, або черга повторень порожня.")
            )
            self.note.setVisible(True)
            return

        self.summary.setText(
            _tr("План на сьогодні · {n} кроків · ≈{time}").format(
                n=len(plan.steps), time=_human_minutes(plan.minutes))
        )
        self.note.setText(
            _tr("Порядок не випадковий: спершу те, що ось-ось забудеться, потім "
                "слабке місце, і аж потім нове.")
        )
        self.note.setVisible(True)

        for index, step in enumerate(plan.steps, start=1):
            item = QListWidgetItem(
                f"{index}. {step.title}\n"
                f"{_kind_label(step.kind)} · "
                f"~{step.minutes} {_tr('хв')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, step.task_id)
            item.setForeground(QColor(KIND_COLOUR.get(step.kind, Colors.text)))
            item.setToolTip(f"{step.reason}\n{step.topic}")
            self.steps.addItem(item)

    def _on_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_selected.emit(task_id)
