"""Сторінка «Повторення»: задачі, які час згадати.

Правило просте: якщо задачу здав не з першого разу, завалив або підглянув
розв'язок — вона повертається через 1 день, потім через 3, потім через 7,
потім через 30. Так знання не вивітрюються.
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

from .theme import Colors


class ReviewPage(QWidget):
    """Список задач на повторення: сьогодні і найближчим часом."""

    task_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(6)

        self.hint_label = QLabel(
            "Задачі повертаються через 1 / 3 / 7 / 30 днів після того, як ти "
            "здав їх не з першого разу. Натисни на задачу, щоб повторити."
        )
        self.hint_label.setObjectName("Subtle")
        self.hint_label.setWordWrap(True)
        box.addWidget(self.hint_label)
        box.addSpacing(4)

        self.today_title = QLabel("СЬОГОДНІ")
        self.today_title.setObjectName("SectionTitle")
        box.addWidget(self.today_title)

        self._has_reviews = False
        self._has_mistakes = False

        self.today_list = self._build_list()
        box.addWidget(self.today_list, 1)

        self.later_title = QLabel("ДАЛІ")
        self.later_title.setObjectName("SectionTitle")
        box.addWidget(self.later_title)

        self.later_list = self._build_list()
        box.addWidget(self.later_list, 1)

        self.empty_label = QLabel("Черга порожня. Здавай задачі — і тут з'явиться розклад повторень.")
        self.empty_label.setObjectName("Subtle")
        self.empty_label.setWordWrap(True)
        box.addWidget(self.empty_label)

        # --- журнал помилок: те, на чому саме ти спіткнувся ---
        self.mistakes_title = QLabel("ТВОЇ ПОМИЛКИ")
        self.mistakes_title.setObjectName("SectionTitle")
        box.addWidget(self.mistakes_title)

        self.mistakes_note = QLabel(
            "Помилка, на якій спіткнувся, — найкорисніше, що є в цьому "
            "тренажері. Натисни, щоб повернутися до задачі."
        )
        self.mistakes_note.setObjectName("Subtle")
        self.mistakes_note.setWordWrap(True)
        box.addWidget(self.mistakes_note)

        self.mistakes_list = self._build_list()
        box.addWidget(self.mistakes_list, 1)

    def _build_list(self) -> QListWidget:
        widget = QListWidget()
        widget.setWordWrap(True)
        widget.itemClicked.connect(self._on_clicked)
        return widget

    # ---------- дані ----------

    def set_rows(self, due_rows: list[dict], later_rows: list[dict]) -> None:
        self._fill(self.today_list, due_rows, overdue=True)
        self._fill(self.later_list, later_rows)

        self._has_reviews = bool(due_rows or later_rows)
        self._refresh_empty()
        self.today_title.setVisible(bool(due_rows))
        self.later_title.setVisible(bool(later_rows))

    def _refresh_empty(self) -> None:
        """Порожній підказці місце лише тоді, коли порожні обидва списки."""
        self.empty_label.setVisible(not self._has_reviews and not self._has_mistakes)

    def _fill(self, widget: QListWidget, rows: list[dict], overdue: bool = False) -> None:
        widget.clear()
        for row in rows:
            item = QListWidgetItem(f'{row["title"]}\n{row["when"]}')
            item.setData(Qt.ItemDataRole.UserRole, row["task_id"])
            colour = Colors.warn if overdue else Colors.muted
            item.setForeground(QColor(colour))
            item.setToolTip(row.get("tooltip", ""))
            widget.addItem(item)
        widget.setVisible(bool(rows))

    def _on_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_selected.emit(task_id)

    # ---------- журнал помилок ----------

    def set_mistakes(self, rows: list[dict]) -> None:
        """Останні помилки: текст помилки, скільки разів і коли."""
        self.mistakes_list.clear()
        for row in rows:
            item = QListWidgetItem(
                f'{row["title"]}\n'
                f'{row["kind"]} · {row["times"]}× · {row["when"]}'
            )
            item.setData(Qt.ItemDataRole.UserRole, row["task_id"])
            item.setForeground(QColor(Colors.error))
            item.setToolTip(row.get("tooltip", ""))
            self.mistakes_list.addItem(item)

        visible = bool(rows)
        self.mistakes_list.setVisible(visible)
        self.mistakes_note.setVisible(visible)
        self.mistakes_title.setVisible(visible)
        self._has_mistakes = visible
        self._refresh_empty()
