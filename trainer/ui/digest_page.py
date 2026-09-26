"""The "Тижневий огляд" ("Weekly digest") window: seven study days read in two minutes.

The day plan answers "what to do today". Once a week a different question is
needed: "and what came of it?". The window computes nothing itself — it is
all in `core/digest.py`; here is just layout, so numbers never have to be
hunted across pages, plus a "save" button, since the report is reread a month
later when the program already shows quite different numbers.
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
    """Weekly digest: verdict, numbers, lists and a "save report" button."""

    task_selected = Signal(str)          # a task in the list was clicked

    def __init__(self, digest: WeeklyDigest, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Тижневий огляд"))
        self.resize(580, 760)
        self._digest = digest

        box = QVBoxLayout(self)
        box.setContentsMargins(16, 14, 16, 14)
        box.setSpacing(8)

        self.title = QLabel(digest.title)
        self.title.setObjectName("TaskTitle")
        box.addWidget(self.title)

        subtitle = QLabel(
            self.tr("Огляд складається сам: із журналу спроб, черги повторень і журналу "
                    "помилок. Це не оцінка, а відповідь на питання «що робити далі».")
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
            ("solved", self.tr("здано нових")),
            ("checks", self.tr("перевірок")),
            ("passes", self.tr("успішних")),
            ("days", self.tr("днів із {n}").format(n=DAYS)),
            ("streak", self.tr("серія днів")),
            ("xp", self.tr("XP загалом")),
        )):
            value, card = self._card("—", caption)
            self.cards[key] = value
            grid.addWidget(card, index // 3, index % 3)
        box.addLayout(grid)

        self.solved_list = self._section(box, self.tr("ЩО ЗДАНО"))
        self.hardest_list = self._section(box, self.tr("НАЙВАЖЧЕ"))
        self.mistakes_list = self._section(box, self.tr("ПОМИЛКИ"))
        self.actions_list = self._section(box, self.tr("ЩО РОБИТИ ДАЛІ"))

        for widget in (self.solved_list, self.hardest_list,
                       self.mistakes_list, self.actions_list):
            widget.itemClicked.connect(self._on_clicked)

        buttons = QHBoxLayout()
        self.save_button = QPushButton(self.tr("Зберегти звіт…"))
        self.save_button.setObjectName("Ghost")
        self.save_button.setToolTip(
            self.tr("Markdown-файл — його можна перечитати через місяць, коли цифри "
                    "в тренажері вже інші")
        )
        # No slot argument needed: clicked passes checked, which is excess.
        self.save_button.clicked.connect(lambda _=False: self.save_report())
        buttons.addWidget(self.save_button)

        self.saved_note = QLabel("")
        self.saved_note.setObjectName("Subtle")
        buttons.addWidget(self.saved_note, 1)

        self.close_button = QPushButton(self.tr("Закрити"))
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.close_button)
        box.addLayout(buttons)

        self.set_digest(digest)

    # ---------- building ----------

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

    # ---------- data ----------

    def set_digest(self, digest: WeeklyDigest) -> None:
        """Draws the digest. Also called after every check if the window is open."""
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
            self.tr("Нічого — і це нормально, якщо тиждень був важкий."),
        )
        self._fill(
            self.hardest_list,
            [(self.tr("⚠  {title} — {n} провалів").format(title=title, n=count),
              task_id, Colors.warn)
             for task_id, title, count in digest.hardest],
            self.tr("Провалів не було."),
        )
        self._fill(
            self.mistakes_list,
            [(f"●  {self._task_title(state.task_id)} — {state.kind} · "
              f"{state.times}× · {state.label}", state.task_id,
              Colors.error if state.is_open else Colors.warn)
             for state in digest.mistakes],
            self.tr("За тиждень жодної помилки в журналі."),
        )
        self._fill(self.actions_list, self._actions(), self.tr("Усе зроблено 🎉"))

    def _actions(self) -> list[tuple[str, str | None, str]]:
        """What to do next — same order as the day plan."""
        rows: list[tuple[str, str | None, str]] = []
        if self._digest.reviews_due:
            rows.append((
                self.tr("↻  Повторити: {n} задач — вони вже в черзі повторень").format(
                    n=self._digest.reviews_due),
                None, Colors.warn,
            ))
        if self._digest.weak_pick:
            topic = f" «{self._digest.weak_topic}»" if self._digest.weak_topic else ""
            rows.append((
                self.tr("⚠  Слабка тема{topic}: {pick}").format(
                    topic=topic, pick=self._digest.weak_pick[1]),
                self._digest.weak_pick[0], Colors.error,
            ))
        for task_id, title in self._digest.next_tasks:
            rows.append((self.tr("→  Нова задача: {title}").format(title=title),
                         task_id, Colors.success))
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
                item.setToolTip(self.tr("Натисни, щоб відкрити задачу"))
            widget.addItem(item)

    def _paint_verdict(self) -> None:
        """The verdict colour is set by the theme, not the widget — else Ctrl+D left it stale."""
        kind = "Good" if self._digest.active and not self._digest.open_mistakes \
            else "Warn"
        self.verdict.setObjectName(kind)
        self.verdict.style().unpolish(self.verdict)
        self.verdict.style().polish(self.verdict)

    # ---------- actions ----------

    def _on_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(TASK_ROLE)
        if not task_id:
            return
        self.task_selected.emit(task_id)
        self.close()

    def save_report(self) -> None:
        suggested = f"pytrainer-week-{self._digest.start}.md"
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Зберегти тижневий звіт"), suggested, "Markdown (*.md)"
        )
        if not path:
            return
        try:
            write_digest(path, self._digest, generated=datetime.now())
        except OSError as error:
            QMessageBox.warning(self, self.tr("Не вдалося зберегти"),
                                self.tr("Файл не записався.\n\n{err}").format(err=error))
            return
        self.saved_note.setText(self.tr("Збережено: {name}").format(name=Path(path).name))
