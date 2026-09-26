"""The "Повторення" ("Reviews") page: tasks due for recall.

The rule is simple: if a task was not passed first try, failed, or its
solution was peeked — it returns after 1 day, then 3, then 7, then 30. That
way knowledge does not evaporate.

Also here is the cold-review entry: a random already-passed task with no
hints and no solution. Ordinary review shows familiar code, while cold review
forces recalling it from zero.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .theme import Colors


class ReviewPage(QWidget):
    """Review-task list: today and upcoming."""

    task_selected = Signal(str)
    cold_review_requested = Signal()   # "give a random passed task, no hints"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(6)

        self.hint_label = QLabel(
            self.tr("Задачі повертаються через 1 / 3 / 7 / 30 днів після того, як ти "
                    "здав їх не з першого разу. Натисни на задачу, щоб повторити.")
        )
        self.hint_label.setObjectName("Subtle")
        self.hint_label.setWordWrap(True)
        box.addWidget(self.hint_label)

        self.cold_button = QPushButton(self.tr("❄  Холодне повторення: випадкова задача"))
        self.cold_button.setObjectName("Ghost")
        self.cold_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cold_button.setToolTip(
            self.tr("Уже здана задача без підказок і розв'язку, з таймером. "
                    "Вердикт іде в чергу повторень: згадав — інтервал довший, "
                    "не згадав — задача повертається завтра.")
        )
        self.cold_button.clicked.connect(
            lambda _=False: self.cold_review_requested.emit()
        )
        box.addWidget(self.cold_button)
        box.addSpacing(4)

        self.today_title = QLabel(self.tr("СЬОГОДНІ"))
        self.today_title.setObjectName("SectionTitle")
        box.addWidget(self.today_title)

        self._has_reviews = False
        self._has_mistakes = False

        self.today_list = self._build_list()
        box.addWidget(self.today_list, 1)

        self.later_title = QLabel(self.tr("ДАЛІ"))
        self.later_title.setObjectName("SectionTitle")
        box.addWidget(self.later_title)

        self.later_list = self._build_list()
        box.addWidget(self.later_list, 1)

        self.empty_label = QLabel(self.tr("Черга порожня. Здавай задачі — і тут з'явиться розклад повторень."))
        self.empty_label.setObjectName("Subtle")
        self.empty_label.setWordWrap(True)
        box.addWidget(self.empty_label)

        # --- mistake journal: what exactly you tripped on ---
        self.mistakes_title = QLabel(self.tr("ТВОЇ ПОМИЛКИ"))
        self.mistakes_title.setObjectName("SectionTitle")
        box.addWidget(self.mistakes_title)

        self.mistakes_note = QLabel(
            self.tr("Помилка, на якій спіткнувся, — найкорисніше, що є в цьому "
                    "тренажері. Натисни, щоб повернутися до задачі.")
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

    # ---------- data ----------

    def set_rows(self, due_rows: list[dict], later_rows: list[dict]) -> None:
        self._fill(self.today_list, due_rows, overdue=True)
        self._fill(self.later_list, later_rows)

        self._has_reviews = bool(due_rows or later_rows)
        self._refresh_empty()
        self.today_title.setVisible(bool(due_rows))
        self.later_title.setVisible(bool(later_rows))

    def _refresh_empty(self) -> None:
        """The empty hint belongs only when both lists are empty."""
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

    # ---------- mistake journal ----------

    MISTAKE_COLOUR = {"open": Colors.error, "helped": Colors.warn}

    def set_mistakes(self, rows: list[dict]) -> None:
        """Latest mistakes: error text, how many times, whether closed.

        Two colours are not for beauty: red still "hangs", yellow is closed
        but with support (a hint or a solution), so the task asks for a cold
        review. Without this difference the list would have to be either
        wiped entirely or kept forever.
        """
        self.mistakes_list.clear()
        helped = False
        for row in rows:
            status = row.get("status", "open")
            helped = helped or status == "helped"
            label = row.get("status_label", "")
            line = (
                f'{row["title"]}\n'
                f'{row["kind"]} · {row["times"]}× · {row["when"]}'
            )
            if label:
                line += f" · {label}"
            item = QListWidgetItem(line)
            item.setData(Qt.ItemDataRole.UserRole, row["task_id"])
            item.setForeground(QColor(self.MISTAKE_COLOUR.get(status, Colors.error)))
            item.setToolTip(row.get("tooltip", ""))
            self.mistakes_list.addItem(item)

        self.mistakes_note.setText(
            self.tr("Помилка «висить», доки задачу не здано чистим проходом — без "
                    "підказок і розв'язку. Жовте «закрито з допомогою» означає, що "
                    "задачу варто згадати холодним повторенням.")
            if helped else
            self.tr("Помилка, на якій спіткнувся, — найкорисніше, що є в цьому "
                    "тренажері. Натисни, щоб повернутися до задачі.")
        )

        visible = bool(rows)
        self.mistakes_list.setVisible(visible)
        self.mistakes_note.setVisible(visible)
        self.mistakes_title.setVisible(visible)
        self._has_mistakes = visible
        self._refresh_empty()
