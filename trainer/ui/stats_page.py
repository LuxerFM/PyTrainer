"""Сторінка «Прогрес»: картки, слабкі теми й календар активності.

Окремо показуємо не лише «здано», а й «утримано» — задачу, яку більше
не треба повторювати. Саме друга цифра чесно описує рівень знань.
"""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme import Colors

WEEKS = 8


class ActivityGrid(QWidget):
    """Календар активності: 8 тижнів × 7 днів, як у GitHub."""

    CELL = 11
    GAP = 3

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._activity: dict[str, int] = {}
        self.setMinimumHeight(7 * (self.CELL + self.GAP))

    def set_activity(self, activity: dict[str, int]) -> None:
        self._activity = activity
        self.update()

    def _cell_color(self, count: int) -> QColor:
        if count <= 0:
            return QColor(Colors.elevated)
        if count < 3:
            return QColor(Colors.selection)
        if count < 6:
            return QColor("#3f74c9")
        return QColor(Colors.accent)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)

        today = date.today()
        start = today - timedelta(days=today.weekday()) - timedelta(weeks=WEEKS - 1)

        for week in range(WEEKS):
            for day in range(7):
                current = start + timedelta(days=week * 7 + day)
                if current > today:
                    continue
                count = self._activity.get(current.isoformat(), 0)
                painter.setBrush(self._cell_color(count))
                painter.drawRoundedRect(
                    week * (self.CELL + self.GAP),
                    day * (self.CELL + self.GAP),
                    self.CELL,
                    self.CELL,
                    3,
                    3,
                )
        painter.end()


class StatsPage(QWidget):
    """Картки + слабкі теми + календар."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.cards: dict[str, QLabel] = {}
        definitions = (
            ("done", "здано задач"),
            ("mastered", "утримано"),
            ("xp", "XP"),
            ("streak", "серія днів"),
            ("rate", "успішність спроб"),
            ("time", "час у тренажері"),
        )
        for index, (key, caption) in enumerate(definitions):
            value_label, card = self._card("—", caption)
            self.cards[key] = value_label
            grid.addWidget(card, index // 2, index % 2)
        box.addLayout(grid)

        weak_title = QLabel("СЛАБКІ МІСЦЯ")
        weak_title.setObjectName("SectionTitle")
        box.addWidget(weak_title)

        self.weak_list = QListWidget()
        self.weak_list.setWordWrap(True)
        box.addWidget(self.weak_list, 1)

        self.weak_empty = QLabel(
            "Поки що все рівно. Слабкі теми з'являться, коли буде кілька провалів — "
            "і саме їх тренажер підсвітить."
        )
        self.weak_empty.setObjectName("Subtle")
        self.weak_empty.setWordWrap(True)
        box.addWidget(self.weak_empty)

        activity_title = QLabel("АКТИВНІСТЬ · 8 ТИЖНІВ")
        activity_title.setObjectName("SectionTitle")
        box.addWidget(activity_title)

        self.activity = ActivityGrid()
        box.addWidget(self.activity)
        legend = QLabel("кожна клітинка — день, насиченіший колір = більше запусків")
        legend.setObjectName("Subtle")
        legend.setWordWrap(True)
        box.addWidget(legend)

    def _card(self, value: str, caption: str) -> tuple[QLabel, QFrame]:
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setObjectName("StatValue")
        caption_label = QLabel(caption)
        caption_label.setObjectName("StatCaption")
        layout.addWidget(value_label)
        layout.addWidget(caption_label)
        return value_label, frame

    def set_data(self, overall: dict, weak: list, activity: dict[str, int],
                 xp: int, streak: int, active_seconds: float = 0.0) -> None:
        self.cards["done"].setText(
            f'{overall.get("done", 0)}/{overall.get("total", 0)}'
        )
        self.cards["mastered"].setText(str(overall.get("mastered", 0)))
        self.cards["xp"].setText(str(xp))
        self.cards["streak"].setText(str(streak))
        rate = overall.get("success_rate", 0.0)
        self.cards["rate"].setText(f"{round(rate * 100)}%")
        self.cards["time"].setText(f"{int(active_seconds) // 3600} год")

        self.weak_list.clear()
        for stat in weak:
            item = QListWidgetItem(
                f"{stat.name}\n"
                f"успішних спроб {round(stat.success_rate * 100)}% "
                f"({stat.passes} із {stat.attempts}) · здано {stat.done}/{stat.total}"
            )
            item.setForeground(QColor(Colors.warn))
            self.weak_list.addItem(item)
        self.weak_list.setVisible(bool(weak))
        self.weak_empty.setVisible(not weak)

        self.activity.set_activity(activity)
