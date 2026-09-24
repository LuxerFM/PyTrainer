"""Сторінка «Прогрес»: загальні цифри, слабкі теми й календар активності."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
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
        # остання колонка — поточний тиждень, перший рядок — понеділок
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

        cards = QHBoxLayout()
        cards.setSpacing(8)
        self.done_value, done_card = self._card("—", "здано задач")
        self.xp_value, xp_card = self._card("—", "XP")
        self.streak_value, streak_card = self._card("—", "серія днів")
        self.rate_value, rate_card = self._card("—", "успішних спроб")
        for card in (done_card, xp_card, streak_card, rate_card):
            cards.addWidget(card)
        box.addLayout(cards)

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
        legend = QLabel("кожна клітинка — день, насиченіший колір = більше спроб")
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
                 xp: int, streak: int) -> None:
        self.done_value.setText(f'{overall.get("done", 0)}/{overall.get("total", 0)}')
        self.xp_value.setText(str(xp))
        self.streak_value.setText(str(streak))
        rate = overall.get("success_rate", 0.0)
        self.rate_value.setText(f"{round(rate * 100)}%")

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
