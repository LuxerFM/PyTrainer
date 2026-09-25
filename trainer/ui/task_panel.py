"""Права панель: умова задачі, перевірки, довідка, підказки та історія.

Тут живе «інформаційний шар» тренажера — усе, що людина має бачити поруч із
редактором:

* **Задача** — умова гарним текстом (окремий шрифт для прози й для коду);
* **Тести** — що саме перевірять *до* запуску і що з цього вийшло *після*,
  плюс людське пояснення помилки замість англійського traceback;
* **Довідка** — міні-шпаргалка, підібрана під тему задачі;
* **Підказки** — підказки за таймером активної роботи (ШІ як вчитель, а не автор);
* **Історія** — усі запуски й здавання цієї задачі.

Розв'язок заблоковано, поки не набіжить достатньо часу активної роботи над
задачею. Це прямо реалізує правило з роадмапу: ШІ — вчитель, а не автор коду.
"""

from __future__ import annotations

import html
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from curriculum import cheatsheets
from curriculum.schema import Check, Hint, Task

from ..core.runner import RunResult
from .theme import Colors, mono_family, prose_family, ui_size

# Індекси вкладок — щоб жодне число не «загубилось» у коді вікна.
TAB_STATEMENT = 0
TAB_TESTS = 1
TAB_CHEATSHEET = 2
TAB_HINTS = 3
TAB_HISTORY = 4


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


# --------------------------------------------------------------------------
# Текст підказок приходить звичайним текстом, а показати його треба гарно:
# проза — звичайним шрифтом, а рядки-код — моноширинним у рамці.
# --------------------------------------------------------------------------

_CODE_START = (
    "def ", "class ", "for ", "while ", "if ", "elif ", "else:", "return ",
    "import ", "from ", "print(", "with ", "try:", "except ", "finally:",
    "assert ", "raise ", "@", "#", ">>>",
)
_ASSIGN_RE = re.compile(r"^[A-Za-z_][\w\.\[\]'\"]*\s*[-+*/]?=[^=]")


