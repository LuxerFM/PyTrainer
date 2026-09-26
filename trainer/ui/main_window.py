"""Головне вікно тренажера — тут зустрічаються всі частини застосунку.

Розділення відповідальності:

    curriculum/       що вчити (дані: місяці, теми, задачі, перевірки)
    trainer/core/     як перевіряти й що пам'ятати (runner, db, scoring, session)
    trainer/ui/       як це показати (це вікно)

Тому вікно не містить жодного правила навчання: воно питає `StudySession`,
що сталося після спроби, і малює результат.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QKeySequence,
    QShortcut,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from curriculum import CURRICULUM, find_task, first_unfinished, study_tasks, topic_of

from ..core import scoring
from ..core.codereview import (
    STARTER_REVIEW,
    CodeReview,
    issues_phrase,
    names_used_in,
    review_code,
)
from ..core.db import Database
from ..core.digest import WeeklyDigest
from ..core.review import cold_seconds, pick_cold_task
from ..core.runner import RunResult
from ..core.session import StudySession, StudyUpdate
from ..paths import app_folder
from .dialogs import Dialogs
from .digest_page import DigestDialog
from .editor import CodeEditor
from .file_sync import FileSync
from .refresh_view import RefreshView
from .run_flow import RunFlow
from .sidebar import SideNav
from .task_panel import TAB_HINTS, TAB_REVIEW, TaskPanel
from .theme import (MONO_FONTS, Colors, apply_theme, pick_font, scale, set_scale)

ROOT = app_folder()
ROADMAP_PATH = ROOT / "Python-Roadmap.md"
PROGRESS_PATH = ROOT / "progress.json"
SETTINGS_PATH = ROOT / "pytrainer.ini"
TICK_SECONDS = 5


class MainWindow(QMainWindow):
    """Головне вікно."""

    run_finished = Signal(object)

    def __init__(self, db: Database | None = None,
                 roadmap_path: str | Path = ROADMAP_PATH,
                 progress_path: str | Path = PROGRESS_PATH,
                 settings_path: str | Path | None = SETTINGS_PATH) -> None:
        super().__init__()
        from ..core.crashlog import version_line

        self.setWindowTitle(f"{version_line()} — тренажер Python")
        self.resize(1480, 920)
        self.setMinimumSize(1120, 700)

        self.db = db or Database()
        self.session = StudySession(self.db)
        self.roadmap_path = Path(roadmap_path)
        self.progress_path = Path(progress_path)
        self.settings = (
            QSettings(str(settings_path), QSettings.Format.IniFormat)
            if settings_path else None
        )

        self._task = None
        self._running = False
        self._review_mode = False
        self._cold_left = 0.0
        self._cold_warned = False
        self._last_saved = ""
        self._restored = False
        self._digest: WeeklyDigest | None = None
        self.digest_dialog: DigestDialog | None = None

        self.sidebar = SideNav()
        self.editor = CodeEditor()
        self.panel = TaskPanel()
        self.console = self._build_console()

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self.files = FileSync(self)
        self.flow = RunFlow(self)
        self.views = RefreshView(self)
        self.dialogs = Dialogs(self)
        self._connect()

        self.sidebar.load_curriculum(CURRICULUM, self.db.statuses())
        self._refresh_all()

        start = first_unfinished(self.db.statuses()) or study_tasks()[0]
        self.open_task(start.id)
        self._restore_state()

        self.timer = QTimer(self)
        self.timer.setInterval(TICK_SECONDS * 1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ==================================================================
    # інтерфейс
    # ==================================================================

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        self._add_action(file_menu, "Зберегти код…", "Ctrl+S", self.save_code_as)
        self._add_action(file_menu, "Скинути код до заготовки", None, self.reset_code)
        file_menu.addSeparator()
        self._add_action(file_menu, "Експортувати розв'язані задачі…", None,
                         self.export_solutions)
        self._add_action(file_menu, "Експортувати прогрес…", None, self.export_progress)
        self._add_action(file_menu, "Імпортувати прогрес…", None, self.import_progress)
        self._add_action(file_menu, "Відновити з копії…", None,
                         self.restore_from_backup)
        self._add_action(file_menu, "Відкрити теку з даними", None,
                         self.open_data_folder)
        self._add_action(file_menu, "Відкрити файл журналу", None,
                         self.open_log_file)
        file_menu.addSeparator()
        self._add_action(file_menu, "Оновити Python-Roadmap.md", None,
                         lambda: self.rewrite_roadmap(force=True))
        file_menu.addSeparator()
        self._add_action(file_menu, "Вихід", "Ctrl+Q", self.close)

        run_menu = self.menuBar().addMenu("Запуск")
        self._add_action(run_menu, "Запустити", "Ctrl+Return", self.run_code_only)
        self._add_action(run_menu, "Перевірити тестами", "F5", self.run_checks)
        self._add_action(run_menu, "Розібрати мій код (рев'ю)", "F6",
                         self.review_current_code)
        self._add_action(run_menu, "Очистити консоль", None, self.console.clear)

        study_menu = self.menuBar().addMenu("Навчання")
        self._add_action(study_menu, "План на сьогодні", "Ctrl+L",
                         lambda: self.sidebar.set_mode(3))
        self._add_action(study_menu, "На повторення", "Ctrl+R", lambda: self.sidebar.set_mode(1))
        self._add_action(study_menu, "Холодне повторення (випадкова задача)",
                         "Ctrl+Shift+R", self.start_cold_review)
        self._add_action(study_menu, "Прогрес і слабкі місця", "Ctrl+P",
                         lambda: self.sidebar.set_mode(2))
        self._add_action(study_menu, "Тижневий огляд", "Ctrl+Shift+W",
                         self.show_digest)
        self._add_action(study_menu, "Наступна незавершена задача", "Ctrl+N",
                         self.open_next_task)
        self._add_action(study_menu, "Знайти задачу", "Ctrl+F", self.focus_search)
        study_menu.addSeparator()
        self._add_action(study_menu, "Позначити виконаним (зроблено поза тренажером)",
                         None, self.toggle_manual_done)
        study_menu.addSeparator()
        self._add_action(study_menu, "Скинути прогрес цієї задачі", None,
                         self.reset_task_progress)

        view_menu = self.menuBar().addMenu("Вигляд")
        self._add_action(view_menu, "Темна / світла тема", "Ctrl+D", self.toggle_theme)
        view_menu.addSeparator()
        self._add_action(view_menu, "Більший шрифт", "Ctrl++",
                         lambda: self.change_font_scale(0.05))
        self._add_action(view_menu, "Менший шрифт", "Ctrl+-",
                         lambda: self.change_font_scale(-0.05))
        self._add_action(view_menu, "Звичайний розмір шрифту", "Ctrl+0",
                         self.reset_font_scale)

        help_menu = self.menuBar().addMenu("Довідка")
        self._add_action(help_menu, "Гарячі клавіші", "F1", self.show_shortcuts)
        self._add_action(help_menu, "Про тренажер", None, self.show_about)

    def _add_action(self, menu, text: str, shortcut: str | None, slot) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _build_toolbar(self) -> None:
        bar = QToolBar()
        bar.setMovable(False)
        self.addToolBar(bar)

        self.btn_run = QToolButton()
        self.btn_run.setObjectName("Primary")
        self.btn_run.setText("▶  Запустити")
        self.btn_run.clicked.connect(self.run_code_only)

        self.btn_check = QToolButton()
        self.btn_check.setText("✓  Перевірити")
        self.btn_check.clicked.connect(self.run_checks)

        self.btn_hint = QToolButton()
        self.btn_hint.setText("Підказка")
        self.btn_hint.clicked.connect(self.open_hints_tab)

        self.btn_reset = QToolButton()
        self.btn_reset.setText("↺  Скинути")
        self.btn_reset.clicked.connect(self.reset_code)

        for button in (self.btn_run, self.btn_check, self.btn_hint, self.btn_reset):
            bar.addWidget(button)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred,
        )
        bar.addWidget(spacer)

        self.today_badge = QLabel("Сьогодні: 0 запусків")
        self.today_badge.setObjectName("Badge")
        self.review_badge = QLabel("На повторення: 0")
        self.review_badge.setObjectName("Badge")
        self.xp_badge = QLabel("XP 0")
        self.xp_badge.setObjectName("BadgeAccent")
        self.streak_badge = QLabel("Серія: 0 дн.")
        self.streak_badge.setObjectName("Badge")
        for badge in (self.today_badge, self.review_badge, self.xp_badge,
                      self.streak_badge):
            bar.addWidget(badge)

    def _build_body(self) -> None:
        center = QWidget()
        box = QVBoxLayout(center)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self._editor_header())

        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.setObjectName("editorSplitter")
        vertical.addWidget(self.editor)
        vertical.addWidget(self._console_box())
        vertical.setSizes([600, 250])
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 1)
        box.addWidget(vertical, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.addWidget(self.sidebar)
        splitter.addWidget(center)
        splitter.addWidget(self.panel)
        splitter.setSizes([300, 760, 400])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        self.setCentralWidget(splitter)

        self.editor_splitter = vertical
        self.main_splitter = splitter

    def _editor_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        box = QHBoxLayout(header)
        box.setContentsMargins(16, 10, 16, 10)
        box.setSpacing(10)

        self.file_label = QLabel("solution.py")
        self.file_label.setStyleSheet("font-weight: 700;")
        box.addWidget(self.file_label)

        hint = QLabel("Ctrl+Enter — запустити · F5 — перевірити тестами")
        hint.setObjectName("Subtle")
        box.addWidget(hint)
        box.addStretch(1)

        self.stdin_label = QLabel("")
        self.stdin_label.setObjectName("Subtle")
        box.addWidget(self.stdin_label)
        return header

    def _build_console(self) -> QTextEdit:
        console = QTextEdit()
        console.setObjectName("Console")
        console.setReadOnly(True)
        console.setFont(pick_font(MONO_FONTS, 10))
        console.setPlaceholderText("Тут з'явиться вивід твоєї програми…")
        return console

    def _console_box(self) -> QWidget:
        holder = QWidget()
        box = QVBoxLayout(holder)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        header = QWidget()
        header.setObjectName("Header")
        row = QHBoxLayout(header)
        row.setContentsMargins(16, 6, 10, 6)
        title = QLabel("КОНСОЛЬ")
        title.setObjectName("SectionTitle")
        row.addWidget(title)
        row.addStretch(1)
        clear = QPushButton("Очистити")
        clear.setObjectName("Ghost")
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self.console.clear)
        row.addWidget(clear)

        box.addWidget(header)
        box.addWidget(self.console, 1)
        return holder

    def _build_statusbar(self) -> None:
        self.status_msg = QLabel("Готово")
        self.statusBar().addWidget(self.status_msg, 1)
        self.timer_label = QLabel("")
        self.statusBar().addPermanentWidget(self.timer_label)
        self.position_label = QLabel("Рядок 1, стовпець 1")
        self.statusBar().addPermanentWidget(self.position_label)
        from platform import python_version, system

        self.statusBar().addPermanentWidget(QLabel(f"Python {python_version()} · {system()}"))

    def _connect(self) -> None:
        self.sidebar.task_selected.connect(self.open_task)
        self.sidebar.cold_review_requested.connect(self.start_cold_review)
        self.sidebar.stats.topic_practice_requested.connect(self.practice_topic)
        self.sidebar.digest_requested.connect(self.show_digest)
        self.panel.hint_revealed.connect(self._on_hint_revealed)
        self.panel.review_requested.connect(self.review_current_code)
        self.panel.solution_use_requested.connect(self._use_solution)
        self.panel.manual_toggle_requested.connect(self.toggle_manual_done)
        self.panel.jump_to_line_requested.connect(self.jump_to_line)
        self.editor.run_requested.connect(self.run_code_only)
        self.editor.cursorPositionChanged.connect(self._update_position)
        self.run_finished.connect(self._on_run_finished)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.run_code_only)

    # ==================================================================
    # робота з задачами
    # ==================================================================

    def open_task(self, task_id: str, review: bool = False) -> None:
        self._save_current_code()
        task = find_task(task_id)

        if task is None or task.stub:
            self._task = None
            self._review_mode = False
            self._cold_left = 0.0
            self.editor.setPlainText("")
            self.editor.setReadOnly(True)
            self._set_run_enabled(False)
            done = task is not None and self.db.status(task.id) == "done"
            self.panel.show_placeholder(
                task.title if task else task_id,
                "Цей пункт робиться не в тренажері, а у твоєму терміналі — "
                "саме там навичка й закріплюється. Зробив? Познач галочкою, "
                "щоб вона з'явилась і в Python-Roadmap.md."
                if task is not None else "Задачу не знайдено.",
                task_id=task.id if task is not None else None,
                manual_done=done,
            )
            self.status_msg.setText(
                "Пункт поза тренажером — познач галочкою, коли зробиш"
                if task is not None else "Задачу не знайдено"
            )
            return

        self._task = task
        self._review_mode = review
        self._cold_left = cold_seconds(task) if review else 0.0
        self._cold_warned = False
        self.btn_hint.setEnabled(not review)
        self.editor.setReadOnly(False)
        self._set_run_enabled(True)

        self.db.mark_in_progress(task.id)
        hints_used = self.db.hints_used(task.id)
        active = self.db.active_seconds(task.id)

        self.panel.show_task(
            task,
            topic=topic_of(task.id),
            hints_used=hints_used,
            active_seconds=active,
            xp_preview=self.session.preview_xp(task),
            position=self._task_position(task.id),
            locked=review,
        )
        self._load_history(task.id)

        saved = self.db.saved_code(task.id)
        # Холодне повторення починається із заготовки: показати свій же
        # розв'язок — це впізнавання, а не згадка. Збережений код у базі при
        # цьому не чіпається (див. _start_run і _tick).
        text = task.starter if review else (saved if saved else task.starter)
        self.editor.setPlainText(text)
        self._last_saved = text
        self.console.clear()
        if review:
            self._log(
                f"❄ Холодне повторення: {task.title}. Підказки й розв'язок "
                f"недоступні, час — до {cold_seconds(task) // 60} хв. "
                "Згадай сам — і тисни F5.",
                Colors.warn,
            )
        self._show_stdin_hint(task)
        self.file_label.setText(f"{task.id}.py")
        self.status_msg.setText(
            f'Повторення: {task.title}' if review else f'Відкрито: {task.title}'
        )
        self._update_timer_label()

    def open_next_task(self) -> None:
        statuses = self.db.statuses()
        for task in study_tasks():
            if statuses.get(task.id) != "done":
                self.open_task(task.id)
                self.sidebar.select(task.id)
                return
        self.status_msg.setText("Усі задачі, які вже написані, здані 🎉")

    # ==================================================================
    # холодне повторення
    # ==================================================================

    def start_cold_review(self) -> None:
        """Випадкова здана задача без підказок і розв'язку, з таймером.

        Навіщо окремий режим: відкрити свою ж здану задачу легко, а згадати її
        з нуля — ні. Тому редактор починається із заготовки, підказки й
        розв'язок вимкнено, а вердикт іде в ту саму чергу повторень.
        """
        choice = pick_cold_task(self.db, exclude=self._current_id())
        if choice is None:
            self.status_msg.setText(
                "Холодне повторення — для вже зданих задач. Здай якусь "
                "задачу (крім відкритої зараз) — і воно стане доступним."
            )
            return

        task = choice.task
        self.open_task(task.id, review=True)
        # Позначку в дереві показуємо, але сторінку не перемикаємо: якщо
        # холодне повторення почалось зі списку повторень, туди ж і хочеться
        # повернутись.
        self.sidebar.tree.select(task.id)
        source = "з черги повторень" if choice.from_queue \
            else "випадкова зі зданих"
        self.status_msg.setText(
            f"❄ Холодне повторення · {source} · до {choice.minutes} хв"
        )

    def _advance_cold(self, seconds: float) -> None:
        """Рахує, скільки лишилось на холодне згадування."""
        if not self._review_mode:
            return
        self._cold_left = max(0.0, self._cold_left - seconds)
        if self._cold_left <= 0 and not self._cold_warned:
            self._cold_warned = True
            self._log(
                "Час вийшов. Допиши думку й тисни F5: краще здати як є, ніж "
                "просидіти над задачею до ночі.",
                Colors.warn,
            )
        self._update_timer_label()

    def _end_cold_review(self) -> None:
        """Холодне повторення — одна спроба: далі підказки знову доступні."""
        self._review_mode = False
        self._cold_left = 0.0
        self._cold_warned = False
        self.btn_hint.setEnabled(True)
        self.panel.set_locked(False)
        self._log(
            "Холодне повторення завершено — підказки знову доступні, якщо "
            "захочеш пройти задачу спокійно.",
            Colors.muted,
        )
        self._update_timer_label()

    def focus_search(self) -> None:
        self.sidebar.set_mode(0)
        self.sidebar.search.setFocus()

    def toggle_manual_done(self, task_id: str | bool | None = None) -> None:
        """Галочка для пунктів, які робляться поза тренажером (venv, Git, pytest)."""
        identifier = task_id if isinstance(task_id, str) and task_id else self._current_id()
        task = find_task(identifier) if identifier else None
        if task is None:
            self.status_msg.setText("Спершу вибери пункт у плані зліва")
            return

        if self.db.status(task.id) == "done":
            answer = QMessageBox.question(
                self, "Зняти позначку?",
                f'«{task.title}» повернеться в план як незавершений пункт.',
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.db.reset_task(task.id)
            self._log(f'Позначку знято: {task.title}', Colors.muted)
        else:
            self.session.mark_manual_done(task)
            self._log(f'Позначено виконаним: {task.title}', Colors.success)

        self._refresh_all()
        self.open_task(task.id)
        self.rewrite_roadmap(silent=True)
        self._write_progress(silent=True)

    def _current_id(self) -> str | None:
        """Id поточної задачі або поточного вибраного пункту плану."""
        if self._task is not None:
            return self._task.id
        item = self.sidebar.tree.currentItem()
        if item is not None:
            return item.data(0, Qt.ItemDataRole.UserRole)
        return None

    def reset_code(self) -> None:
        if self._task is None:
            return
        answer = QMessageBox.question(
            self, "Скинути код?",
            "Поточний код буде замінено на заготовку. Продовжити?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.editor.setPlainText(self._task.starter)
            self._last_saved = self._task.starter
            self.console.clear()
            self.status_msg.setText("Код скинуто до заготовки")

    def reset_task_progress(self) -> None:
        if self._task is None:
            return
        answer = QMessageBox.question(
            self, "Скинути прогрес задачі?",
            f'Прогрес «{self._task.title}» буде стерто: спроби, XP, підказки, '
            "черга повторень. Далі — як уперше.",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.db.reset_task(self._task.id)
            self._refresh_all()
            self.open_task(self._task.id)
            self.status_msg.setText("Прогрес задачі скинуто")

    def save_code_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти код", f"{self._task.id if self._task else 'solution'}.py",
            "Python (*.py)",
        )
        if not path:
            return
        Path(path).write_text(self.editor.toPlainText(), encoding="utf-8")
        self.status_msg.setText(f"Збережено: {Path(path).name}")

    def _save_current_code(self) -> None:
        if self._task is not None and not self._review_mode:
            text = self.editor.toPlainText()
            self.db.save_code(self._task.id, text)
            self._last_saved = text

    def _show_stdin_hint(self, task) -> None:
        if task.stdin:
            feed = " / ".join(task.stdin.splitlines())
            self.stdin_label.setText(f"Ввід для запуску: {feed}")
        elif task.has_files:
            self.stdin_label.setText(
                "У цій задачі є файли: " + ", ".join(task.files)
            )
        else:
            self.stdin_label.setText("")

    def open_hints_tab(self) -> None:
        self.panel.tabs.setCurrentIndex(TAB_HINTS)

    def jump_to_line(self, line: int) -> None:
        """Ставить курсор на рядок, на який вказала помилка.

        Шукати очима рядок 37 у файлі — саме та дрібниця, через яку новачок
        кидає задачу. Тому картка з поясненням помилки має кнопку з номером.
        """
        if self._task is None or line <= 0:
            return
        block = self.editor.document().findBlockByNumber(line - 1)
        if not block.isValid():
            self.status_msg.setText(f"У файлі немає рядка {line}")
            return

        cursor = self.editor.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock,
            QTextCursor.MoveMode.KeepAnchor,
        )
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        self.editor.setFocus()
        self.status_msg.setText(f"Рядок {line} — саме тут сталася помилка")

    def practice_topic(self, topic_name: str) -> None:
        """Відкриває задачу з теми, де статистика бачить провали.

        Список слабких тем раніше лише повідомляв проблему — тепер з нього
        можна одразу піти працювати.
        """
        statuses = self.db.statuses()
        for task in study_tasks():
            if topic_of(task.id) != topic_name:
                continue
            if statuses.get(task.id) == "done":
                continue
            self.open_task(task.id)
            self.sidebar.select(task.id)
            self.status_msg.setText(f"Тренуємо тему: {topic_name}")
            return

        self.sidebar.set_mode(0)
        self.status_msg.setText(
            f"У темі «{topic_name}» усі задачі здані — час на повторення"
        )

    @staticmethod
    def _task_position(task_id: str) -> tuple[int, int] | None:
        """«Задача 5 із 31» — щоб було видно, де ти на шляху."""
        ready = study_tasks()
        for index, task in enumerate(ready, start=1):
            if task.id == task_id:
                return index, len(ready)
        return None

    # ==================================================================
    # запуск коду (м'ясо — в ui/run_flow.py)
    # ==================================================================

    def run_code_only(self) -> None:
        self.flow.run_code_only()

    def run_checks(self) -> None:
        self.flow.run_checks()

    def _start_run(self, with_checks: bool) -> None:
        self.flow.start_run(with_checks=with_checks)

    def _run_in_thread(self, task, code: str, checks) -> None:
        self.flow.run_in_thread(task, code, checks)

    def _on_run_finished(self, result: RunResult) -> None:
        self.flow.on_run_finished(result)

    def review_current_code(self) -> None:
        """Розбирає код із редактора й показує вкладку «Рев'ю». F6.

        Це не оцінка й не перевірка: тести кажуть, чи код працює, а розбір —
        чи його зрозуміє інша людина. Тому він нічого не блокує й не зменшує XP.
        """
        if self._task is None:
            self.status_msg.setText("Спершу вибери задачу з плану зліва")
            return

        review = self._refresh_review()
        self.panel.tabs.setCurrentIndex(TAB_REVIEW)
        self.status_msg.setText(review.summary)
        self._log(f"Рев'ю коду: {review.summary}", Colors.muted)

    def _check_names(self) -> set[str]:
        """Імена, які потрібні прихованим перевіркам задачі.

        Перевірки виконуються в тому ж файлі, тому можуть читати змінні
        людини. Якщо розбір про це не знає, він радить видалити те, без чого
        задача перестане здаватись — це найгірше, що може зробити порадник.
        """
        if self._task is None:
            return set()
        return names_used_in(
            check.code for check in self._task.checks if check.code
        )

    def _refresh_review(self, *, announce: bool = False) -> CodeReview:
        """Оновлює розбір коду, не перемикаючи вкладку (тихо, після запуску).

        Заготовку задачі не розбираємо: доки людина нічого не написала, будь-яке
        зауваження було б докором за чужий код.
        """
        code = self.editor.toPlainText()
        if self._task is not None and code.strip() == self._task.starter.strip():
            review = CodeReview(summary=STARTER_REVIEW)
        else:
            review = review_code(code, keep=self._check_names())
        self.panel.show_review(review)
        if announce and review.issues:
            self._log(
                f"» Рев'ю коду: {issues_phrase(len(review.issues))} — вкладка «Рев'ю»",
                Colors.muted,
            )
        return review

    def _render_update(self, update: StudyUpdate, task, result: RunResult,
                       *, cold: bool = False) -> None:
        """Малює те, що вирішило ядро: XP, статус, чергу повторень."""
        self.flow.render_update(update, task, result, cold=cold)

    # ==================================================================
    # підказки й таймер активної роботи
    # ==================================================================

    def _on_hint_revealed(self, index: int, is_solution: bool) -> None:
        if self._task is None:
            return
        xp = self.session.record_hint(self._task, index, is_solution)
        self.panel.update_xp_preview(xp, self.db.hints_used(self._task.id))
        self._log(f"Підказка {index} — XP за задачу тепер {xp}", Colors.warn)

    def _use_solution(self, text: str) -> None:
        if self._task is None:
            return
        price = scoring.xp_for(self._task, solution_used=True)
        answer = QMessageBox.question(
            self, "Вставити розв'язок?",
            "Код у редакторі буде замінено готовим розв'язком.\n\n"
            f"XP за цю задачу впаде до {price}, а сама задача потрапить у чергу "
            "повторень.\n\nУсе одно спробуй перебрати код руками — інакше на "
            "наступній задачі буде так само важко.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        xp = self.session.use_solution(self._task)
        self.editor.setPlainText(text)
        self.editor.setFocus()
        self.panel.update_xp_preview(xp, self.db.hints_used(self._task.id))
        self._log(
            "Розв'язок вставлено в редактор. Перепиши його своїми руками — "
            "це і є вправа.",
            Colors.warn,
        )

    def _tick(self) -> None:
        """Раз на 5 секунд: рахуємо час роботи й тихо зберігаємо код."""
        if self._task is None or self._running:
            return
        if not self.isActiveWindow():
            return  # у фоні час не йде

        if self._review_mode:
            # Холодне повторення: свій відлік і жодного запису в прогрес.
            # Збережений розв'язок і набраний час за задачею лишаються як були.
            self._advance_cold(TICK_SECONDS)
            return

        code = self.editor.toPlainText()
        if code != self._last_saved:      # автозбереження: крах не з'їсть роботу
            self.db.save_code(self._task.id, code)
            self._last_saved = code

        if self.db.status(self._task.id) == "done":
            return

        active = self.db.add_active_seconds(self._task.id, TICK_SECONDS)
        self.panel.tick(active)
        self._update_timer_label()

    def _update_timer_label(self) -> None:
        if self._task is None:
            self.timer_label.setText("")
            return
        if self._review_mode:
            left = max(0, int(self._cold_left))
            self.timer_label.setText(
                f"❄ Холодне повторення · лишилось {left // 60}:{left % 60:02d}"
                if left else
                "❄ Холодне повторення · час вийшов — здай як є (F5)"
            )
            return
        active = self.db.active_seconds(self._task.id)
        if self.db.status(self._task.id) == "done":
            self.timer_label.setText(
                f"Здано ✓ · час над задачею {int(active) // 60} хв"
            )
            return
        left = max(0, int(self._task.minutes * 60 - active))
        clock = f"{int(active) // 60}:{int(active) % 60:02d}"
        if left:
            self.timer_label.setText(
                f"Час над задачею {clock} · розв'язок через "
                f"{left // 60}:{left % 60:02d}"
            )
        else:
            self.timer_label.setText(
                f"Час над задачею {clock} · розв'язок відкрито"
            )

    # ==================================================================
    # роадмап, прогрес, експорт (м'ясо — в ui/file_sync.py)
    # ==================================================================

    def _files_write_due(self, force: bool) -> bool:
        return self.files.due(force)

    def rewrite_roadmap(self, silent: bool = False, force: bool = False) -> None:
        self.files.rewrite_roadmap(silent=silent, force=force)

    def _write_progress(self, silent: bool = False, force: bool = False) -> None:
        """Пише progress.json — його можна тримати в Git і переносити між машинами."""
        self.files.write_progress(silent=silent, force=force)

    def export_progress(self) -> None:
        self.files.export_progress()

    def import_progress(self) -> None:
        self.files.import_progress()

    def restore_from_backup(self) -> None:
        """Відкочує базу до однієї з авто-копій із `backups/`."""
        self.files.restore_from_backup()

    def export_solutions(self) -> None:
        """Складає розв'язані задачі у файли — це вже заготовка портфоліо."""
        self.files.export_solutions()

    def _refresh_all(self) -> None:
        self.views.refresh_all()

    def _refresh_mistakes(self) -> None:
        """Журнал помилок: що саме не пройшло й скільки разів."""
        self.views.refresh_mistakes()

    def _refresh_digest(self) -> None:
        """Тижневий огляд — одні розрахунки на сторінку, меню й вікно."""
        self.views.refresh_digest()

    def show_digest(self) -> None:
        """Відкриває тижневий огляд (меню, Ctrl+Shift+W або сторінка «Прогрес»)."""
        self.dialogs.show_digest()

    def _forget_digest(self, _result: int) -> None:
        self.dialogs.forget_digest(_result)

    def _open_from_digest(self, task_id: str) -> None:
        self.dialogs.open_from_digest(task_id)

    def _refresh_plan(self) -> None:
        self.views.refresh_plan()

    def _refresh_progress(self) -> None:
        self.views.refresh_progress()

    def _done_count(self) -> int:
        return self.views.done_count()

    def _refresh_reviews(self) -> None:
        self.views.refresh_reviews()

    def _refresh_stats(self) -> None:
        self.views.refresh_stats()

    def _update_today_badge(self, streak: int) -> None:
        """Нагадування про сьогоднішню практику — серія днів не чекає."""
        self.views.update_today_badge(streak)

    def _load_history(self, task_id: str) -> None:
        self.views.load_history(task_id)

    # ==================================================================
    # службове
    # ==================================================================

    def _set_run_enabled(self, enabled: bool) -> None:
        self.btn_run.setEnabled(enabled)
        self.btn_check.setEnabled(enabled)
        if not enabled and self._running:
            self.btn_run.setText("⏳  Виконується…")
            self.btn_check.setText("⏳  Перевіряю…")
        else:
            self.btn_run.setText("▶  Запустити")
            self.btn_check.setText("✓  Перевірити")

    def _log(self, text: str, colour: str) -> None:
        self.console.setTextColor(QColor(colour))
        self.console.append(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def _update_position(self) -> None:
        cursor = self.editor.textCursor()
        self.position_label.setText(
            f"Рядок {cursor.blockNumber() + 1}, стовпець {cursor.positionInBlock() + 1}"
        )

    def show_shortcuts(self) -> None:
        self.dialogs.show_shortcuts()

    def open_data_folder(self) -> None:
        """Відкриває теку, де лежить база, копії й налаштування."""
        self.dialogs.open_data_folder()

    def open_log_file(self) -> None:
        self.dialogs.open_log_file()

    def show_about(self) -> None:
        self.dialogs.show_about()

    def closeEvent(self, event) -> None:  # noqa: N802
        # Зупиняємо таймер ПЕРШИМ: він ходить у базу кожні кілька секунд, а
        # базу ми зараз закриємо.
        self.timer.stop()
        self._save_current_code()
        self._save_state()
        self.rewrite_roadmap(silent=True, force=True)
        self._write_progress(silent=True, force=True)
        self.db.close()
        super().closeEvent(event)

    # ==================================================================
    # стан вікна, тема, масштаб шрифту
    # ==================================================================

    def _save_state(self) -> None:
        """Запам'ятовує геометрію, сплітери, тему й останню задачу.

        Без цього кожен запуск починається з нуля: доводиться заново
        розсувати панелі та згадувати, на чому зупинився.
        """
        if self.settings is None:
            return
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue("window/mainSplitter", self.main_splitter.saveState())
        self.settings.setValue("window/editorSplitter", self.editor_splitter.saveState())
        self.settings.setValue("view/theme", Colors.name)
        self.settings.setValue("view/scale", scale())
        self.settings.setValue("view/sidebarMode", self.sidebar.stack.currentIndex())
        self.settings.setValue("view/panelTab", self.panel.tabs.currentIndex())
        self.settings.setValue("study/taskId", self._task.id if self._task else "")
        self.settings.sync()

    def _restore_state(self) -> None:
        """Повертає те, що було при закритті: розміри, тему, задачу."""
        if self.settings is None:
            return

        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        for key, splitter in (("window/mainSplitter", self.main_splitter),
                              ("window/editorSplitter", self.editor_splitter)):
            saved = self.settings.value(key)
            if saved is not None:
                splitter.restoreState(saved)

        set_scale(self._float_setting("view/scale", 1.0))
        Colors.use(str(self.settings.value("view/theme", "dark")))
        self._retheme()

        self.sidebar.set_mode(int(self._float_setting("view/sidebarMode", 0)))

        task_id = str(self.settings.value("study/taskId", "") or "")
        if task_id and find_task(task_id) is not None:
            self.open_task(task_id)
        self.panel.tabs.setCurrentIndex(int(self._float_setting("view/panelTab", 0)))

    def _float_setting(self, key: str, fallback: float) -> float:
        """QSettings повертає рядки — перетворюємо й не падаємо на смітті."""
        try:
            return float(self.settings.value(key, fallback))
        except (TypeError, ValueError):
            return fallback

    def _retheme(self) -> None:
        """Перемальовує все після зміни теми або масштабу.

        QSS застосовується до віджетів сам, але HTML-сторінки (умова,
        довідка, статистика) мають кольори прямо в тексті — тому їх треба
        згенерувати заново, інакше вони лишаться зі старої теми.
        """
        apply_theme(QApplication.instance(), Colors.name)
        self.editor.apply_theme()
        self._refresh_all()
        self._reopen_current()

    def _reopen_current(self) -> None:
        """Перемальовує поточну задачу після зміни теми чи масштабу тексту.

        У холодному повторенні код у базу не пишеться (задум режиму), тому
        написане треба перенести руками: інакше Ctrl+D посеред спроби стер би
        все, що людина встигла набрати, і ще й обнулив би таймер.
        """
        if self._task is None:
            return

        draft = self.editor.toPlainText()
        left = self._cold_left
        review = self._review_mode
        self.open_task(self._task.id, review=review)
        if review:
            self._cold_left = left
            self.editor.setPlainText(draft)
            self._update_timer_label()

    def toggle_theme(self) -> None:
        """Ctrl+D — темна ⇄ світла."""
        Colors.use("light" if Colors.name == "dark" else "dark")
        self._retheme()
        self._save_state()
        self.statusBar().showMessage(
            f"Тема: {'світла' if Colors.name == 'light' else 'темна'}", 2500
        )

    def change_font_scale(self, delta: float) -> None:
        """Ctrl+= / Ctrl+- — більший або менший текст у всьому вікні."""
        set_scale(scale() + delta)
        self._retheme()
        self._save_state()
        self.statusBar().showMessage(f"Масштаб шрифту: {round(scale() * 100)}%", 2500)

    def reset_font_scale(self) -> None:
        set_scale(1.0)
        self._retheme()
        self._save_state()
        self.statusBar().showMessage("Масштаб шрифту: 100%", 2500)
