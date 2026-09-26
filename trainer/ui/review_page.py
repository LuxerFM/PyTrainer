"""Сторінка «Повторення»: задачі, які час згадати.

Правило просте: якщо задачу здав не з першого разу, завалив або підглянув
розв'язок — вона повертається через 1 день, потім через 3, потім через 7,
потім через 30. Так знання не вивітрюються.

Тут же — вхід у холодне повторення: випадкова вже здана задача без підказок
і розв'язку. Звичайне повторення показує знайомий код, а холодне змушує
згадати його з нуля.
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
    """Список задач на повторення: сьогодні і найближчим часом."""

    task_selected = Signal(str)
    cold_review_requested = Signal()   # «дай випадкову здану задачу без підказок»

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

        self.cold_button = QPushButton("❄  Холодне повторення: випадкова задача")
        self.cold_button.setObjectName("Ghost")
        self.cold_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cold_button.setToolTip(
            "Уже здана задача без підказок і розв'язку, з таймером. "
            "Вердикт іде в чергу повторень: згадав — інтервал довший, "
            "не згадав — задача повертається завтра."
        )
        self.cold_button.clicked.connect(
            lambda _=False: self.cold_review_requested.emit()
        )
        box.addWidget(self.cold_button)
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

    MISTAKE_COLOUR = {"open": Colors.error, "helped": Colors.warn}

    def set_mistakes(self, rows: list[dict]) -> None:
        """Останні помилки: текст помилки, скільки разів і чи вже закрито.

        Два кольори не для краси: червоне — ще «висить», жовте — закрито, але
        з опорою (підказкою чи розв'язком), тому задача просить холодного
        повторення. Без цієї різниці список довелося б або чистити цілком,
        або тримати в ньому все назавжди.
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
            "Помилка «висить», доки задачу не здано чистим проходом — без "
            "підказок і розв'язку. Жовте «закрито з допомогою» означає, що "
            "задачу варто згадати холодним повторенням."
            if helped else
            "Помилка, на якій спіткнувся, — найкорисніше, що є в цьому "
            "тренажері. Натисни, щоб повернутися до задачі."
        )

        visible = bool(rows)
        self.mistakes_list.setVisible(visible)
        self.mistakes_note.setVisible(visible)
        self.mistakes_title.setVisible(visible)
        self._has_mistakes = visible
        self._refresh_empty()
