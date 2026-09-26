"""Сторінка «Прогрес»: картки, слабкі теми й календар активності.

Окремо показуємо не лише «здано», а й «утримано» — задачу, яку більше
не треба повторювати. Саме друга цифра чесно описує рівень знань.
"""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.digest import WeeklyDigest
from .theme import Colors

WEEKS = 8


def _plural(count: int, one: str, few: str, many: str) -> str:
    """«1 перевірка», «2 перевірки», «5 перевірок» — інакше рядок читається як машинний."""
    if count % 10 == 1 and count % 100 != 11:
        return one
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return few
    return many


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


class XpChart(QWidget):
    """Стовпчики XP по днях: видно не лише «скільки всього», а й темп.

    Календар активності показує, що ти займався. Цей графік — наскільки
    продуктивно: два дні по 10 запусків на легких задачах і два дні над
    одною складною виглядають зовсім по-різному.
    """

    DAYS = 28

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._by_day: dict[str, int] = {}
        self.setMinimumHeight(64)

    def set_data(self, by_day: dict[str, int]) -> None:
        self._by_day = by_day
        self.update()

    def _days(self) -> list[tuple[str, int]]:
        today = date.today()
        return [
            ((today - timedelta(days=offset)).isoformat(),
             self._by_day.get((today - timedelta(days=offset)).isoformat(), 0))
            for offset in range(self.DAYS - 1, -1, -1)
        ]

    def paintEvent(self, event) -> None:  # noqa: N802
        days = self._days()
        peak = max((value for _, value in days), default=0)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        width = self.width()
        gap = 3
        bar = max(2.0, (width - gap * (len(days) - 1)) / len(days))
        baseline = self.height()

        for index, (_, value) in enumerate(days):
            height = 0.0 if not peak else max(2.0, (value / peak) * (self.height() - 6))
            colour = Colors.accent if value else Colors.elevated
            if value and peak and value < peak * 0.4:
                colour = "#3f74c9"      # середній темп — окремий відтінок
            painter.setBrush(QColor(colour))
            painter.drawRoundedRect(
                QRectF(index * (bar + gap), baseline - height, bar, height), 2, 2
            )

        if peak:
            painter.setPen(QPen(QColor(Colors.muted)))
            painter.drawText(0, 10, f"найкращий день: {peak} XP")
        painter.end()


class StatsPage(QWidget):
    """Картки + слабкі теми + календар + вхід у тижневий огляд."""

    topic_practice_requested = Signal(str)
    digest_requested = Signal()

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

        self.digest_button = QPushButton("Тижневий огляд · 7 днів")
        self.digest_button.setObjectName("Ghost")
        self.digest_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.digest_button.setToolTip(
            "Що сталося за тиждень: скільки здано, на чому спіткнувся, "
            "що робити далі. Звіт можна зберегти файлом."
        )
        self.digest_button.clicked.connect(
            lambda _=False: self.digest_requested.emit()
        )
        box.addWidget(self.digest_button)

        self.digest_line = QLabel("")
        self.digest_line.setObjectName("Subtle")
        self.digest_line.setWordWrap(True)
        box.addWidget(self.digest_line)

        weak_title = QLabel("СЛАБКІ МІСЦЯ")
        weak_title.setObjectName("SectionTitle")
        box.addWidget(weak_title)

        self.weak_list = QListWidget()
        self.weak_list.setWordWrap(True)
        self.weak_list.itemClicked.connect(self._on_weak_clicked)
        box.addWidget(self.weak_list, 1)

        self.weak_note = QLabel(
            "Натисни на тему — тренажер відкриє задачу, на якій її можна "
            "підтягнути."
        )
        self.weak_note.setObjectName("Subtle")
        self.weak_note.setWordWrap(True)
        box.addWidget(self.weak_note)

        self.weak_empty = QLabel(
            "Поки що все рівно. Слабкі теми з'являться, коли буде кілька провалів — "
            "і саме їх тренажер підсвітить."
        )
        self.weak_empty.setObjectName("Subtle")
        self.weak_empty.setWordWrap(True)
        box.addWidget(self.weak_empty)

        xp_title = QLabel("XP ЗА 4 ТИЖНІ")
        xp_title.setObjectName("SectionTitle")
        box.addWidget(xp_title)

        self.xp_chart = XpChart()
        box.addWidget(self.xp_chart)

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
                 xp: int, streak: int, active_seconds: float = 0.0,
                 xp_by_day: dict[str, int] | None = None) -> None:
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
            item.setData(Qt.ItemDataRole.UserRole, stat.name)
            item.setForeground(QColor(Colors.warn))
            item.setToolTip("Натисни, щоб тренувати цю тему")
            self.weak_list.addItem(item)
        self.weak_list.setVisible(bool(weak))
        self.weak_note.setVisible(bool(weak))
        self.weak_empty.setVisible(not weak)

        self.activity.set_activity(activity)
        self.xp_chart.set_data(xp_by_day or {})

    def set_digest_summary(self, digest: WeeklyDigest) -> None:
        """Один рядок про тиждень — щоб огляд не губився за кнопкою.

        Повний звіт відкривається кнопкою, але найважливіше видно вже тут:
        скільки перевірок було і скільки помилок ще не закрито.
        """
        if not digest.active:
            self.digest_line.setText("Цього тижня занять ще не було.")
            return
        open_count = len(digest.open_mistakes)
        self.digest_line.setText(
            f"Тиждень: {digest.checks} "
            f"{_plural(digest.checks, 'перевірка', 'перевірки', 'перевірок')} "
            f"({digest.passes} успішних) · здано {len(digest.solved)} · "
            f"відкрито {open_count} "
            f"{_plural(open_count, 'помилка', 'помилки', 'помилок')}"
        )

    def _on_weak_clicked(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.topic_practice_requested.emit(name)
