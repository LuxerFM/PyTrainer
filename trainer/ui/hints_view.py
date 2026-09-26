"""Вкладка «Підказки»: блоки підказок, замок розв'язку, таймер, XP-передпоказ.

Витягнуто з `TaskPanel` (зріз 5 розпилу, модуль 3). Контролер тримає
вказівник на панель (`p`) — стан підказок лишається у панелі.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget

from .theme import Colors

if TYPE_CHECKING:
    from ..curriculum.schema import Hint, Task

    from .task_panel import TaskPanel


def format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


class HintsView:
    """Рендер вкладки підказок і лічильника активної роботи."""

    def __init__(self, panel: TaskPanel) -> None:
        self.p = panel

    def clear_hints(self) -> None:
        p = self.p
        while p.hints_box.count() > 1:
            item = p.hints_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                p._drop_widget(widget)

    def build_manual_block(self, task_id: str, done: bool) -> None:
        p = self.p
        self.clear_hints()
        block = QWidget()
        box = QVBoxLayout(block)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)

        button = QPushButton(
            "Зняти позначку" if done else "Позначити виконаним"
        )
        button.setObjectName("Ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda _=False, task=task_id: p.manual_toggle_requested.emit(task)
        )
        box.addWidget(button)
        p.hints_box.insertWidget(p.hints_box.count() - 1, block)

    def build_hints(self, task: Task, hints_used: int) -> None:
        p = self.p
        self.clear_hints()
        p._hint_widgets.clear()

        hints = list(task.clue_hints) + ([task.solution_hint] if task.solution_hint else [])
        for index, hint in enumerate(hints, start=1):
            block, widgets = self.hint_block(index, hint, hints_used)
            p._hint_widgets.append(widgets)
            p.hints_box.insertWidget(p.hints_box.count() - 1, block)

    def hint_block(self, index: int, hint: Hint, hints_used: int) -> tuple[QWidget, dict]:
        from .task_panel import AutoHeightText, plain_to_html

        p = self.p
        block = QWidget()
        box = QVBoxLayout(block)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)

        button = QToolButton()
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setText(f"Підказка {index} · {hint.title}")
        button.setStyleSheet(
            "QToolButton { text-align: left; padding: 9px 12px; border-radius: 8px; "
            f"background: {Colors.elevated}; border: 1px solid {Colors.border}; "
            "font-weight: 600; }"
            f"QToolButton:hover {{ border-color: {Colors.accent}; }}"
            f"QToolButton:checked {{ border-color: {Colors.accent}; "
            f"background: {Colors.selection}; }}"
            f"QToolButton:disabled {{ color: {Colors.muted}; }}"
        )
        box.addWidget(button)

        text = AutoHeightText(p._wrap_html(plain_to_html(hint.text)))
        text.setStyleSheet(
            f"QTextBrowser {{ background: {Colors.elevated}; "
            f"border: 1px solid {Colors.border}; border-radius: 8px; "
            f"color: {Colors.text}; }}"
        )
        text.setVisible(False)
        box.addWidget(text)

        note = QLabel("")
        note.setObjectName("CheckDetail")
        note.setWordWrap(True)
        note.setVisible(bool(hint.solution))
        box.addWidget(note)

        use_button = QPushButton("Вставити розв'язок у редактор")
        use_button.setObjectName("Ghost")
        use_button.setCursor(Qt.CursorShape.PointingHandCursor)
        use_button.setVisible(False)
        use_button.clicked.connect(
            lambda _=False, h=hint: p.solution_use_requested.emit(h.text)
        )
        box.addWidget(use_button)

        widgets = {
            "button": button,
            "text": text,
            "note": note,
            "use_button": use_button,
            "hint": hint,
            "index": index,
        }

        def toggled(checked: bool, item=widgets) -> None:
            item["text"].setVisible(checked)
            if checked:
                p.hint_revealed.emit(item["index"], bool(item["hint"].solution))

        button.toggled.connect(toggled)

        # уже відкриті підказки лишаються відкритими між сесіями — але не під
        # час холодного повторення: там усе закрито за задумом
        if index <= hints_used and not hint.solution and not p._locked:
            button.setChecked(True)
        return block, widgets

    def refresh_lock_state(self) -> None:
        p = self.p
        if p._task is None:
            return
        if p._locked:
            self.lock_everything()
            return

        needed = p._task.minutes * 60
        left = max(0.0, needed - p._active_seconds)

        for widgets in p._hint_widgets:
            hint = widgets["hint"]
            if not hint.solution:
                # підказка-орієнтир: пояснення під нею потрібне лише колись
                widgets["note"].setVisible(False)
                continue
            button = widgets["button"]
            note = widgets["note"]
            if left <= 0:
                button.setEnabled(True)
                button.setText(f'Підказка {widgets["index"]} · {hint.title}')
                note.setText(
                    "Розв'язок відкрито після достатньої роботи над задачею. "
                    "Подивись — і спробуй переписати код своїми руками."
                )
                widgets["use_button"].setVisible(True)
            else:
                button.setEnabled(False)
                widgets["use_button"].setVisible(False)
                button.setChecked(False)
                widgets["text"].setVisible(False)
                button.setText(
                    f'Підказка {widgets["index"]} · розв\'язок — заблоковано'
                )
                note.setText(
                    f"Відкриється через {format_time(left)} активної роботи над "
                    f"задачею (з {p._task.minutes} хв). Працювало: "
                    f"{format_time(p._active_seconds)}."
                )

    def lock_everything(self) -> None:
        """Холодне повторення: жодна підказка не відкривається, розв'язок теж.

        Перевірки при цьому лишаються доступними: людина має здати задачу
        так, як згадала, і вже вердикт скаже, чи справді пам'ятає.
        """
        for widgets in self.p._hint_widgets:
            button = widgets["button"]
            button.setChecked(False)
            button.setEnabled(False)
            button.setText(
                f'Підказка {widgets["index"]} · недоступна в холодному повторенні'
            )
            widgets["text"].setVisible(False)
            widgets["use_button"].setVisible(False)

            note = widgets["note"]
            note.setVisible(True)
            if widgets["hint"].solution:
                note.setText(
                    "Розв'язок повернеться, щойно завершиш холодне повторення."
                )
            else:
                note.setText(
                    "Холодне повторення: спершу згадай сам. Підказки "
                    "повернуться після спроби."
                )

    def refresh_xp(self, xp_preview: int | None, hints_used: int) -> None:
        p = self.p
        if p._task is None:
            p.xp_label.setText("")
            return
        parts = []
        if xp_preview is not None:
            parts.append(f"Здаси зараз — отримаєш {xp_preview} XP")
        # базу показуємо лише тоді, коли вона відрізняється від поточної —
        # інакше рядок просто повторює сам себе
        if xp_preview is None or xp_preview != p._task.base_xp:
            parts.append(f"база {p._task.base_xp} XP")
        if hints_used:
            parts.append(f"підказок відкрито: {hints_used}")
        p.xp_label.setText(" · ".join(parts))

    @property
    def locked(self) -> bool:
        """Чи це холодне повторення (підказки й розв'язок вимкнено)."""
        return self.p._locked

    def set_locked(self, locked: bool) -> None:
        """Вмикає/вимикає холодне повторення в панелі підказок."""
        from .task_panel import TAB_HINTS

        p = self.p
        p._locked = bool(locked)
        p.cold_note.setVisible(p._locked)
        p.tabs.setTabText(
            TAB_HINTS, "Підказки 🔒" if p._locked else "Підказки"
        )
        self.refresh_lock_state()

    def update_xp_preview(self, xp: int, hints_used: int) -> None:
        """Показує, скільки XP дасть задача з урахуванням відкритих підказок."""
        self.refresh_xp(xp, hints_used)

    def tick(self, active_seconds: float) -> None:
        """Оновлює лічильник активної роботи (викликає таймер головного вікна)."""
        p = self.p
        if p._task is None:
            return
        p._active_seconds = active_seconds
        self.refresh_lock_state()


__all__ = ["HintsView", "format_time"]
