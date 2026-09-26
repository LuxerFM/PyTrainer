"""Вікно «Тижневий огляд»: сім днів навчання, прочитані за дві хвилини.

Щоденний план відповідає на питання «що робити сьогодні». Раз на тиждень
потрібне інше питання: «і що з цього вийшло?». Вікно нічого не рахує само —
усе вже є в `core/digest.py`; тут лише розкладка, щоб числа не доводилося
шукати по різних сторінках, і кнопка «зберегти», бо звіт читають і через
місяць, коли програма вже показує зовсім інші цифри.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.digest import DAYS, WeeklyDigest, write_digest
from .theme import Colors

TASK_ROLE = Qt.ItemDataRole.UserRole


class DigestDialog(QDialog):
    """Тижневий огляд: вердикт, числа, списки й кнопка «зберегти звіт»."""

    task_selected = Signal(str)          # натиснули на задачу в списку

    def __init__(self, digest: WeeklyDigest, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Тижневий огляд")
        self.resize(580, 760)
        self._digest = digest

        box = QVBoxLayout(self)
        box.setContentsMargins(16, 14, 16, 14)
        box.setSpacing(8)

        self.title = QLabel(digest.title)
        self.title.setObjectName("TaskTitle")
        box.addWidget(self.title)

        subtitle = QLabel(
            "Огляд складається сам: із журналу спроб, черги повторень і журналу "
            "помилок. Це не оцінка, а відповідь на питання «що робити далі»."
        )
        subtitle.setObjectName("Subtle")
        subtitle.setWordWrap(True)
        box.addWidget(subtitle)

        self.verdict = QLabel(digest.verdict)
        self.verdict.setWordWrap(True)
        box.addWidget(self.verdict)

        grid = QGridLayout()
        grid.setSpacing(6)
        self.cards: dict[str, QLabel] = {}
        for index, (key, caption) in enumerate((
            ("solved", "здано нових"),
            ("checks", "перевірок"),
            ("passes", "успішних"),
            ("days", f"днів із {DAYS}"),
            ("streak", "серія днів"),
            ("xp", "XP загалом"),
        )):
            value, card = self._card("—", caption)
            self.cards[key] = value
            grid.addWidget(card, index // 3, index % 3)
        box.addLayout(grid)

        self.solved_list = self._section(box, "ЩО ЗДАНО")
        self.hardest_list = self._section(box, "НАЙВАЖЧЕ")
        self.mistakes_list = self._section(box, "ПОМИЛКИ")
        self.actions_list = self._section(box, "ЩО РОБИТИ ДАЛІ")

        for widget in (self.solved_list, self.hardest_list,
                       self.mistakes_list, self.actions_list):
            widget.itemClicked.connect(self._on_clicked)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Зберегти звіт…")
        self.save_button.setObjectName("Ghost")
        self.save_button.setToolTip(
            "Markdown-файл — його можна перечитати через місяць, коли цифри "
            "в тренажері вже інші"
        )
        # Аргумент у слоті не потрібен: clicked передає checked, а він зайвий.
        self.save_button.clicked.connect(lambda _=False: self.save_report())
        buttons.addWidget(self.save_button)

        self.saved_note = QLabel("")
        self.saved_note.setObjectName("Subtle")
        buttons.addWidget(self.saved_note, 1)

        self.close_button = QPushButton("Закрити")
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.close_button)
        box.addLayout(buttons)

        self.set_digest(digest)

    # ---------- побудова ----------

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

    def _section(self, box: QVBoxLayout, title: str) -> QListWidget:
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        box.addWidget(label)

        widget = QListWidget()
        widget.setWordWrap(True)
        widget.setMaximumHeight(110)
        box.addWidget(widget)
        return widget

    # ---------- дані ----------

    def set_digest(self, digest: WeeklyDigest) -> None:
        """Малює огляд. Викликається і після кожної перевірки, якщо вікно відкрите."""
        self._digest = digest
        self.title.setText(digest.title)
        self.verdict.setText(digest.verdict)
        self._paint_verdict()

        self.cards["solved"].setText(str(len(digest.solved)))
        self.cards["checks"].setText(str(digest.checks))
        self.cards["passes"].setText(str(digest.passes))
        self.cards["days"].setText(f"{digest.days_active}/{DAYS}")
        self.cards["streak"].setText(str(digest.streak))
        self.cards["xp"].setText(str(digest.xp))

        self._fill(
            self.solved_list,
            [(f"✓  {title}", task_id, Colors.success)
             for task_id, title in digest.solved],
            "Нічого — і це нормально, якщо тиждень був важкий.",
        )
        self._fill(
            self.hardest_list,
            [(f"⚠  {title} — {count} провалів", task_id, Colors.warn)
             for task_id, title, count in digest.hardest],
            "Провалів не було.",
        )
        self._fill(
            self.mistakes_list,
            [(f"●  {self._task_title(state.task_id)} — {state.kind} · "
              f"{state.times}× · {state.label}", state.task_id,
              Colors.error if state.is_open else Colors.warn)
             for state in digest.mistakes],
            "За тиждень жодної помилки в журналі.",
        )
        self._fill(self.actions_list, self._actions(), "Усе зроблено 🎉")

    def _actions(self) -> list[tuple[str, str | None, str]]:
        """Що робити далі — тим самим порядком, що й у плані на день."""
        rows: list[tuple[str, str | None, str]] = []
        if self._digest.reviews_due:
            rows.append((
                f"↻  Повторити: {self._digest.reviews_due} задач — вони вже "
                "в черзі повторень",
                None, Colors.warn,
            ))
        if self._digest.weak_pick:
            topic = f" «{self._digest.weak_topic}»" if self._digest.weak_topic else ""
            rows.append((
                f"⚠  Слабка тема{topic}: {self._digest.weak_pick[1]}",
                self._digest.weak_pick[0], Colors.error,
            ))
        for task_id, title in self._digest.next_tasks:
            rows.append((f"→  Нова задача: {title}", task_id, Colors.success))
        return rows

    @staticmethod
    def _task_title(task_id: str) -> str:
        from curriculum import find_task

        task = find_task(task_id)
        return task.title if task else task_id

    def _fill(self, widget: QListWidget, rows, empty_text: str) -> None:
        widget.clear()
        if not rows:
            item = QListWidgetItem(empty_text)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            widget.addItem(item)
            return
        for text, task_id, colour in rows:
            item = QListWidgetItem(text)
            item.setForeground(QColor(colour))
            if task_id:
                item.setData(TASK_ROLE, task_id)
                item.setToolTip("Натисни, щоб відкрити задачу")
            widget.addItem(item)

    def _paint_verdict(self) -> None:
        """Колір вердикту задає тему, а не віджет — інакше Ctrl+D лишав би старий."""
        kind = "Good" if self._digest.active and not self._digest.open_mistakes \
            else "Warn"
        self.verdict.setObjectName(kind)
        self.verdict.style().unpolish(self.verdict)
        self.verdict.style().polish(self.verdict)

    # ---------- дії ----------

    def _on_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(TASK_ROLE)
        if not task_id:
            return
        self.task_selected.emit(task_id)
        self.close()

    def save_report(self) -> None:
        suggested = f"pytrainer-week-{self._digest.start}.md"
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти тижневий звіт", suggested, "Markdown (*.md)"
        )
        if not path:
            return
        try:
            write_digest(path, self._digest, generated=datetime.now())
        except OSError as error:
            QMessageBox.warning(self, "Не вдалося зберегти",
                                f"Файл не записався.\n\n{error}")
            return
        self.saved_note.setText(f"Збережено: {Path(path).name}")
