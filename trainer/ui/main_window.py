"""Головне вікно тренажера — тут зустрічаються всі частини застосунку.

Розділення відповідальності просте:
  * curriculum — що вчити (дані);
  * trainer/core — як перевіряти й що пам'ятати (без інтерфейсу);
  * trainer/ui — як це показати.

Це вікно лише зшиває три шари: відкриває задачу, запускає код, записує
результат у базу й оновлює екрани.
"""

from __future__ import annotations

import threading
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
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

from curriculum import (
    CURRICULUM,
    find_task,
    first_unfinished,
    study_tasks,
    topic_of,
)
from curriculum.roadmap_md import write as write_roadmap

from ..core import scoring
from ..core.db import Database
from ..core.runner import RunResult, run_code
from ..core.stats import overall, weak_topics
from .editor import CodeEditor
from .sidebar import SideNav
from .task_panel import TaskPanel
from .theme import MONO_FONTS, Colors, pick_font

ROOT = Path(__file__).resolve().parents[2]
ROADMAP_PATH = ROOT / "Python-Roadmap.md"
TICK_SECONDS = 5


def _human_date(iso: str) -> str:
    """2026-09-26 → 26.09 (з позначкою прострочення)."""
    try:
        target = date.fromisoformat(iso)
    except ValueError:
        return iso
    text = target.strftime("%d.%m")
    days = (target - date.today()).days
    if days < 0:
        return f"{text} · прострочено"
    if days == 0:
        return f"{text} · сьогодні"
    return f"{text} · через {days} дн."


