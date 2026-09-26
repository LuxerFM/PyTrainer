"""Запуск коду: потік, вердикт, малювання результату.

Витягнуто з `MainWindow` (зріз 2 розпилу). Контролер тримає вказівник на
вікно (`w`) — стан (`_running`, `_task`, таймер холодного повторення)
лишається у вікні, бо його чіпають і інші контролери.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ..core.runner import RunResult, run_task
from ..core.session import StudyUpdate
from .theme import Colors

if TYPE_CHECKING:
    from .main_window import MainWindow


class RunFlow:
    """Запуск коду й обробка вердикту."""

    def __init__(self, window: MainWindow) -> None:
        self.w = window

    def run_code_only(self) -> None:
        self.start_run(with_checks=False)

    def run_checks(self) -> None:
        self.start_run(with_checks=True)

    def start_run(self, with_checks: bool) -> None:
        w = self.w
        if w._running or w._task is None:
            return

        task = w._task
        code = w.editor.toPlainText()
        if not w._review_mode:
            # У холодному повторенні в редакторі лежить заготовка, і записати
            # її в базу означало б стерти справжній розв'язок.
            w.db.save_code(task.id, code)
        w._last_saved = code
        checks = list(task.checks) if with_checks else []

        w._running = True
        w._set_run_enabled(False)
        w.console.clear()

        label = "Перевірка тестами" if with_checks else "Запуск коду"
        w._log(f"{label}…", Colors.muted)
        if task.stdin:
            w._log(f"→ Ввід: {' / '.join(task.stdin.splitlines())}", Colors.muted)
        w.status_msg.setText(f"{label}…")

        threading.Thread(
            target=self.run_in_thread, args=(task, code, checks), daemon=True
        ).start()

    def run_in_thread(self, task, code: str, checks) -> None:
        self.w.run_finished.emit(run_task(task, code, checks))

    def on_run_finished(self, result: RunResult) -> None:
        w = self.w
        w._running = False
        w._set_run_enabled(True)

        if result.stdout:
            w._log(result.stdout, Colors.text)
        if result.stderr:
            w._log(result.stderr, Colors.error)
        if not result.stdout and not result.stderr:
            w._log("(вивід порожній)", Colors.muted)
        if result.output_truncated:
            w._log("…вивід обрізано, щоб не з'їсти пам'ять", Colors.warn)

        advice = result.advice
        if advice:
            w._log("", Colors.muted)
            for line in advice.splitlines():
                w._log(line, Colors.warn)

        w.panel.show_result(result, bool(result.ran_checks))

        if w._task is None:
            return

        # Розбір коду показуємо після кожного запуску: вердикт сказав, що код
        # не працює, а розбір — що він робить із очима читача.
        w._refresh_review(announce=result.ran_checks and result.all_passed)
        task = w._task

        if not result.ran_checks:
            w.status_msg.setText("Код виконано")
            w._load_history(task.id)
            w._refresh_stats()
            return

        cold = w._review_mode
        update = w.session.record_result(task, result, review_mode=cold)

        if update is None:
            return
        self.render_update(update, task, result, cold=cold)
        if cold:
            w._end_cold_review()

        w._refresh_all()
        w._load_history(task.id)
        w._update_timer_label()
        w.rewrite_roadmap(silent=True)
        w._write_progress(silent=True)

    def render_update(self, update: StudyUpdate, task, result: RunResult,
                      *, cold: bool = False) -> None:
        """Малює те, що вирішило ядро: XP, статус, чергу повторень."""
        w = self.w
        if update.passed:
            w.sidebar.mark(task.id, "done")
            parts = [f"Задача здана! +{update.xp} XP"]
            if update.bonus_xp:
                parts.append(f"бонус за повторення +{update.bonus_xp} XP")
            w._log("Усі перевірки пройдено · " + " · ".join(parts), Colors.success)
            for note in update.notes:
                w._log(f"» {note}", Colors.muted if "повторення" in note else Colors.warn)
            if cold:
                w._log("❄ Холодне повторення: згадав без підказок ✓",
                       Colors.success)
            if update.mastered:
                w._log("Задача утримана — більше не в черзі повторень 🎯",
                       Colors.success)
            w.status_msg.setText(parts[0])
        else:
            w.sidebar.mark(task.id, "current")
            w._log(f"Пройдено {result.passed_count} із {len(result.checks)}",
                   Colors.warn)
            for note in update.notes:
                w._log(f"» {note}", Colors.muted)
            if cold:
                w._log(
                    "❄ Холодне повторення: не згадав — задача повернеться в "
                    "чергу. Це нормально: саме такі прогалини й ловляться.",
                    Colors.warn,
                )
            w.status_msg.setText("Є помилки — дивись вкладку «Тести»")


__all__ = ["RunFlow"]
