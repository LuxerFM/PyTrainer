"""The "Підказки" ("Hints") tab: hint blocks, solution lock, timer, XP preview.

Extracted from `TaskPanel` (split slice 5, module 3). The controller holds a
pointer to the panel (`p`) — hint state stays in the panel.
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
    """Hints-tab renderer and active-work counter."""

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
            _tr("Зняти позначку") if done else _tr("Позначити виконаним")
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
        button.setText(_tr("Підказка {n} · {title}").format(n=index, title=hint.title))
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

        use_button = QPushButton(_tr("Вставити розв'язок у редактор"))
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

        # Opened hints stay open across sessions — but not during a cold
        # review: everything is closed there by design
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
                # a guiding hint: the note under it matters only sometimes
                widgets["note"].setVisible(False)
                continue
            button = widgets["button"]
            note = widgets["note"]
            if left <= 0:
                button.setEnabled(True)
                button.setText(_tr("Підказка {n} · {title}").format(
                    n=widgets["index"], title=hint.title))
                note.setText(
                    _tr("Розв'язок відкрито після достатньої роботи над задачею. "
                        "Подивись — і спробуй переписати код своїми руками.")
                )
                widgets["use_button"].setVisible(True)
            else:
                button.setEnabled(False)
                widgets["use_button"].setVisible(False)
                button.setChecked(False)
                widgets["text"].setVisible(False)
                button.setText(
                    _tr("Підказка {n} · розв'язок — заблоковано").format(
                        n=widgets["index"])
                )
                note.setText(
                    _tr("Відкриється через {left} активної роботи над "
                        "задачею (з {total} хв). Працювало: {done}.").format(
                            left=format_time(left), total=p._task.minutes,
                            done=format_time(p._active_seconds))
                )

    def lock_everything(self) -> None:
        """Cold review: no hint opens, neither does the solution.

        Checks stay available: the human must pass the task as recalled, and
        the verdict will tell whether memory is real.
        """
        for widgets in self.p._hint_widgets:
            button = widgets["button"]
            button.setChecked(False)
            button.setEnabled(False)
            button.setText(
                _tr("Підказка {n} · недоступна в холодному повторенні").format(
                    n=widgets["index"])
            )
            widgets["text"].setVisible(False)
            widgets["use_button"].setVisible(False)

            note = widgets["note"]
            note.setVisible(True)
            if widgets["hint"].solution:
                note.setText(
                    _tr("Розв'язок повернеться, щойно завершиш холодне повторення.")
                )
            else:
                note.setText(
                    _tr("Холодне повторення: спершу згадай сам. Підказки "
                        "повернуться після спроби.")
                )

    def refresh_xp(self, xp_preview: int | None, hints_used: int) -> None:
        p = self.p
        if p._task is None:
            p.xp_label.setText("")
            return
        parts = []
        if xp_preview is not None:
            parts.append(_tr("Здаси зараз — отримаєш {n} XP").format(n=xp_preview))
        # the base shows only when it differs from the current —
        # otherwise the line just repeats itself
        if xp_preview is None or xp_preview != p._task.base_xp:
            parts.append(_tr("база {n} XP").format(n=p._task.base_xp))
        if hints_used:
            parts.append(_tr("підказок відкрито: {n}").format(n=hints_used))
        p.xp_label.setText(" · ".join(parts))

    @property
    def locked(self) -> bool:
        """Whether this is a cold review (hints and solution off)."""
        return self.p._locked

    def set_locked(self, locked: bool) -> None:
        """Switches cold review on/off in the hints panel."""
        from .task_panel import TAB_HINTS

        p = self.p
        p._locked = bool(locked)
        p.cold_note.setVisible(p._locked)
        p.tabs.setTabText(
            TAB_HINTS, _tr("Підказки 🔒") if p._locked else _tr("Підказки")
        )
        self.refresh_lock_state()

    def update_xp_preview(self, xp: int, hints_used: int) -> None:
        """Shows how much XP the task grants given the opened hints."""
        self.refresh_xp(xp, hints_used)

    def tick(self, active_seconds: float) -> None:
        """Refreshes the active-work counter (called by the main-window timer)."""
        p = self.p
        if p._task is None:
            return
        p._active_seconds = active_seconds
        self.refresh_lock_state()


__all__ = ["HintsView", "format_time"]
