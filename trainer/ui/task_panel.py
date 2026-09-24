"""Права панель: умова задачі, перевірки, підказки за таймером та історія.

Розв'язок заблоковано, поки не набіжить достатньо часу активної роботи над
задачею. Це прямо реалізує правило з роадмапу: ШІ — вчитель, а не автор коду.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QTabWidget,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from curriculum.schema import Task

from ..core.runner import RunResult
from .theme import Colors


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


class TaskPanel(QWidget):
    """Показує умову, результати перевірки, підказки та історію спроб."""

    hint_revealed = Signal(int, bool)  # (рівень підказки, чи це повний розв'язок)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setMinimumWidth(340)

        self._task: Task | None = None
        self._hint_widgets: list[dict] = []
        self._active_seconds = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_statement_tab(), "Задача")
        self.tabs.addTab(self._build_tests_tab(), "Тести")
        self.tabs.addTab(self._build_hints_tab(), "Підказки")
        self.tabs.addTab(self._build_history_tab(), "Історія")
        layout.addWidget(self.tabs, 1)

    # ---------- верхівка ----------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        box = QVBoxLayout(header)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(6)

        self.title = QLabel("Задача")
        self.title.setObjectName("TaskTitle")
        self.title.setWordWrap(True)
        box.addWidget(self.title)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.level_badge = QLabel("—")
        self.level_badge.setObjectName("Badge")
        self.topic_label = QLabel("")
        self.topic_label.setObjectName("Subtle")
        row.addWidget(self.level_badge)
        row.addWidget(self.topic_label, 1)
        box.addLayout(row)

        self.xp_label = QLabel("")
        self.xp_label.setObjectName("Subtle")
        self.xp_label.setWordWrap(True)
        box.addWidget(self.xp_label)
        return header

    # ---------- вкладки ----------

    def _build_statement_tab(self) -> QWidget:
        self.statement = QTextBrowser()
        self.statement.setOpenExternalLinks(True)
        self.statement.setContentsMargins(14, 12, 14, 12)
        return self.statement

    def _build_tests_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)

        self.tests_summary = QLabel("Ще не перевірялося")
        self.tests_summary.setWordWrap(True)
        box.addWidget(self.tests_summary)

        self.tests_list = QListWidget()
        self.tests_list.setWordWrap(True)
        box.addWidget(self.tests_list, 1)

        self.tests_detail = QLabel("")
        self.tests_detail.setWordWrap(True)
        self.tests_detail.setObjectName("Subtle")
        box.addWidget(self.tests_detail)
        return page

    def _build_hints_tab(self) -> QWidget:
        area = QScrollArea()
        area.setWidgetResizable(True)
        page = QWidget()
        self.hints_box = QVBoxLayout(page)
        self.hints_box.setContentsMargins(14, 12, 14, 12)
        self.hints_box.setSpacing(10)
        self.hints_box.addStretch(1)
        area.setWidget(page)
        return area

    def _build_history_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)

        self.history_summary = QLabel("Історії ще немає")
        self.history_summary.setWordWrap(True)
        box.addWidget(self.history_summary)

        self.history_list = QListWidget()
        box.addWidget(self.history_list, 1)
        return page

    # ---------- API ----------

    def show_task(
        self,
        task: Task,
        *,
        topic: str = "",
        hints_used: int = 0,
        active_seconds: float = 0.0,
        xp_preview: int | None = None,
    ) -> None:
        self._task = task
        self._active_seconds = active_seconds

        self.title.setText(task.title)
        self.level_badge.setText(task.level)
        self.topic_label.setText(topic)
        self.statement.setHtml(self._wrap_html(task.statement))
        self._refresh_xp(xp_preview, hints_used)
        self.reset_tests()
        self._build_hints(task, hints_used)
        self._refresh_lock_state()
        self.tabs.setCurrentIndex(0)

    def show_placeholder(self, title: str, message: str) -> None:
        """Задача, якої ще немає (запланована на пізніше)."""
        self._task = None
        self._hint_widgets.clear()
        self.title.setText(title)
        self.level_badge.setText("Заплановано")
        self.topic_label.setText("")
        self.xp_label.setText("")
        self.statement.setHtml(self._wrap_html(f"<p>{message}</p>"))
        self.reset_tests()
        self.history_summary.setText("Історії ще немає")
        self.history_list.clear()
        while self.hints_box.count() > 1:
            item = self.hints_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.tabs.setCurrentIndex(0)

    def set_history(self, rows, *, solved: bool, best_xp: int, hints_used: int,
                    active_seconds: float) -> None:
        self.history_list.clear()
        if not rows:
            self.history_summary.setText("Ще жодного запуску цієї задачі.")
            return

        self.history_summary.setText(
            f"Спроба з перевіркою: {'здано ✓' if solved else 'ще ні'} · "
            f"найкращий XP: {best_xp} · підказок відкрито: {hints_used} · "
            f"час над задачею: {_format_time(active_seconds)}"
        )
        for row in rows:
            mark = "✓" if row["ok"] else "✕"
            kind = "перевірка" if row["with_checks"] else "запуск"
            xp = f' · +{row["xp"]} XP' if row["xp"] else ""
            item = QListWidgetItem(f'{row["created_at"][:16].replace("T", " ")} · '
                                   f"{mark} {kind}{xp}")
            item.setForeground(QColor(Colors.success if row["ok"] else Colors.error))
            self.history_list.addItem(item)

    def update_xp_preview(self, xp: int, hints_used: int) -> None:
        """Показує, скільки XP дасть задача з урахуванням відкритих підказок."""
        self._refresh_xp(xp, hints_used)

    def tick(self, active_seconds: float) -> None:
        """Оновлює лічильник активної роботи (викликає таймер головного вікна)."""
        if self._task is None:
            return
        self._active_seconds = active_seconds
        self._refresh_lock_state()

    def reset_tests(self) -> None:
        self.tests_list.clear()
        self.tests_summary.setText("Ще не перевірялося")
        self.tests_summary.setStyleSheet(f"color: {Colors.muted};")
        self.tests_detail.setText("")

    def show_result(self, result: RunResult, with_checks: bool) -> None:
        self.tests_list.clear()

        if with_checks and result.checks:
            passed = result.passed_count
            total = len(result.checks)
            if result.all_passed:
                self.tests_summary.setText(f"Усі перевірки пройдено: {passed} із {total} ✓")
                self.tests_summary.setStyleSheet(
                    f"color: {Colors.success}; font-weight: 700;"
                )
            else:
                self.tests_summary.setText(f"Пройдено {passed} із {total} — є що виправити")
                self.tests_summary.setStyleSheet(
                    f"color: {Colors.error}; font-weight: 700;"
                )

            for check in result.checks:
                mark = "✓" if check.ok else "✕"
                item = QListWidgetItem(f"{mark}  {check.name}")
                item.setForeground(QColor(Colors.success if check.ok else Colors.error))
                if check.error:
                    item.setToolTip(check.error)
                self.tests_list.addItem(item)

            first_error = result.first_error
            if first_error:
                self.tests_detail.setText(f"Перша проблема: {first_error}")
            elif result.all_passed:
                self.tests_detail.setText("Так тримати! Наступна задача — у списку зліва.")
        elif result.timed_out:
            self.tests_summary.setText("Код зупинено за таймаутом")
            self.tests_summary.setStyleSheet(f"color: {Colors.warn}; font-weight: 700;")
            self.tests_detail.setText(
                "Схоже, цикл не завершується. Перевір умову виходу."
            )
        elif result.stderr:
            self.tests_summary.setText("Код впав з помилкою")
            self.tests_summary.setStyleSheet(f"color: {Colors.error}; font-weight: 700;")
            self.tests_detail.setText("Повний текст помилки — у консолі знизу.")
        else:
            self.tests_summary.setText("Код виконано без помилок")
            self.tests_summary.setStyleSheet(f"color: {Colors.success};")
            self.tests_detail.setText("Натисни «Перевірити», щоб прогнати тести.")

        self.tabs.setCurrentIndex(1)

    # ---------- підказки ----------

    def _build_hints(self, task: Task, hints_used: int) -> None:
        while self.hints_box.count() > 1:
            item = self.hints_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._hint_widgets.clear()

        hints = list(task.clue_hints) + ([task.solution_hint] if task.solution_hint else [])
        for index, hint in enumerate(hints, start=1):
            block, widgets = self._hint_block(index, hint, hints_used)
            self._hint_widgets.append(widgets)
            self.hints_box.insertWidget(self.hints_box.count() - 1, block)

    def _hint_block(self, index: int, hint, hints_used: int) -> tuple[QWidget, dict]:
        block = QWidget()
        box = QVBoxLayout(block)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(4)

        button = QToolButton()
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setText(f"Підказка {index} · {hint.title}")
        button.setStyleSheet(
            "QToolButton { text-align: left; padding: 8px 12px; border-radius: 8px; "
            f"background: {Colors.elevated}; border: 1px solid {Colors.border}; "
            "font-weight: 600; }"
            f"QToolButton:hover {{ border-color: {Colors.accent}; }}"
            f"QToolButton:disabled {{ color: {Colors.muted}; }}"
        )
        box.addWidget(button)

        text = QLabel(hint.text)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text.setFont(self.font())
        text.setStyleSheet(
            f"background: {Colors.elevated}; border: 1px solid {Colors.border}; "
            f"border-radius: 8px; padding: 10px 12px; color: {Colors.text};"
        )
        text.setVisible(False)
        box.addWidget(text)

        note = QLabel("")
        note.setObjectName("Subtle")
        note.setWordWrap(True)
        note.setVisible(bool(hint.solution))
        box.addWidget(note)

        widgets = {
            "button": button,
            "text": text,
            "note": note,
            "hint": hint,
            "index": index,
        }

        def toggled(checked: bool, item=widgets) -> None:
            item["text"].setVisible(checked)
            if checked:
                self.hint_revealed.emit(item["index"], bool(item["hint"].solution))

        button.toggled.connect(toggled)

        # уже відкриті підказки лишаються відкритими між сесіями
        if index <= hints_used and not hint.solution:
            button.setChecked(True)
        return block, widgets

    def _refresh_lock_state(self) -> None:
        if self._task is None:
            return
        needed = self._task.minutes * 60
        left = max(0.0, needed - self._active_seconds)

        for widgets in self._hint_widgets:
            hint = widgets["hint"]
            if not hint.solution:
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
            else:
                button.setEnabled(False)
                button.setChecked(False)
                widgets["text"].setVisible(False)
                button.setText(
                    f'Підказка {widgets["index"]} · розв\'язок — заблоковано'
                )
                note.setText(
                    f"Відкриється через {_format_time(left)} активної роботи над задачею "
                    f"(з {self._task.minutes} хв). Працювало: "
                    f"{_format_time(self._active_seconds)}."
                )

    def _refresh_xp(self, xp_preview: int | None, hints_used: int) -> None:
        if self._task is None:
            self.xp_label.setText("")
            return
        parts = [f"База: {self._task.base_xp} XP"]
        if hints_used:
            parts.append(f"підказок відкрито: {hints_used}")
        if xp_preview is not None:
            parts.append(f"зараз задача дасть {xp_preview} XP")
        self.xp_label.setText(" · ".join(parts))

    # ---------- службове ----------

    def _wrap_html(self, body: str) -> str:
        return f"""
        <style>
            body {{ color: {Colors.text}; font-size: 13px; line-height: 1.55; }}
            h4 {{ color: {Colors.accent}; margin: 14px 0 6px 0; font-size: 13px; }}
            p {{ margin: 8px 0; }}
            code {{ background: {Colors.elevated}; color: {Colors.syn_string};
                     padding: 1px 5px; border-radius: 4px; }}
            pre {{ background: {Colors.editor_bg}; color: {Colors.text};
                   padding: 10px 12px; border: 1px solid {Colors.border};
                   border-radius: 8px; white-space: pre-wrap; }}
            ol, ul {{ margin: 6px 0 6px 18px; }}
            li {{ margin: 4px 0; }}
            b {{ color: {Colors.text}; }}
            .warn {{ color: {Colors.warn}; }}
        </style>
        <body>{body}</body>
        """
