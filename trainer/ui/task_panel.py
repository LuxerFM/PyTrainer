"""Right panel: task statement, checks, reference, hints and history.

The trainer's "information layer" lives here — everything the human must see
next to the editor:

* **Задача** ("Task") — the statement in handsome text (separate fonts for
  prose and code);
* **Тести** ("Tests") — what exactly will be checked *before* the run and
  what came out *after*, plus a human error explanation instead of an
  English traceback;
* **Рев'ю** ("Review") — the code itself reviewed: what is wrong and how to
  make it better;
* **Довідка** ("Reference") — a mini-cheatsheet matched to the task topic;
* **Підказки** ("Hints") — hints on an active-work timer (AI as teacher, not
  author);
* **Історія** ("History") — all runs and passes of this task.

The solution is locked until enough active-work time on the task accrues.
That directly implements the roadmap rule: AI is the teacher, not the code
author.

A special case is cold review (an already-passed task): hints and solution
are unavailable entirely, since the whole exercise is pulling the solution
from memory rather than recognising your own code.
"""

from __future__ import annotations

import html
import re

from PySide6.QtCore import QCoreApplication, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from curriculum import cheatsheets
from curriculum.schema import Check, Hint, Task

from ..core.codereview import NOT_REVIEWED, CodeReview, Remark
from ..core.runner import RunResult
from .hints_view import HintsView
from .history_view import HistoryView
from .review_view import ReviewView
from .test_results import TestResults
from .theme import Colors, mono_family, prose_family, ui_size

# Tab indices — so no bare number gets "lost" in the window code.
TAB_STATEMENT = 0
TAB_TESTS = 1
TAB_REVIEW = 2
TAB_CHEATSHEET = 3
TAB_HINTS = 4
TAB_HISTORY = 5


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


# --------------------------------------------------------------------------
# Hint text arrives as plain text, but must be shown handsomely:
# prose in the plain font, code lines in monospace inside a frame.
# --------------------------------------------------------------------------

_CODE_START = (
    "def ", "class ", "for ", "while ", "if ", "elif ", "else:", "return ",
    "import ", "from ", "print(", "with ", "try:", "except ", "finally:",
    "assert ", "raise ", "@", "#", ">>>",
)
_ASSIGN_RE = re.compile(r"^[A-Za-z_][\w\.\[\]'\"]*\s*[-+*/]?=[^=]")


