"""Права панель: умова задачі, перевірки, довідка, підказки та історія.

Тут живе «інформаційний шар» тренажера — усе, що людина має бачити поруч із
редактором:

* **Задача** — умова гарним текстом (окремий шрифт для прози й для коду);
* **Тести** — що саме перевірять *до* запуску і що з цього вийшло *після*,
  плюс людське пояснення помилки замість англійського traceback;
* **Рев'ю** — розбір самого коду: що в ньому не так і як зробити краще;
* **Довідка** — міні-шпаргалка, підібрана під тему задачі;
* **Підказки** — підказки за таймером активної роботи (ШІ як вчитель, а не автор);
* **Історія** — усі запуски й здавання цієї задачі.

Розв'язок заблоковано, поки не набіжить достатньо часу активної роботи над
задачею. Це прямо реалізує правило з роадмапу: ШІ — вчитель, а не автор коду.

Окремий випадок — холодне повторення (вже здана задача): там підказки й
розв'язок недоступні зовсім, бо вся вправа в тому, щоб дістати рішення
з пам'яті, а не впізнати власний код.
"""

from __future__ import annotations

import html
import re

from PySide6.QtCore import Qt, Signal
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

# Індекси вкладок — щоб жодне число не «загубилось» у коді вікна.
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
    review_requested = Signal()             # «розбери мій код» (вкладка «Рев'ю»)

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
        self.tabs.addTab(self._build_statement_tab(), "Задача")
        self.tabs.addTab(self._build_tests_tab(), "Тести")
        self.tabs.addTab(self._build_review_tab(), "Рев'ю")
        self.tabs.addTab(self._build_cheatsheet_tab(), "Довідка")
        self.tabs.addTab(self._build_hints_tab(), "Підказки")
        self.tabs.addTab(self._build_history_tab(), "Історія")
        layout.addWidget(self.tabs, 1)

        self.results = TestResults(self)
        self.review_view = ReviewView(self)
        self.hints_view = HintsView(self)
        self.history_view = HistoryView(self)

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

    def _build_review_tab(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(9)

        self.review_summary = QLabel(NOT_REVIEWED)
        self.review_summary.setObjectName("Subtle")
        self.review_summary.setWordWrap(True)
        box.addWidget(self.review_summary)

        self.review_button = QPushButton("Розібрати код")
        self.review_button.setObjectName("Ghost")
        self.review_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.review_button.setToolTip(
            "Розбір не оцінює і не перевіряє: він каже, що в коді буде важко "
            "читати іншій людині — і як це виправити (F6)"
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
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 12, 14, 0)
        outer.setSpacing(8)

        # Пояснення холодного повторення живе поза списком підказок: список
        # перебудовується на кожну задачу, а цей напис має лишатись на місці.
        self.cold_note = QLabel(
            "Холодне повторення: підказки й розв'язок недоступні, доки не "
            "завершиш спробу. Саме в цьому суть — згадати самому."
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
        """Пункт плану, який робиться поза тренажером (venv, Git, pytest)."""
        self._task = None
        self.set_locked(False)
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
        self.reset_review()
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
        """Чи це холодне повторення (підказки й розв'язок вимкнено)."""
        return self.hints_view.locked

    def set_locked(self, locked: bool) -> None:
        """Вмикає/вимикає холодне повторення в панелі підказок."""
        self.hints_view.set_locked(locked)

    def update_xp_preview(self, xp: int, hints_used: int) -> None:
        """Показує, скільки XP дасть задача з урахуванням відкритих підказок."""
        self.hints_view.update_xp_preview(xp, hints_used)

    def tick(self, active_seconds: float) -> None:
        """Оновлює лічильник активної роботи (викликає таймер головного вікна)."""
        self.hints_view.tick(active_seconds)

    # ---------- перевірки ----------

    # ---------- вкладка «Тести» (м'ясо — в ui/test_results.py) ----------

    def _clear_checks(self) -> None:
        self.results.clear_checks()

    def _add_card(self, widget: QWidget, box: QVBoxLayout | None = None) -> None:
        self.results.add_card(widget, box)

    def _check_card(self, **kwargs) -> QFrame:
        """Одна картка: значок стану, назва перевірки й пояснення."""
        return self.results.check_card(**kwargs)

    @staticmethod
    def _check_kind(check: Check) -> str:
        return TestResults.check_kind(check)

    def show_planned_checks(self, task: Task | None) -> None:
        """Показує список перевірок **до** запуску: що саме вимагатимуть."""
        self.results.show_planned_checks(task)

    def reset_tests(self) -> None:
        self.results.reset_tests()

    def show_result(self, result: RunResult, with_checks: bool) -> None:
        self.results.show_result(result, with_checks)

    def _show_advice(self, result: RunResult, passed: int, total: int) -> None:
        """Пояснює помилку людською мовою й підказує наступний крок."""
        self.results.show_advice(result, passed, total)

    def _add_jump_button(self, result: RunResult) -> None:
        """Кнопка «перейти до рядка N» — найшвидший шлях від помилки до коду."""
        self.results.add_jump_button(result)

    @property
    def jump_line(self) -> int:
        """Рядок, на який можна перейти після останнього прогону (0 — немає)."""
        return self.results.jump_line

    # ---------- розбір коду ----------

    def show_review(self, review: CodeReview) -> None:
        """Показує розбір коду: зауваження з номерами рядків і одну похвалу."""
        self.review_view.show_review(review)

    def reset_review(self) -> None:
        """Забуває попередній розбір: для нової задачі він був би брехнею."""
        self.review_view.reset_review()

    @property
    def review_cards(self) -> list[QFrame]:
        """Картки розбору — щоб тести могли їх порахувати."""
        return self.review_view.review_cards

    def _clear_review(self) -> None:
        self.review_view.clear_review()

    def _review_card(self, remark: Remark) -> QFrame:
        return self.review_view.review_card(remark)

    def _line_button(self, line: int) -> QWidget | None:
        """Кнопка «перейти до рядка» — з зауваження одразу в код."""
        return self.review_view.line_button(line)

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
        self.hints_view.build_hints(task, hints_used)

    def _hint_block(self, index: int, hint: Hint, hints_used: int) -> tuple[QWidget, dict]:
        return self.hints_view.hint_block(index, hint, hints_used)

    def _refresh_lock_state(self) -> None:
        self.hints_view.refresh_lock_state()

    def _lock_everything(self) -> None:
        """Холодне повторення: жодна підказка не відкривається, розв'язок теж."""
        self.hints_view.lock_everything()

    def _refresh_xp(self, xp_preview: int | None, hints_used: int) -> None:
        self.hints_view.refresh_xp(xp_preview, hints_used)

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