class MainWindow(QMainWindow):
    """Головне вікно."""

    run_finished = Signal(object)

    def __init__(self, db: Database | None = None,
                 roadmap_path: str | Path = ROADMAP_PATH) -> None:
        super().__init__()
        self.setWindowTitle("PyTrainer — тренажер Python")
        self.resize(1480, 920)
        self.setMinimumSize(1120, 700)

        self.db = db or Database()
        self.roadmap_path = Path(roadmap_path)
        self._task = None
        self._running = False
        self._review_mode = False

        self.sidebar = SideNav()
        self.editor = CodeEditor()
        self.panel = TaskPanel()
        self.console = self._build_console()

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self._connect()

        self.sidebar.load_curriculum(CURRICULUM, self.db.statuses())
        self._refresh_all()

        start = first_unfinished(self.db.statuses()) or study_tasks()[0]
        self.open_task(start.id)

        self.timer = QTimer(self)
        self.timer.setInterval(TICK_SECONDS * 1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ==================================================================
    # збирання інтерфейсу
    # ==================================================================

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        self._add_action(file_menu, "Зберегти код…", "Ctrl+S", self.save_code_as)
        self._add_action(file_menu, "Скинути код до заготовки", None, self.reset_code)
        file_menu.addSeparator()
        self._add_action(file_menu, "Оновити Python-Roadmap.md", None, self.rewrite_roadmap)
        file_menu.addSeparator()
        self._add_action(file_menu, "Вихід", "Ctrl+Q", self.close)

        run_menu = self.menuBar().addMenu("Запуск")
        self._add_action(run_menu, "Запустити", "Ctrl+Return", self.run_code_only)
        self._add_action(run_menu, "Перевірити тестами", "F5", self.run_checks)
        self._add_action(run_menu, "Очистити консоль", None, self.console.clear)

        study_menu = self.menuBar().addMenu("Навчання")
        self._add_action(study_menu, "На повторення", "Ctrl+R", lambda: self.sidebar.set_mode(1))
        self._add_action(study_menu, "Прогрес і слабкі місця", "Ctrl+P",
                         lambda: self.sidebar.set_mode(2))
        self._add_action(study_menu, "Відкрити наступну незавершену задачу", "Ctrl+N",
                         self.open_next_task)
        study_menu.addSeparator()
        self._add_action(study_menu, "Скинути прогрес цієї задачі", None,
                         self.reset_task_progress)

        help_menu = self.menuBar().addMenu("Довідка")
        self._add_action(help_menu, "Гарячі клавіші", "F1", self.show_shortcuts)
        self._add_action(help_menu, "Про тренажер", None, self.show_about)

    def _add_action(self, menu, text: str, shortcut: str | None, slot):
        from PySide6.QtGui import QAction

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

        self.xp_badge = QLabel("XP 0")
        self.xp_badge.setObjectName("BadgeAccent")
        self.streak_badge = QLabel("Серія: 0 дн.")
        self.streak_badge.setObjectName("Badge")
        self.review_badge = QLabel("На повторення: 0")
        self.review_badge.setObjectName("Badge")
        for badge in (self.review_badge, self.xp_badge, self.streak_badge):
            bar.addWidget(badge)

    def _build_body(self) -> None:
        center = QWidget()
        box = QVBoxLayout(center)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self._editor_header())

        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(self.editor)
        vertical.addWidget(self._console_box())
        vertical.setSizes([600, 250])
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 1)
        box.addWidget(vertical, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(center)
        splitter.addWidget(self.panel)
        splitter.setSizes([300, 760, 400])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        self.setCentralWidget(splitter)

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
        self.panel.hint_revealed.connect(self._on_hint_revealed)
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
            self.editor.setPlainText("")
            self.editor.setReadOnly(True)
            self._set_run_enabled(False)
            self.panel.show_placeholder(
                task.title if task else task_id,
                "Ця тема ще попереду: план уже видно в роадмапі, а задачі й теорію "
                "додамо після місяця 1. Спершу — база, без неї решта не має сенсу.",
            )
            self.status_msg.setText("Задача ще не написана — тема попереду")
            return

        self._task = task
        self._review_mode = review
        self.editor.setReadOnly(False)
        self._set_run_enabled(True)

        self.db.mark_in_progress(task.id)
        hints_used = self.db.hints_used(task.id)
        active = self.db.active_seconds(task.id)
        solved = self.db.status(task.id) == "done"

        self.panel.show_task(
            task,
            topic=topic_of(task.id),
            hints_used=hints_used,
            active_seconds=active,
            xp_preview=scoring.xp_for(task, hints_used=hints_used, first_time=not solved),
        )
        self._load_history(task.id)

        saved = self.db.saved_code(task.id)
        self.editor.setPlainText(saved if saved else task.starter)
        self.console.clear()
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
        self.status_msg.setText("Усі задачі місяця 1 здані — час на проєкти 🎉")

    def reset_code(self) -> None:
        if self._task is None:
            return
        answer = QMessageBox.question(
            self, "Скинути код?",
            "Поточний код буде замінено на заготовку. Продовжити?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.editor.setPlainText(self._task.starter)
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
        if self._task is not None:
            self.db.save_code(self._task.id, self.editor.toPlainText())

    def _show_stdin_hint(self, task) -> None:
        if task.stdin:
            feed = " / ".join(task.stdin.splitlines())
            self.stdin_label.setText(f"Ввід для запуску: {feed}")
        else:
            self.stdin_label.setText("")

    def open_hints_tab(self) -> None:
        self.panel.tabs.setCurrentIndex(2)

    # ==================================================================
    # запуск коду
    # ==================================================================

    def run_code_only(self) -> None:
        self._start_run(with_checks=False)

    def run_checks(self) -> None:
        self._start_run(with_checks=True)

    def _start_run(self, with_checks: bool) -> None:
        if self._running or self._task is None:
            return

        task = self._task
        code = self.editor.toPlainText()
        self.db.save_code(task.id, code)
        checks = list(task.checks) if with_checks else []

        self._running = True
        self._set_run_enabled(False)
        self.console.clear()

        label = "Перевірка тестами" if with_checks else "Запуск коду"
        self._log(f"{label}…", Colors.muted)
        if task.stdin:
            self._log(f"→ Ввід: {' / '.join(task.stdin.splitlines())}", Colors.muted)
        self.status_msg.setText(f"{label}…")

        threading.Thread(
            target=self._run_in_thread, args=(code, checks, task.stdin), daemon=True
        ).start()

    def _run_in_thread(self, code: str, checks, stdin: str) -> None:
        self.run_finished.emit(run_code(code, checks, stdin=stdin))

    def _on_run_finished(self, result: RunResult) -> None:
        self._running = False
        self._set_run_enabled(True)

        if result.stdout:
            self._log(result.stdout, Colors.text)
        if result.stderr:
            self._log(result.stderr, Colors.error)
        if not result.stdout and not result.stderr:
            self._log("(вивід порожній)", Colors.muted)

        self.panel.show_result(result, bool(result.ran_checks))

        if not result.ran_checks or self._task is None:
            self.status_msg.setText("Код виконано")
            self._load_history(self._task.id)
            return

        task = self._task
        solved_before = self.db.status(task.id) == "done"
        hints_used = self.db.hints_used(task.id)
        xp = scoring.xp_for(task, hints_used=hints_used, first_time=not solved_before)

        self.db.record_attempt(
            task.id,
            ok=result.all_passed,
            with_checks=True,
            xp=xp if result.all_passed else 0,
        )

        if result.all_passed:
            if solved_before:
                self.db.mark_repeat_passed(task.id, xp)
            else:
                self.db.mark_solved(task.id, xp)
                self.sidebar.mark(task.id, "done")
            self._log(f"Усі перевірки пройдено · +{xp} XP", Colors.success)
            self.status_msg.setText(f"Задача здана! +{xp} XP")

            attempts = self.db.attempts_count(task.id)
            if self._review_mode:
                index, days = self.db.schedule_from_result(task.id, True)
                if days is None:
                    self._log("Повторення більше не потрібне — задачу засвоєно 🎯",
                              Colors.success)
                else:
                    self._log(f"Наступне повторення: через {days} дн.", Colors.muted)
            elif scoring.needs_review(
                solved=True, attempts=attempts,
                solution_used=self.db.solution_used(task.id),
            ):
                self.db.schedule_from_result(task.id, False)
                self._log(
                    "Здано не з першого разу — задачу додано в чергу повторень.",
                    Colors.warn,
                )
            else:
                self.db.clear_review(task.id)
        else:
            self.sidebar.mark(task.id, "current")
            self.db.schedule_from_result(task.id, False)
            passed = result.passed_count
            self._log(f"Пройдено {passed} із {len(result.checks)}", Colors.warn)
            self.status_msg.setText("Є помилки — дивись вкладку «Тести»")

        self._refresh_all()
        self._load_history(task.id)
        self._update_timer_label()
        self.rewrite_roadmap(silent=True)

    # ==================================================================
    # підказки й таймер активної роботи
    # ==================================================================

    def _on_hint_revealed(self, index: int, is_solution: bool) -> None:
        if self._task is None:
            return
        self.db.reveal_hint(self._task.id, index, is_solution)
        hints_used = self.db.hints_used(self._task.id)
        solved = self.db.status(self._task.id) == "done"
        xp = scoring.xp_for(self._task, hints_used=hints_used, first_time=not solved)
        self.panel.update_xp_preview(xp, hints_used)
        self._log(
            f"Підказка {index} — XP за задачу тепер {xp}", Colors.warn
        )

    def _tick(self) -> None:
        """Раз на 5 секунд: рахуємо час роботи над задачею."""
        if self._task is None or self._running:
            return
        if not self.isActiveWindow():
            return  # у фоні час не йде
        if self.db.status(self._task.id) == "done":
            return

        active = self.db.add_active_seconds(self._task.id, TICK_SECONDS)
        self.panel.tick(active)
        self._update_timer_label()

    def _update_timer_label(self) -> None:
        if self._task is None:
            self.timer_label.setText("")
            return
        active = self.db.active_seconds(self._task.id)
        solved = self.db.status(self._task.id) == "done"
        if solved:
            self.timer_label.setText("Задача здана ✓")
            return
        left = max(0, int(self._task.minutes * 60 - active))
        if left:
            self.timer_label.setText(
                f"Час над задачею {int(active) // 60}:{int(active) % 60:02d} · "
                f"розв'язок через {left // 60}:{left % 60:02d}"
            )
        else:
            self.timer_label.setText(
                f"Час над задачею {int(active) // 60}:{int(active) % 60:02d} · "
                "розв'язок відкрито"
            )

    # ==================================================================
    # роадмап, статистика, історія
    # ==================================================================

    def rewrite_roadmap(self, silent: bool = False) -> None:
        statuses = self.db.statuses()
        write_roadmap(
            self.roadmap_path,
            statuses,
            {"xp": self.db.total_xp(), "streak": self.db.streak()},
        )
        if not silent:
            self.status_msg.setText(f"Роадмап оновлено: {self.roadmap_path.name}")

    def _refresh_all(self) -> None:
        self.sidebar.load_curriculum(CURRICULUM, self.db.statuses())
        self._refresh_progress()
        self._refresh_reviews()
        self._refresh_stats()

    def _refresh_progress(self) -> None:
        tasks = study_tasks()
        done = sum(1 for task in tasks if self.db.status(task.id) == "done")
        self.sidebar.set_progress(done, len(tasks))

    def _refresh_reviews(self) -> None:
        due_rows = []
        for row in self.db.due_reviews():
            task = find_task(row["task_id"])
            if task is None:
                continue
            due_rows.append({
                "task_id": task.id,
                "title": task.title,
                "when": f'{_human_date(row["due_date"])} · інтервал '
                        f'{scoring.INTERVALS[min(row["interval_index"], len(scoring.INTERVALS) - 1)]} дн.',
                "tooltip": f'{task.level} · {task.base_xp} XP',
            })

        later_rows = []
        for row in self.db.upcoming_reviews():
            task = find_task(row["task_id"])
            if task is None:
                continue
            later_rows.append({
                "task_id": task.id,
                "title": task.title,
                "when": _human_date(row["due_date"]),
                "tooltip": f'{task.level} · {task.base_xp} XP',
            })

        self.sidebar.set_reviews(due_rows, later_rows)
        self.review_badge.setText(f"На повторення: {len(due_rows)}")

    def _refresh_stats(self) -> None:
        rows = self.db.task_results()
        xp = self.db.total_xp()
        streak = self.db.streak()
        self.sidebar.set_stats(
            overall(rows), weak_topics(rows), self.db.attempts_per_day(), xp, streak
        )
        self.xp_badge.setText(f"XP {xp}")
        self.streak_badge.setText(
            f"Серія: {streak} дн." if streak != 1 else "Серія: 1 день"
        )

    def _load_history(self, task_id: str) -> None:
        self.panel.set_history(
            self.db.history(task_id),
            solved=self.db.status(task_id) == "done",
            best_xp=self.db.best_xp(task_id),
            hints_used=self.db.hints_used(task_id),
            active_seconds=self.db.active_seconds(task_id),
        )

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
        QMessageBox.information(
            self, "Гарячі клавіші",
            "Ctrl+Enter — запустити код\n"
            "F5 — перевірити прихованими тестами\n"
            "Ctrl+N — наступна незавершена задача\n"
            "Ctrl+R — черга повторень\n"
            "Ctrl+P — прогрес і слабкі місця\n"
            "Tab / Shift+Tab — відступ / зменшити відступ\n"
            "Ctrl+S — зберегти код у файл\n"
            "F1 — ця довідка",
        )

    def show_about(self) -> None:
        QMessageBox.information(
            self, "Про тренажер",
            "PyTrainer — тренажер Python з перевіркою коду.\n\n"
            "Твій код виконується в окремому процесі Python із таймаутом 5 с, "
            "тому навіть while True не зашкодить програмі.\n\n"
            "Прогрес, XP, підказки й черга повторень зберігаються в SQLite "
            f"({Path(self.db.path).name}).\n"
            "Роадмап Python-Roadmap.md генерується з цього ж плану — галочки "
            "ставляться самі.",
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_current_code()
        self.rewrite_roadmap(silent=True)
        self.db.close()
        super().closeEvent(event)