def _looks_like_code(line: str) -> bool:
    """Heuristic: the line looks like code, not a Ukrainian sentence."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(_CODE_START):
        return True
    return bool(_ASSIGN_RE.match(stripped))


def plain_to_html(text: str) -> str:
    """Turns plain text into HTML, pulling code blocks out.

    Hints are written by a human (me) as plain text — and that is exactly
    how they are easy to edit. But they must be shown so code never melts
    into explanation. So neighbouring code lines gather into one `<pre>`,
    and the rest becomes paragraphs.
    """
    blocks: list[str] = []
    code: list[str] = []

    def flush_code() -> None:
        if code:
            blocks.append(f"<pre>{html.escape(chr(10).join(code).strip(chr(10)))}</pre>")
            code.clear()

    for line in text.splitlines():
        if _looks_like_code(line):
            code.append(line)
            continue
        flush_code()
        if line.strip():
            blocks.append(f"<p>{html.escape(line.strip())}</p>")

    flush_code()
    return "\n".join(blocks) or "<p></p>"


class AutoHeightText(QTextBrowser):
    """A QTextBrowser that fits its height to its content.

    Needed where a block must be "card-like": shows all text without adding
    its own scroll inside a scroll.
    """

    _fitting = False   # class-level attribute: resizeEvent may arrive before __init__

    def __init__(self, html_text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(10)
        if html_text:
            self.setHtml(html_text)

    def setHtml(self, text: str) -> None:  # noqa: N802 — Qt-given name
        super().setHtml(text)
        self._fit()

    def resizeEvent(self, event) -> None:  # noqa: N802 — Qt-given name
        super().resizeEvent(event)
        self._fit()

    def _fit(self) -> None:
        if self._fitting or self.document() is None:
            return
        self._fitting = True
        try:
            width = max(120, self.viewport().width())
            self.document().setTextWidth(width)
            wanted = int(self.document().size().height()) + 4
            if wanted != self.maximumHeight() or self.height() != wanted:
                self.setFixedHeight(wanted)
        finally:
            self._fitting = False


class TaskPanel(QWidget):
    """Shows the statement, check results, reference, hints and history."""

    hint_revealed = Signal(int, bool)       # (hint level, whether a full solution)
    solution_use_requested = Signal(str)    # human wants the solution in the editor
    manual_toggle_requested = Signal(str)   # item done outside the trainer
    jump_to_line_requested = Signal(int)    # put the cursor on the error line
    review_requested = Signal()             # "review my code" (the "Рев'ю" tab)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setMinimumWidth(360)

        self._task: Task | None = None
        self._locked = False
        self._hint_widgets: list[dict] = []
        self._check_cards: list[QFrame] = []
        self._active_seconds = 0.0
        self._sheets = cheatsheets.all_sheets()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_statement_tab(), self.tr("Задача"))
        self.tabs.addTab(self._build_tests_tab(), self.tr("Тести"))
        self.tabs.addTab(self._build_review_tab(), self.tr("Рев'ю"))
        self.tabs.addTab(self._build_cheatsheet_tab(), self.tr("Довідка"))
        self.tabs.addTab(self._build_hints_tab(), self.tr("Підказки"))
        self.tabs.addTab(self._build_history_tab(), self.tr("Історія"))
        layout.addWidget(self.tabs, 1)

        self.results = TestResults(self)
        self.review_view = ReviewView(self)
        self.hints_view = HintsView(self)
        self.history_view = HistoryView(self)

    # ---------- header ----------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        box = QVBoxLayout(header)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(7)

        self.title = QLabel(self.tr("Задача"))
        self.title.setObjectName("TaskTitle")
        self.title.setWordWrap(True)
        box.addWidget(self.title)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.level_badge = QLabel("—")
        self.level_badge.setObjectName("Badge")
        self.topic_label = QLabel("")
        self.topic_label.setObjectName("Subtle")
        self.topic_label.setWordWrap(True)   # a long topic must wrap, not clip
        row.addWidget(self.level_badge)
        row.addWidget(self.topic_label, 1)
        box.addLayout(row)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("Meta")
        self.meta_label.setWordWrap(True)
        box.addWidget(self.meta_label)

        self.xp_label = QLabel("")
        self.xp_label.setObjectName("Meta")
        self.xp_label.setWordWrap(True)
        box.addWidget(self.xp_label)
        return header

    # ---------- tabs ----------

    def _build_statement_tab(self) -> QWidget:
        self.statement = QTextBrowser()
        self.statement.setObjectName("Statement")
        self.statement.setOpenExternalLinks(True)
        self.statement.document().setDocumentMargin(16)
        return self.statement

    def _build_tests_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(9)

        self.tests_summary = QLabel(self.tr("Ще не перевірялося"))
        self.tests_summary.setObjectName("VerdictWarn")
        self.tests_summary.setWordWrap(True)
        box.addWidget(self.tests_summary)

        self.checks_page = QScrollArea()
        self.checks_page.setObjectName("ChecksPage")
        self.checks_page.setWidgetResizable(True)
        holder = QWidget()
        self.checks_box = QVBoxLayout(holder)
        self.checks_box.setContentsMargins(0, 0, 0, 0)
        self.checks_box.setSpacing(7)
        self.checks_box.addStretch(1)
        self.checks_page.setWidget(holder)
        box.addWidget(self.checks_page, 1)

        self.tests_detail = QLabel("")
        self.tests_detail.setObjectName("CheckDetail")
        self.tests_detail.setWordWrap(True)
        self.tests_detail.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        box.addWidget(self.tests_detail)
        return page

    def _build_review_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(9)

        self.review_summary = QLabel(NOT_REVIEWED)
        self.review_summary.setObjectName("Subtle")
        self.review_summary.setWordWrap(True)
        box.addWidget(self.review_summary)

        self.review_button = QPushButton(self.tr("Розібрати код"))
        self.review_button.setObjectName("Ghost")
        self.review_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.review_button.setToolTip(
            self.tr("Розбір не оцінює і не перевіряє: він каже, що в коді буде важко "
                    "читати іншій людині — і як це виправити (F6)")
        )
        self.review_button.clicked.connect(
            lambda _=False: self.review_requested.emit()
        )
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.review_button)
        row.addStretch(1)
        box.addWidget(holder)

        self.review_page = QScrollArea()
        self.review_page.setObjectName("ChecksPage")
        self.review_page.setWidgetResizable(True)
        inner = QWidget()
        self.review_box = QVBoxLayout(inner)
        self.review_box.setContentsMargins(0, 0, 0, 0)
        self.review_box.setSpacing(7)
        self.review_box.addStretch(1)
        self.review_page.setWidget(inner)
        box.addWidget(self.review_page, 1)
        return page

    def _build_cheatsheet_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(9)

        self.sheet_note = QLabel(
            self.tr("Міні-довідка з теми задачі. Можна вибрати будь-яку іншу — "
                    "це не впливає на XP.")
        )
        self.sheet_note.setObjectName("CheckDetail")
        self.sheet_note.setWordWrap(True)
        box.addWidget(self.sheet_note)

        self.sheet_picker = QComboBox()
        for sheet in self._sheets:
            self.sheet_picker.addItem(sheet.title)
        self.sheet_picker.currentIndexChanged.connect(self._render_sheet)
        box.addWidget(self.sheet_picker)

        self.sheet_view = QTextBrowser()
        self.sheet_view.setObjectName("CheatSheet")
        self.sheet_view.setOpenExternalLinks(True)
        self.sheet_view.document().setDocumentMargin(6)
        box.addWidget(self.sheet_view, 1)
        return page

    def _build_hints_tab(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 12, 14, 0)
        outer.setSpacing(8)

        # The cold-review note lives outside the hint list: the list is
        # rebuilt per task, while this caption must stay put.
        self.cold_note = QLabel(
            self.tr("Холодне повторення: підказки й розв'язок недоступні, доки не "
                    "завершиш спробу. Саме в цьому суть — згадати самому.")
        )
        self.cold_note.setObjectName("Warn")
        self.cold_note.setWordWrap(True)
        self.cold_note.setVisible(False)
        outer.addWidget(self.cold_note)

        area = QScrollArea()
        area.setWidgetResizable(True)
        holder = QWidget()
        self.hints_box = QVBoxLayout(holder)
        self.hints_box.setContentsMargins(0, 0, 0, 12)
        self.hints_box.setSpacing(10)
        self.hints_box.addStretch(1)
        area.setWidget(holder)
        outer.addWidget(area, 1)
        return page

    def _build_history_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)

        self.history_summary = QLabel(self.tr("Історії ще немає"))
        self.history_summary.setWordWrap(True)
        self.history_summary.setObjectName("CheckDetail")
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
        position: tuple[int, int] | None = None,
        locked: bool = False,
    ) -> None:
        self._task = task
        self._active_seconds = active_seconds
        self.set_locked(locked)

        self.title.setText(task.title)
        self.level_badge.setText(task.level)
        self.topic_label.setText(topic)
        self.statement.setHtml(self._wrap_html(self._with_source(task)))
        self.meta_label.setText(self._meta_text(task, position))
        self._refresh_xp(xp_preview, hints_used)
        self.show_planned_checks(task)
        self._select_sheet(cheatsheets.pick(task))
        self._build_hints(task, hints_used)
        self._refresh_lock_state()
        self.reset_review()
        self.tabs.setCurrentIndex(TAB_STATEMENT)

    def show_placeholder(self, title: str, message: str, *,
                         task_id: str | None = None, manual_done: bool = False) -> None:
        """A plan item done outside the trainer (venv, Git, pytest)."""
        self._task = None
        self.set_locked(False)
        self._hint_widgets.clear()
        self.title.setText(title)
        self.level_badge.setText(self.tr("Виконано поза тренажером") if manual_done else self.tr("План"))
        self.topic_label.setText("")
        self.meta_label.setText("")
        self.xp_label.setText(
            self.tr("Цей пункт не перевіряється тестами: зроби його у своєму терміналі "
                    "й познач галочкою.") if task_id else ""
        )
        self.statement.setHtml(self._wrap_html(f"<p>{html.escape(message)}</p>"))
        self.show_planned_checks(None)
        self._select_sheet(cheatsheets.pick_text(title))
        self.history_summary.setText(self.tr("Історії ще немає"))
        self.history_list.clear()
        self._clear_hints()

        if task_id:
            self._build_manual_block(task_id, manual_done)
        self.reset_review()
        self.tabs.setCurrentIndex(TAB_STATEMENT)

    @staticmethod
    def _drop_widget(widget: QWidget) -> None:
        """Removes the widget immediately.

        deleteLater() alone only queues it: until the next event-loop round
        the old block would stay painted over the new one. So first unparent,
        and only then destroy.
        """
        widget.setParent(None)
        widget.deleteLater()

    def _clear_hints(self) -> None:
        self.hints_view.clear_hints()

    def _build_manual_block(self, task_id: str, done: bool) -> None:
        self.hints_view.build_manual_block(task_id, done)

    def set_history(self, rows, *, solved: bool, best_xp: int, hints_used: int,
                    active_seconds: float) -> None:
        self.history_view.set_history(
            rows, solved=solved, best_xp=best_xp, hints_used=hints_used,
            active_seconds=active_seconds,
        )

    @property
    def locked(self) -> bool:
        """Whether this is a cold review (hints and solution off)."""
        return self.hints_view.locked

    def set_locked(self, locked: bool) -> None:
        """Switches cold review on/off in the hints panel."""
        self.hints_view.set_locked(locked)

    def update_xp_preview(self, xp: int, hints_used: int) -> None:
        """Shows how much XP the task grants given the opened hints."""
        self.hints_view.update_xp_preview(xp, hints_used)

    def tick(self, active_seconds: float) -> None:
        """Refreshes the active-work counter (called by the main-window timer)."""
        self.hints_view.tick(active_seconds)

    # ---------- checks ----------

    # ---------- the "Тести" tab (meat lives in ui/test_results.py) ----------

    def _clear_checks(self) -> None:
        self.results.clear_checks()

    def _add_card(self, widget: QWidget, box: QVBoxLayout | None = None) -> None:
        self.results.add_card(widget, box)

    def _check_card(self, **kwargs) -> QFrame:
        """One card: state icon, check name and explanation."""
        return self.results.check_card(**kwargs)

    @staticmethod
    def _check_kind(check: Check) -> str:
        return TestResults.check_kind(check)

    def show_planned_checks(self, task: Task | None) -> None:
        """Shows the check list **before** the run: what exactly they will demand."""
        self.results.show_planned_checks(task)

    def reset_tests(self) -> None:
        self.results.reset_tests()

    def show_result(self, result: RunResult, with_checks: bool) -> None:
        self.results.show_result(result, with_checks)

    def _show_advice(self, result: RunResult, passed: int, total: int) -> None:
        """Explains the error in human language and hints the next step."""
        self.results.show_advice(result, passed, total)

    def _add_jump_button(self, result: RunResult) -> None:
        """A "jump to line N" button — the fastest path from error to code."""
        self.results.add_jump_button(result)

    @property
    def jump_line(self) -> int:
        """Line jumpable to after the last run (0 — none)."""
        return self.results.jump_line

    # ---------- code review ----------

    def show_review(self, review: CodeReview) -> None:
        """Shows the code review: remarks with line numbers and one praise."""
        self.review_view.show_review(review)

    def reset_review(self) -> None:
        """Forgets the previous review: for a new task it would be a lie."""
        self.review_view.reset_review()

    @property
    def review_cards(self) -> list[QFrame]:
        """Review cards — so tests can count them."""
        return self.review_view.review_cards

    def _clear_review(self) -> None:
        self.review_view.clear_review()

    def _review_card(self, remark: Remark) -> QFrame:
        return self.review_view.review_card(remark)

    def _line_button(self, line: int) -> QWidget | None:
        """A "jump to line" button — from the remark straight into code."""
        return self.review_view.line_button(line)

    # ---------- reference ----------

    def _select_sheet(self, sheet: cheatsheets.CheatSheet) -> None:
        """Shows the right cheatsheet without yanking the human's choice."""
        index = self._sheets.index(sheet) if sheet in self._sheets else 0
        if self.sheet_picker.currentIndex() != index:
            self.sheet_picker.blockSignals(True)
            self.sheet_picker.setCurrentIndex(index)
            self.sheet_picker.blockSignals(False)
        self._render_sheet(index)

    def _render_sheet(self, index: int) -> None:
        if not (0 <= index < len(self._sheets)):
            return
        sheet = self._sheets[index]
        # compact: in a narrow panel spare font size = spare line wraps
        self.sheet_view.setHtml(
            self._wrap_html(plain_to_html(sheet.body), compact=True)
        )

    # ---------- hints ----------

    def _build_hints(self, task: Task, hints_used: int) -> None:
        self.hints_view.build_hints(task, hints_used)

    def _hint_block(self, index: int, hint: Hint, hints_used: int) -> tuple[QWidget, dict]:
        return self.hints_view.hint_block(index, hint, hints_used)

    def _refresh_lock_state(self) -> None:
        self.hints_view.refresh_lock_state()

    def _lock_everything(self) -> None:
        """Cold review: no hint opens, neither does the solution."""
        self.hints_view.lock_everything()

    def _refresh_xp(self, xp_preview: int | None, hints_used: int) -> None:
        self.hints_view.refresh_xp(xp_preview, hints_used)

    # ---------- service ----------

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        """After an objectName change Qt never repaints the style itself — ask explicitly."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    @staticmethod
    def _meta_text(task: Task, position: tuple[int, int] | None) -> str:
        tr = lambda s: QCoreApplication.translate("TaskPanel", s)
        parts = []
        if position:
            parts.append(tr("Задача {a} із {b}").format(a=position[0], b=position[1]))
        parts.append(tr("≈{n} хв роботи").format(n=task.minutes))
        if task.has_files:
            parts.append(tr("проєкт із кількох файлів"))
        if task.stdin:
            parts.append(tr("є ввід"))
        return " · ".join(parts)

    @staticmethod
    def _with_source(task: Task) -> str:
        """Appends where the task comes from (respect to the authors)."""
        if not task.has_source:
            return task.statement
        credit = html.escape(task.source)
        if task.source_url:
            credit = (
                f'<a href="{html.escape(task.source_url, quote=True)}">'
                f"{credit}</a>"
            )
        return (
            task.statement
            + f'<p style="color: {Colors.muted}; font-size: {ui_size(11)}px;">'
              + QCoreApplication.translate(
                  "TaskPanel",
                  "Джерело задачі: {credit}. Умова переказана українською, "
                  "перевірки — власні.").format(credit=credit) + "</p>"
        )

    def _wrap_html(self, body: str, *, compact: bool = False) -> str:
        """Shared "stylesheet" for statements, hints and reference.

        Prose and code in different fonts: the eye must tell explanation
        from what to type into the editor at first glance.

        compact=True — slightly smaller text: the reference needs it, where
        as much code as possible must fit the narrow panel without wraps.
        """
        prose = prose_family()
        mono = mono_family()
        prose_px = ui_size(13 if compact else 14)
        code_px = ui_size(12 if compact else 13)
        pad = "8px 10px" if compact else "10px 12px"
        return f"""
        <style>
            /* line-height in Qt is percent-based: 120% of 14px gives ~21px
               per line — a comfortable 1.5, more already looks sparse */
            body {{ color: {Colors.text}; font-family: '{prose}';
                    font-size: {prose_px}px; line-height: 120%; }}
            p {{ margin: 8px 0; }}
            h3 {{ color: {Colors.accent}; font-size: {prose_px + 1}px;
                  font-weight: 700; margin: 15px 0 6px 0; }}
            h4 {{ color: {Colors.accent}; font-size: {prose_px - 2}px;
                  font-weight: 700; letter-spacing: 1px;
                  margin: 16px 0 6px 0; }}
            b {{ color: {Colors.strong}; }}
            i {{ color: {Colors.muted}; }}
            code {{ font-family: '{mono}'; font-size: {code_px}px;
                    background-color: {Colors.editor_bg};
                    color: {Colors.syn_string}; padding: 1px 5px; }}
            /* code lines sit denser than prose — like in the editor */
            pre {{ font-family: '{mono}'; font-size: {code_px}px;
                   background-color: {Colors.editor_bg}; color: {Colors.text};
                   padding: {pad}; border: 1px solid {Colors.border};
                   white-space: pre-wrap; line-height: 100%; }}
            ol, ul {{ margin: 6px 0 6px 20px; }}
            li {{ margin: 5px 0; }}
            a {{ color: {Colors.accent}; }}
            .warn {{ color: {Colors.warn}; }}
        </style>
        <body>{body}</body>
        """
