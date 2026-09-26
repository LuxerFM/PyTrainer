"""The trainer's main window — where all app parts meet.

Responsibility split:

    curriculum/       what to learn (data: months, topics, tasks, checks)
    trainer/core/     how to check and what to remember (runner, db, scoring, session)
    trainer/ui/       how to show it (this window)

So the window holds no learning rule: it asks `StudySession` what happened
after the attempt, and draws the result.
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
    """Main window."""

    run_finished = Signal(object)

    def __init__(self, db: Database | None = None,
                 roadmap_path: str | Path = ROADMAP_PATH,
                 progress_path: str | Path = PROGRESS_PATH,
                 settings_path: str | Path | None = SETTINGS_PATH) -> None:
        super().__init__()
        from ..core.crashlog import version_line

        self.setWindowTitle(self.tr("{ver} — тренажер Python").format(
            ver=version_line()))
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
    # interface
    # ==================================================================

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("Файл"))
        self._add_action(file_menu, self.tr("Зберегти код…"), "Ctrl+S", self.save_code_as)
        self._add_action(file_menu, self.tr("Скинути код до заготовки"), None, self.reset_code)
        file_menu.addSeparator()
        self._add_action(file_menu, self.tr("Експортувати розв'язані задачі…"), None,
                         self.export_solutions)
        self._add_action(file_menu, self.tr("Експортувати прогрес…"), None, self.export_progress)
        self._add_action(file_menu, self.tr("Імпортувати прогрес…"), None, self.import_progress)
        self._add_action(file_menu, self.tr("Відновити з копії…"), None,
                         self.restore_from_backup)
        self._add_action(file_menu, self.tr("Відкрити теку з даними"), None,
                         self.open_data_folder)
        self._add_action(file_menu, self.tr("Відкрити файл журналу"), None,
                         self.open_log_file)
        file_menu.addSeparator()
        self._add_action(file_menu, self.tr("Оновити Python-Roadmap.md"), None,
                         lambda: self.rewrite_roadmap(force=True))
        file_menu.addSeparator()
        self._add_action(file_menu, self.tr("Вихід"), "Ctrl+Q", self.close)

        run_menu = self.menuBar().addMenu(self.tr("Запуск"))
        self._add_action(run_menu, self.tr("Запустити"), "Ctrl+Return", self.run_code_only)
        self._add_action(run_menu, self.tr("Перевірити тестами"), "F5", self.run_checks)
        self._add_action(run_menu, self.tr("Розібрати мій код (рев'ю)"), "F6",
                         self.review_current_code)
        self._add_action(run_menu, self.tr("Очистити консоль"), None, self.console.clear)

        study_menu = self.menuBar().addMenu(self.tr("Навчання"))
        self._add_action(study_menu, self.tr("План на сьогодні"), "Ctrl+L",
                         lambda: self.sidebar.set_mode(3))
        self._add_action(study_menu, self.tr("На повторення"), "Ctrl+R", lambda: self.sidebar.set_mode(1))
        self._add_action(study_menu, self.tr("Холодне повторення (випадкова задача)"),
                         "Ctrl+Shift+R", self.start_cold_review)
        self._add_action(study_menu, self.tr("Прогрес і слабкі місця"), "Ctrl+P",
                         lambda: self.sidebar.set_mode(2))
        self._add_action(study_menu, self.tr("Тижневий огляд"), "Ctrl+Shift+W",
                         self.show_digest)
        self._add_action(study_menu, self.tr("Наступна незавершена задача"), "Ctrl+N",
                         self.open_next_task)
        self._add_action(study_menu, self.tr("Знайти задачу"), "Ctrl+F", self.focus_search)
        study_menu.addSeparator()
        self._add_action(study_menu, self.tr("Позначити виконаним (зроблено поза тренажером)"),
                         None, self.toggle_manual_done)
        study_menu.addSeparator()
        self._add_action(study_menu, self.tr("Скинути прогрес цієї задачі"), None,
                         self.reset_task_progress)

        view_menu = self.menuBar().addMenu(self.tr("Вигляд"))
        self._add_action(view_menu, self.tr("Темна / світла тема"), "Ctrl+D", self.toggle_theme)
        view_menu.addSeparator()
        self._add_action(view_menu, self.tr("Більший шрифт"), "Ctrl++",
                         lambda: self.change_font_scale(0.05))
        self._add_action(view_menu, self.tr("Менший шрифт"), "Ctrl+-",
                         lambda: self.change_font_scale(-0.05))
        self._add_action(view_menu, self.tr("Звичайний розмір шрифту"), "Ctrl+0",
                         self.reset_font_scale)

        help_menu = self.menuBar().addMenu(self.tr("Довідка"))
        self._add_action(help_menu, self.tr("Гарячі клавіші"), "F1", self.show_shortcuts)
        self._add_action(help_menu, self.tr("Про тренажер"), None, self.show_about)

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
        self.btn_run.setText(self.tr("▶  Запустити"))
        self.btn_run.clicked.connect(self.run_code_only)

        self.btn_check = QToolButton()
        self.btn_check.setText(self.tr("✓  Перевірити"))
        self.btn_check.clicked.connect(self.run_checks)

        self.btn_hint = QToolButton()
        self.btn_hint.setText(self.tr("Підказка"))
        self.btn_hint.clicked.connect(self.open_hints_tab)

        self.btn_reset = QToolButton()
        self.btn_reset.setText(self.tr("↺  Скинути"))
        self.btn_reset.clicked.connect(self.reset_code)

        for button in (self.btn_run, self.btn_check, self.btn_hint, self.btn_reset):
            bar.addWidget(button)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred,
        )
        bar.addWidget(spacer)

        self.today_badge = QLabel(self.tr("Сьогодні: 0 запусків"))
        self.today_badge.setObjectName("Badge")
        self.review_badge = QLabel(self.tr("На повторення: 0"))
        self.review_badge.setObjectName("Badge")
        self.xp_badge = QLabel("XP 0")
        self.xp_badge.setObjectName("BadgeAccent")
        self.streak_badge = QLabel(self.tr("Серія: 0 дн."))
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

        hint = QLabel(self.tr("Ctrl+Enter — запустити · F5 — перевірити тестами"))
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
        console.setPlaceholderText(self.tr("Тут з'явиться вивід твоєї програми…"))
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
        title = QLabel(self.tr("КОНСОЛЬ"))
        title.setObjectName("SectionTitle")
        row.addWidget(title)
        row.addStretch(1)
        clear = QPushButton(self.tr("Очистити"))
        clear.setObjectName("Ghost")
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self.console.clear)
        row.addWidget(clear)

        box.addWidget(header)
        box.addWidget(self.console, 1)
        return holder

    def _build_statusbar(self) -> None:
        self.status_msg = QLabel(self.tr("Готово"))
        self.statusBar().addWidget(self.status_msg, 1)
        self.timer_label = QLabel("")
        self.statusBar().addPermanentWidget(self.timer_label)
        self.position_label = QLabel(self.tr("Рядок 1, стовпець 1"))
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
    # working with tasks
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
                self.tr("Цей пункт робиться не в тренажері, а у твоєму терміналі — "
                        "саме там навичка й закріплюється. Зробив? Познач галочкою, "
                        "щоб вона з'явилась і в Python-Roadmap.md.")
                if task is not None else self.tr("Задачу не знайдено."),
                task_id=task.id if task is not None else None,
                manual_done=done,
            )
            self.status_msg.setText(
                self.tr("Пункт поза тренажером — познач галочкою, коли зробиш")
                if task is not None else self.tr("Задачу не знайдено")
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
        # Cold review starts from the stub: showing your own solution would
        # be recognition, not recall. The saved code in the database stays
        # untouched here (see _start_run and _tick).
        text = task.starter if review else (saved if saved else task.starter)
        self.editor.setPlainText(text)
        self._last_saved = text
        self.console.clear()
        if review:
            self._log(
                self.tr("❄ Холодне повторення: {title}. Підказки й розв'язок "
                        "недоступні, час — до {mins} хв. Згадай сам — і тисни F5.").format(
                            title=task.title, mins=cold_seconds(task) // 60),
                Colors.warn,
            )
        self._show_stdin_hint(task)
        self.file_label.setText(f"{task.id}.py")
        self.status_msg.setText(
            self.tr("Повторення: {title}").format(title=task.title)
            if review else self.tr("Відкрито: {title}").format(title=task.title)
        )
        self._update_timer_label()

    def open_next_task(self) -> None:
        statuses = self.db.statuses()
        for task in study_tasks():
            if statuses.get(task.id) != "done":
                self.open_task(task.id)
                self.sidebar.select(task.id)
                return
        self.status_msg.setText(self.tr("Усі задачі, які вже написані, здані 🎉"))

    # ==================================================================
    # cold review
    # ==================================================================

    def start_cold_review(self) -> None:
        """A random passed task with no hints and no solution, on a timer.

        Why a separate mode: opening your own passed task is easy, recalling
        it from zero is not. So the editor starts from the stub, hints and
        solution are off, and the verdict goes to the same review queue.
        """
        choice = pick_cold_task(self.db, exclude=self._current_id())
        if choice is None:
            self.status_msg.setText(
                self.tr("Холодне повторення — для вже зданих задач. Здай якусь "
                        "задачу (крім відкритої зараз) — і воно стане доступним.")
            )
            return

        task = choice.task
        self.open_task(task.id, review=True)
        # The tree mark shows, but the page does not switch: if the cold
        # review started from the review list, that is where you want to
        # return.
        self.sidebar.tree.select(task.id)
        source = self.tr("з черги повторень") if choice.from_queue \
            else self.tr("випадкова зі зданих")
        self.status_msg.setText(
            self.tr("❄ Холодне повторення · {source} · до {mins} хв").format(
                source=source, mins=choice.minutes)
        )

    def _advance_cold(self, seconds: float) -> None:
        """Counts down the cold-recall time left."""
        if not self._review_mode:
            return
        self._cold_left = max(0.0, self._cold_left - seconds)
        if self._cold_left <= 0 and not self._cold_warned:
            self._cold_warned = True
            self._log(
                self.tr("Час вийшов. Допиши думку й тисни F5: краще здати як є, ніж "
                        "просидіти над задачею до ночі."),
                Colors.warn,
            )
        self._update_timer_label()

    def _end_cold_review(self) -> None:
        """Cold review is one attempt: hints are available again after."""
        self._review_mode = False
        self._cold_left = 0.0
        self._cold_warned = False
        self.btn_hint.setEnabled(True)
        self.panel.set_locked(False)
        self._log(
            self.tr("Холодне повторення завершено — підказки знову доступні, якщо "
                    "захочеш пройти задачу спокійно."),
            Colors.muted,
        )
        self._update_timer_label()

    def focus_search(self) -> None:
        self.sidebar.set_mode(0)
        self.sidebar.search.setFocus()

    def toggle_manual_done(self, task_id: str | bool | None = None) -> None:
        """Tick for items done outside the trainer (venv, Git, pytest)."""
        identifier = task_id if isinstance(task_id, str) and task_id else self._current_id()
        task = find_task(identifier) if identifier else None
        if task is None:
            self.status_msg.setText(self.tr("Спершу вибери пункт у плані зліва"))
            return

        if self.db.status(task.id) == "done":
            answer = QMessageBox.question(
                self, self.tr("Зняти позначку?"),
                self.tr("«{title}» повернеться в план як незавершений пункт.").format(
                    title=task.title),
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.db.reset_task(task.id)
            self._log(self.tr("Позначку знято: {title}").format(title=task.title),
                       Colors.muted)
        else:
            self.session.mark_manual_done(task)
            self._log(self.tr("Позначено виконаним: {title}").format(title=task.title),
                       Colors.success)

        self._refresh_all()
        self.open_task(task.id)
        self.rewrite_roadmap(silent=True)
        self._write_progress(silent=True)

    def _current_id(self) -> str | None:
        """Id of the current task or the currently picked plan item."""
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
            self, self.tr("Скинути код?"),
            self.tr("Поточний код буде замінено на заготовку. Продовжити?"),
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.editor.setPlainText(self._task.starter)
            self._last_saved = self._task.starter
            self.console.clear()
            self.status_msg.setText(self.tr("Код скинуто до заготовки"))

    def reset_task_progress(self) -> None:
        if self._task is None:
            return
        answer = QMessageBox.question(
            self, self.tr("Скинути прогрес задачі?"),
            self.tr("Прогрес «{title}» буде стерто: спроби, XP, підказки, "
                    "черга повторень. Далі — як уперше.").format(title=self._task.title),
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.db.reset_task(self._task.id)
            self._refresh_all()
            self.open_task(self._task.id)
            self.status_msg.setText(self.tr("Прогрес задачі скинуто"))

    def save_code_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Зберегти код"), f"{self._task.id if self._task else 'solution'}.py",
            "Python (*.py)",
        )
        if not path:
            return
        Path(path).write_text(self.editor.toPlainText(), encoding="utf-8")
        self.status_msg.setText(self.tr("Збережено: {name}").format(name=Path(path).name))

    def _save_current_code(self) -> None:
        if self._task is not None and not self._review_mode:
            text = self.editor.toPlainText()
            self.db.save_code(self._task.id, text)
            self._last_saved = text

    def _show_stdin_hint(self, task) -> None:
        if task.stdin:
            feed = " / ".join(task.stdin.splitlines())
            self.stdin_label.setText(self.tr("Ввід для запуску: {feed}").format(feed=feed))
        elif task.has_files:
            self.stdin_label.setText(
                self.tr("У цій задачі є файли: {files}").format(files=", ".join(task.files))
            )
        else:
            self.stdin_label.setText("")

    def open_hints_tab(self) -> None:
        self.panel.tabs.setCurrentIndex(TAB_HINTS)

    def jump_to_line(self, line: int) -> None:
        """Puts the cursor on the line the error pointed at.

        Hunting line 37 with your eyes in a file is exactly the trifle that
        makes a beginner drop the task. So the error-explanation card carries
        a numbered button.
        """
        if self._task is None or line <= 0:
            return
        block = self.editor.document().findBlockByNumber(line - 1)
        if not block.isValid():
            self.status_msg.setText(self.tr("У файлі немає рядка {n}").format(n=line))
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
        self.status_msg.setText(self.tr("Рядок {n} — саме тут сталася помилка").format(n=line))

    def practice_topic(self, topic_name: str) -> None:
        """Opens a task from the topic where stats see failures.

        The weak-topic list used to only report the problem — now you can go
        work straight from it.
        """
        statuses = self.db.statuses()
        for task in study_tasks():
            if topic_of(task.id) != topic_name:
                continue
            if statuses.get(task.id) == "done":
                continue
            self.open_task(task.id)
            self.sidebar.select(task.id)
            self.status_msg.setText(self.tr("Тренуємо тему: {topic}").format(topic=topic_name))
            return

        self.sidebar.set_mode(0)
        self.status_msg.setText(
            self.tr("У темі «{topic}» усі задачі здані — час на повторення").format(
                topic=topic_name)
        )

    @staticmethod
    def _task_position(task_id: str) -> tuple[int, int] | None:
        """"Task 5 of 31" — so you see where you are on the path."""
        ready = study_tasks()
        for index, task in enumerate(ready, start=1):
            if task.id == task_id:
                return index, len(ready)
        return None

    # ==================================================================
    # running code (meat lives in ui/run_flow.py)
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
        """Reviews the editor code and shows the "Рев'ю" tab. F6.

        This is neither grading nor checking: tests say whether the code
        works, while review says whether another human will understand it.
        So it blocks nothing and lowers no XP.
        """
        if self._task is None:
            self.status_msg.setText(self.tr("Спершу вибери задачу з плану зліва"))
            return

        review = self._refresh_review()
        self.panel.tabs.setCurrentIndex(TAB_REVIEW)
        self.status_msg.setText(review.summary)
        self._log(self.tr("Рев'ю коду: {summary}").format(summary=review.summary),
                   Colors.muted)

    def _check_names(self) -> set[str]:
        """Names the task's hidden checks need.

        Checks run in the same file, so they can read the human's variables.
        If review does not know that, it advises deleting what the task
        cannot pass without — the worst an advisor can do.
        """
        if self._task is None:
            return set()
        return names_used_in(
            check.code for check in self._task.checks if check.code
        )

    def _refresh_review(self, *, announce: bool = False) -> CodeReview:
        """Refreshes the code review without switching tabs (quiet, after a run).

        The task stub is never reviewed: until the human wrote nothing, any
        remark would scold someone else's code.
        """
        code = self.editor.toPlainText()
        if self._task is not None and code.strip() == self._task.starter.strip():
            review = CodeReview(summary=STARTER_REVIEW)
        else:
            review = review_code(code, keep=self._check_names())
        self.panel.show_review(review)
        if announce and review.issues:
            self._log(
                self.tr("» Рев'ю коду: {phrase} — вкладка «Рев'ю»").format(
                    phrase=issues_phrase(len(review.issues))),
                Colors.muted,
            )
        return review

    def _render_update(self, update: StudyUpdate, task, result: RunResult,
                       *, cold: bool = False) -> None:
        """Draws what the core decided: XP, status, review queue."""
        self.flow.render_update(update, task, result, cold=cold)

    # ==================================================================
    # hints and active-work timer
    # ==================================================================

    def _on_hint_revealed(self, index: int, is_solution: bool) -> None:
        if self._task is None:
            return
        xp = self.session.record_hint(self._task, index, is_solution)
        self.panel.update_xp_preview(xp, self.db.hints_used(self._task.id))
        self._log(self.tr("Підказка {n} — XP за задачу тепер {xp}").format(
            n=index, xp=xp), Colors.warn)

    def _use_solution(self, text: str) -> None:
        if self._task is None:
            return
        price = scoring.xp_for(self._task, solution_used=True)
        answer = QMessageBox.question(
            self, self.tr("Вставити розв'язок?"),
            self.tr("Код у редакторі буде замінено готовим розв'язком.\n\n"
                    "XP за цю задачу впаде до {price}, а сама задача потрапить у чергу "
                    "повторень.\n\nУсе одно спробуй перебрати код руками — інакше на "
                    "наступній задачі буде так само важко.").format(price=price),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        xp = self.session.use_solution(self._task)
        self.editor.setPlainText(text)
        self.editor.setFocus()
        self.panel.update_xp_preview(xp, self.db.hints_used(self._task.id))
        self._log(
            self.tr("Розв'язок вставлено в редактор. Перепиши його своїми руками — "
                    "це і є вправа."),
            Colors.warn,
        )

    def _tick(self) -> None:
        """Every 5 seconds: count work time and quietly save the code."""
        if self._task is None or self._running:
            return
        if not self.isActiveWindow():
            return  # no time passes in the background

        if self._review_mode:
            # Cold review: its own countdown and zero progress writes.
            # The saved solution and accrued task time stay as they were.
            self._advance_cold(TICK_SECONDS)
            return

        code = self.editor.toPlainText()
        if code != self._last_saved:      # autosave: a crash will not eat the work
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
                self.tr("❄ Холодне повторення · лишилось {m}:{s:02d}").format(
                    m=left // 60, s=left % 60)
                if left else
                self.tr("❄ Холодне повторення · час вийшов — здай як є (F5)")
            )
            return
        active = self.db.active_seconds(self._task.id)
        if self.db.status(self._task.id) == "done":
            self.timer_label.setText(
                self.tr("Здано ✓ · час над задачею {m} хв").format(m=int(active) // 60)
            )
            return
        left = max(0, int(self._task.minutes * 60 - active))
        clock = f"{int(active) // 60}:{int(active) % 60:02d}"
        if left:
            self.timer_label.setText(
                self.tr("Час над задачею {clock} · розв'язок через {m}:{s:02d}").format(
                    clock=clock, m=left // 60, s=left % 60)
            )
        else:
            self.timer_label.setText(
                self.tr("Час над задачею {clock} · розв'язок відкрито").format(clock=clock)
            )

    # ==================================================================
    # roadmap, progress, export (meat lives in ui/file_sync.py)
    # ==================================================================

    def _files_write_due(self, force: bool) -> bool:
        return self.files.due(force)

    def rewrite_roadmap(self, silent: bool = False, force: bool = False) -> None:
        self.files.rewrite_roadmap(silent=silent, force=force)

    def _write_progress(self, silent: bool = False, force: bool = False) -> None:
        """Writes progress.json — keepable in Git and portable across machines."""
        self.files.write_progress(silent=silent, force=force)

    def export_progress(self) -> None:
        self.files.export_progress()

    def import_progress(self) -> None:
        self.files.import_progress()

    def restore_from_backup(self) -> None:
        """Rolls the database back to one of the `backups/` auto-copies."""
        self.files.restore_from_backup()

    def export_solutions(self) -> None:
        """Lays solved tasks out into files — a portfolio draft already."""
        self.files.export_solutions()

    def _refresh_all(self) -> None:
        self.views.refresh_all()

    def _refresh_mistakes(self) -> None:
        """Mistake journal: what exactly failed and how many times."""
        self.views.refresh_mistakes()

    def _refresh_digest(self) -> None:
        """Weekly digest — the same numbers for the page, the menu and the window."""
        self.views.refresh_digest()

    def show_digest(self) -> None:
        """Opens the weekly digest (menu, Ctrl+Shift+W or the "Прогрес" page)."""
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
        """Today-practice reminder — the day streak does not wait."""
        self.views.update_today_badge(streak)

    def _load_history(self, task_id: str) -> None:
        self.views.load_history(task_id)

    # ==================================================================
    # service
    # ==================================================================

    def _set_run_enabled(self, enabled: bool) -> None:
        self.btn_run.setEnabled(enabled)
        self.btn_check.setEnabled(enabled)
        if not enabled and self._running:
            self.btn_run.setText(self.tr("⏳  Виконується…"))
            self.btn_check.setText(self.tr("⏳  Перевіряю…"))
        else:
            self.btn_run.setText(self.tr("▶  Запустити"))
            self.btn_check.setText(self.tr("✓  Перевірити"))

    def _log(self, text: str, colour: str) -> None:
        self.console.setTextColor(QColor(colour))
        self.console.append(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def _update_position(self) -> None:
        cursor = self.editor.textCursor()
        self.position_label.setText(
            self.tr("Рядок {line}, стовпець {col}").format(
                line=cursor.blockNumber() + 1, col=cursor.positionInBlock() + 1)
        )

    def show_shortcuts(self) -> None:
        self.dialogs.show_shortcuts()

    def open_data_folder(self) -> None:
        """Opens the folder holding the database, copies and settings."""
        self.dialogs.open_data_folder()

    def open_log_file(self) -> None:
        self.dialogs.open_log_file()

    def show_about(self) -> None:
        self.dialogs.show_about()

    def closeEvent(self, event) -> None:  # noqa: N802
        # Stop the timer FIRST: it walks the database every few seconds, and
        # the database is about to close.
        self.timer.stop()
        self._save_current_code()
        self._save_state()
        self.rewrite_roadmap(silent=True, force=True)
        self._write_progress(silent=True, force=True)
        self.db.close()
        super().closeEvent(event)

    # ==================================================================
    # window state, theme, font scale
    # ==================================================================

    def _save_state(self) -> None:
        """Remembers geometry, splitters, theme and the last task.

        Without this every launch starts from zero: re-spreading panels and
        recalling where you stopped.
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
        """Restores what was there at close: sizes, theme, task."""
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
        """QSettings returns strings — convert, never crash on garbage."""
        try:
            return float(self.settings.value(key, fallback))
        except (TypeError, ValueError):
            return fallback

    def _retheme(self) -> None:
        """Redraws everything after a theme or scale change.

        QSS applies to widgets by itself, but HTML pages (statement,
        reference, stats) carry colours inline in the text — so they must be
        regenerated, else they keep the old theme.
        """
        apply_theme(QApplication.instance(), Colors.name)
        self.editor.apply_theme()
        self._refresh_all()
        self._reopen_current()

    def _reopen_current(self) -> None:
        """Redraws the current task after a theme or text-scale change.

        In cold review no code is written to the database (the mode's idea),
        so the draft must be carried over by hand: else Ctrl+D mid-attempt
        would wipe everything typed and zero the timer too.
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
        """Ctrl+D — dark ⇄ light."""
        Colors.use("light" if Colors.name == "dark" else "dark")
        self._retheme()
        self._save_state()
        self.statusBar().showMessage(
            self.tr("Тема: {name}").format(
                name=self.tr("світла") if Colors.name == "light" else self.tr("темна")),
            2500,
        )

    def change_font_scale(self, delta: float) -> None:
        """Ctrl+= / Ctrl+- — bigger or smaller text across the window."""
        set_scale(scale() + delta)
        self._retheme()
        self._save_state()
        self.statusBar().showMessage(
            self.tr("Масштаб шрифту: {n}%").format(n=round(scale() * 100)), 2500)

    def reset_font_scale(self) -> None:
        set_scale(1.0)
        self._retheme()
        self._save_state()
        self.statusBar().showMessage(self.tr("Масштаб шрифту: 100%"), 2500)