def _looks_like_code(line: str) -> bool:
    """Евристика: рядок схожий на код, а не на речення українською."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(_CODE_START):
        return True
    return bool(_ASSIGN_RE.match(stripped))


def plain_to_html(text: str) -> str:
    """Перетворює звичайний текст у HTML, виділяючи блоки коду.

    Підказки пише людина (я) простим текстом — і саме так їх легко правити.
    А показувати треба так, щоб код не зливався з поясненням. Тому сусідні
    рядки-код збираються в один `<pre>`, а решта стає абзацами.
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
    """QTextBrowser, який сам підганяє висоту під свій вміст.

    Потрібен там, де блок має бути «як картка»: показує весь текст, не
    додаючи власної прокрутки всередині прокрутки.
    """

    _fitting = False   # атрибут рівня класу: resizeEvent може прийти раніше за __init__

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

    def setHtml(self, text: str) -> None:  # noqa: N802 — назва з Qt
        super().setHtml(text)
        self._fit()

    def resizeEvent(self, event) -> None:  # noqa: N802 — назва з Qt
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
    """Показує умову, результати перевірки, довідку, підказки та історію."""

    hint_revealed = Signal(int, bool)       # (рівень підказки, чи це повний розв'язок)
    solution_use_requested = Signal(str)    # людина хоче вставити розв'язок у редактор
    manual_toggle_requested = Signal(str)   # пункт, зроблений поза тренажером
    jump_to_line_requested = Signal(int)    # поставити курсор на рядок з помилкою

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setMinimumWidth(360)

        self._task: Task | None = None
        self._hint_widgets: list[dict] = []
        self._check_cards: list[QFrame] = []
        self._active_seconds = 0.0
        self._sheets = cheatsheets.all_sheets()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_statement_tab(), "Задача")
        self.tabs.addTab(self._build_tests_tab(), "Тести")
        self.tabs.addTab(self._build_cheatsheet_tab(), "Довідка")
        self.tabs.addTab(self._build_hints_tab(), "Підказки")
        self.tabs.addTab(self._build_history_tab(), "Історія")
        layout.addWidget(self.tabs, 1)

    # ---------- верхівка ----------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        box = QVBoxLayout(header)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(7)

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
        self.topic_label.setWordWrap(True)   # довга тема має переноситись, а не різатись
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

    # ---------- вкладки ----------

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

        self.tests_summary = QLabel("Ще не перевірялося")
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

    def _build_cheatsheet_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(9)

        self.sheet_note = QLabel(
            "Міні-довідка з теми задачі. Можна вибрати будь-яку іншу — "
            "це не впливає на XP."
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
    ) -> None:
        self._task = task
        self._active_seconds = active_seconds

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
        self.tabs.setCurrentIndex(TAB_STATEMENT)

    def show_placeholder(self, title: str, message: str, *,
                         task_id: str | None = None, manual_done: bool = False) -> None:
        """Пункт плану, який робиться поза тренажером (venv, Git, pytest)."""
        self._task = None
        self._hint_widgets.clear()
        self.title.setText(title)
        self.level_badge.setText("Виконано поза тренажером" if manual_done else "План")
        self.topic_label.setText("")
        self.meta_label.setText("")
        self.xp_label.setText(
            "Цей пункт не перевіряється тестами: зроби його у своєму терміналі "
            "й познач галочкою." if task_id else ""
        )
        self.statement.setHtml(self._wrap_html(f"<p>{html.escape(message)}</p>"))
        self.show_planned_checks(None)
        self._select_sheet(cheatsheets.pick_text(title))
        self.history_summary.setText("Історії ще немає")
        self.history_list.clear()
        self._clear_hints()

        if task_id:
            self._build_manual_block(task_id, manual_done)
        self.tabs.setCurrentIndex(TAB_STATEMENT)

    @staticmethod
    def _drop_widget(widget: QWidget) -> None:
        """Прибирає віджет негайно.

        Сам deleteLater() лише ставить його в чергу: до наступного кола циклу
        подій старий блок лишався б намальованим поверх нового. Тому спершу
        відв'язуємо від батька, і аж потім знищуємо.
        """
        widget.setParent(None)
        widget.deleteLater()

    def _clear_hints(self) -> None:
        while self.hints_box.count() > 1:
            item = self.hints_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self._drop_widget(widget)

    def _build_manual_block(self, task_id: str, done: bool) -> None:
        self._clear_hints()
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
            lambda _=False, task=task_id: self.manual_toggle_requested.emit(task)
        )
        box.addWidget(button)
        self.hints_box.insertWidget(self.hints_box.count() - 1, block)

    def set_history(self, rows, *, solved: bool, best_xp: int, hints_used: int,
                    active_seconds: float) -> None:
        self.history_list.clear()
        if not rows:
            self.history_summary.setText("Ще жодного запуску цієї задачі.")
            return

        self.history_summary.setText(
            f"Задача: {'здано ✓' if solved else 'ще не здана'} · "
            f"XP: {best_xp} · підказок відкрито: {hints_used} · "
            f"час над задачею: {_format_time(active_seconds)}"
        )
        for row in rows:
            when = row["created_at"][:16].replace("T", " ")
            if not row["with_checks"]:
                # звичайний запуск: не невдача, просто проба коду
                item = QListWidgetItem(f"{when} · ▸ запуск")
                item.setForeground(QColor(Colors.muted))
            else:
                mark = "✓" if row["ok"] else "✕"
                xp = f' · +{row["xp"]} XP' if row["xp"] else ""
                item = QListWidgetItem(f"{when} · {mark} перевірка{xp}")
                item.setForeground(
                    QColor(Colors.success if row["ok"] else Colors.error)
                )
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

    # ---------- перевірки ----------

    def _clear_checks(self) -> None:
        while self.checks_box.count() > 1:
            item = self.checks_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self._drop_widget(widget)
        self._check_cards.clear()

    def _add_card(self, widget: QWidget) -> None:
        self.checks_box.insertWidget(self.checks_box.count() - 1, widget)

    def _check_card(
        self,
        *,
        mark: str,
        name: str,
        detail: str = "",
        state: str = "pending",
        tooltip: str = "",
    ) -> QFrame:
        """Одна картка: значок стану, назва перевірки й пояснення."""
        card = QFrame()
        card.setObjectName("CheckCard")
        colours = {
            "ok": (Colors.success, Colors.border),
            "fail": (Colors.error, Colors.error),
            "pending": (Colors.muted, Colors.border),
            "info": (Colors.warn, Colors.warn),
        }
        mark_colour, border = colours.get(state, colours["pending"])
        card.setStyleSheet(
            f"QFrame#CheckCard {{ background-color: {Colors.elevated};"
            f" border: 1px solid {border}; border-radius: 8px; }}"
        )

        row = QHBoxLayout(card)
        row.setContentsMargins(11, 9, 11, 9)
        row.setSpacing(9)

        mark_label = QLabel(mark)
        mark_label.setObjectName("CheckMark")
        mark_label.setStyleSheet(f"color: {mark_colour};")
        mark_label.setFixedWidth(16)
        mark_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        row.addWidget(mark_label)

        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(3)

        name_label = QLabel(name)
        name_label.setObjectName("CheckName")
        name_label.setWordWrap(True)
        column.addWidget(name_label)

        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName(
                "CheckError" if state == "fail" else "CheckDetail"
            )
            detail_label.setWordWrap(True)
            detail_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            column.addWidget(detail_label)

        row.addLayout(column, 1)
        if tooltip:
            card.setToolTip(tooltip)
        return card

    @staticmethod
    def _check_kind(check: Check) -> str:
        return "перевірка виводу програми" if check.is_stdout else "перевірка коду"

    def show_planned_checks(self, task: Task | None) -> None:
        """Показує список перевірок **до** запуску: що саме вимагатимуть."""
        self._clear_checks()

        if task is None or not task.checks:
            self.tests_summary.setObjectName("VerdictWarn")
            self.tests_summary.setText("Це пункт поза тренажером")
            self.tests_detail.setText(
                "Тут немає прихованих тестів — результат оцінюєш ти сам."
            )
        else:
            total = len(task.checks)
            self.tests_summary.setObjectName("VerdictWarn")
            self.tests_summary.setText(
                f"Буде {total} " + (
                    "перевірка" if total == 1 else
                    "перевірки" if 2 <= total <= 4 else
                    "перевірок"
                ) + " — ще не запускались"
            )
            for check in task.checks:
                self._add_card(self._check_card(
                    mark="○",
                    name=check.name,
                    detail=self._check_kind(check),
                    state="pending",
                ))
            self.tests_detail.setText(
                "Перевірки приховані: ти бачиш, що саме вони вимагають, але не "
                "сам код тесту. Натисни «Перевірити» (F5), щоб прогнати їх."
            )

        self._repolish(self.tests_summary)

    def reset_tests(self) -> None:
        self.show_planned_checks(self._task)

    def show_result(self, result: RunResult, with_checks: bool) -> None:
        self._clear_checks()

        if with_checks and result.checks:
            passed = result.passed_count
            total = len(result.checks)

            for check in result.checks:
                detail = ""
                if check.ok:
                    detail = "пройдено"
                elif check.error:
                    detail = check.error
                if not check.ok and check.actual:
                    first_lines = "\n".join(check.actual.splitlines()[:4])
                    detail = f"{detail}\nНасправді вивела:\n{first_lines}" if detail \
                        else f"Насправді вивела:\n{first_lines}"
                self._add_card(self._check_card(
                    mark="✓" if check.ok else "✕",
                    name=check.name,
                    detail=detail.strip(),
                    state="ok" if check.ok else "fail",
                    tooltip=check.error,
                ))

            if result.all_passed:
                self.tests_summary.setObjectName("VerdictOk")
                self.tests_summary.setText(
                    f"Усі перевірки пройдено: {passed} із {total} ✓"
                )
            else:
                self.tests_summary.setObjectName("VerdictBad")
                self.tests_summary.setText(
                    f"Пройдено {passed} із {total} — є що виправити"
                )

            self._show_advice(result, passed, total)
        elif result.timed_out:
            self.tests_summary.setObjectName("VerdictWarn")
            self.tests_summary.setText("Код зупинено за таймаутом")
            self._show_advice(result, 0, 0)
        elif result.stderr:
            self.tests_summary.setObjectName("VerdictBad")
            self.tests_summary.setText("Код впав з помилкою")
            self._show_advice(result, 0, 0)
        else:
            self.tests_summary.setObjectName("VerdictOk")
            self.tests_summary.setText("Код виконано без помилок")
            self.tests_detail.setText(
                "Це був звичайний запуск. Натисни «Перевірити» (F5), щоб "
                "прогнати приховані тести."
            )

        self._repolish(self.tests_summary)
        self.tabs.setCurrentIndex(TAB_TESTS)

    def _show_advice(self, result: RunResult, passed: int, total: int) -> None:
        """Пояснює помилку людською мовою й підказує наступний крок."""
        advice = result.advice
        self._add_jump_button(result)
        if not advice:
            if result.all_passed:
                self.tests_detail.setText(
                    "Так тримати! Наступна задача — у списку зліва (Ctrl+N)."
                )
            else:
                first_error = result.first_error
                self.tests_detail.setText(
                    f"Перша проблема: {first_error}" if first_error
                    else "Подивись, яка саме перевірка впала, вище."
                )
            return

        kind = advice.splitlines()[0]
        self._add_card(self._check_card(
            mark="?",
            name="Що це означає",
            detail=advice,
            state="info",
            tooltip=kind,
        ))
        self.tests_detail.setText(
            "Помилка — це підказка, а не вирок: Python каже, де саме код "
            "розійшовся з твоїм задумом."
        )

    def _add_jump_button(self, result: RunResult) -> None:
        """Кнопка «перейти до рядка N» — найшвидший шлях від помилки до коду.

        Номер рядка вже знає пояснювач помилок; лишається дати людині
        кнопку, щоб не шукати його очима в редакторі.
        """
        line = result.failed_line
        if not line:
            self._jump_line = 0
            return
        self._jump_line = line
        button = QPushButton(f"↪  Перейти до рядка {line}")
        button.setObjectName("Ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda _=False, number=line: self.jump_to_line_requested.emit(number)
        )
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(button)
        row.addStretch(1)
        self._add_card(holder)

    @property
    def jump_line(self) -> int:
        """Рядок, на який можна перейти після останнього прогону (0 — немає)."""
        return getattr(self, "_jump_line", 0)

    # ---------- довідка ----------

    def _select_sheet(self, sheet: cheatsheets.CheatSheet) -> None:
        """Показує потрібну шпаргалку, не смикаючи вибір людини без причини."""
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
        # compact: у вузькій панелі зайвий розмір шрифту = зайві переноси рядків
        self.sheet_view.setHtml(
            self._wrap_html(plain_to_html(sheet.body), compact=True)
        )

    # ---------- підказки ----------

    def _build_hints(self, task: Task, hints_used: int) -> None:
        self._clear_hints()
        self._hint_widgets.clear()

        hints = list(task.clue_hints) + ([task.solution_hint] if task.solution_hint else [])
        for index, hint in enumerate(hints, start=1):
            block, widgets = self._hint_block(index, hint, hints_used)
            self._hint_widgets.append(widgets)
            self.hints_box.insertWidget(self.hints_box.count() - 1, block)

    def _hint_block(self, index: int, hint: Hint, hints_used: int) -> tuple[QWidget, dict]:
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

        text = AutoHeightText(self._wrap_html(plain_to_html(hint.text)))
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
            lambda _=False, h=hint: self.solution_use_requested.emit(h.text)
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
                    f"Відкриється через {_format_time(left)} активної роботи над "
                    f"задачею (з {self._task.minutes} хв). Працювало: "
                    f"{_format_time(self._active_seconds)}."
                )

    def _refresh_xp(self, xp_preview: int | None, hints_used: int) -> None:
        if self._task is None:
            self.xp_label.setText("")
            return
        parts = []
        if xp_preview is not None:
            parts.append(f"Здаси зараз — отримаєш {xp_preview} XP")
        # базу показуємо лише тоді, коли вона відрізняється від поточної —
        # інакше рядок просто повторює сам себе
        if xp_preview is None or xp_preview != self._task.base_xp:
            parts.append(f"база {self._task.base_xp} XP")
        if hints_used:
            parts.append(f"підказок відкрито: {hints_used}")
        self.xp_label.setText(" · ".join(parts))

    # ---------- службове ----------

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        """Після зміни objectName Qt сам стиль не перемальовує — просимо явно."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    @staticmethod
    def _meta_text(task: Task, position: tuple[int, int] | None) -> str:
        parts = []
        if position:
            parts.append(f"Задача {position[0]} із {position[1]}")
        parts.append(f"≈{task.minutes} хв роботи")
        if task.has_files:
            parts.append("проєкт із кількох файлів")
        if task.stdin:
            parts.append("є ввід")
        return " · ".join(parts)

    @staticmethod
    def _with_source(task: Task) -> str:
        """Дописує в кінець умови, звідки задача (повага до авторів)."""
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
              f"Джерело задачі: {credit}. Умова переказана українською, "
              "перевірки — власні.</p>"
        )

    def _wrap_html(self, body: str, *, compact: bool = False) -> str:
        """Спільний «аркуш стилів» для умов, підказок і довідки.

        Проза й код — різними шрифтами: око має з першого погляду відрізняти
        пояснення від того, що треба набрати в редакторі.

        compact=True — трохи дрібніший текст: він потрібен довідці, де в
        вузьку панель має влізти якомога більше коду без переносів.
        """
        prose = prose_family()
        mono = mono_family()
        prose_px = ui_size(13 if compact else 14)
        code_px = ui_size(12 if compact else 13)
        pad = "8px 10px" if compact else "10px 12px"
        return f"""
        <style>
            /* line-height у Qt задається у відсотках: 120% від 14px дає ~21px
               на рядок — це комфортні 1.5, більше вже виглядає розріджено */
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
            /* у коді рядки стоять щільніше, ніж у прозі — як у редакторі */
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
