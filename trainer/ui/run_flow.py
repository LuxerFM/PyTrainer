"""Running code: thread, verdict, drawing the result.

Extracted from `MainWindow` (split slice 2). The controller holds a pointer
to the window (`w`) — state (`_running`, `_task`, cold-review timer) stays in
the window, since other controllers touch it too.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication

from ..core.runner import RunResult, run_task
from ..core.session import StudyUpdate
from .theme import Colors

if TYPE_CHECKING:
    from .main_window import MainWindow


def _tr(text: str) -> str:
    return QCoreApplication.translate("RunFlow", text)


class RunFlow:
    """Code runs and verdict handling."""

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
            # In cold review the editor holds the stub, and writing it to
            # the database would erase the real solution.
            w.db.save_code(task.id, code)
        w._last_saved = code
        checks = list(task.checks) if with_checks else []

        w._running = True
        w._set_run_enabled(False)
        w.console.clear()

        label = _tr("Перевірка тестами") if with_checks else _tr("Запуск коду")
        w._log(f"{label}…", Colors.muted)
        if task.stdin:
            w._log(_tr("→ Ввід: {stdin}").format(
                stdin=' / '.join(task.stdin.splitlines())), Colors.muted)
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
            w._log(_tr("(вивід порожній)"), Colors.muted)
        if result.output_truncated:
            w._log(_tr("…вивід обрізано, щоб не з'їсти пам'ять"), Colors.warn)

        advice = result.advice
        if advice:
            w._log("", Colors.muted)
            for line in advice.splitlines():
                w._log(line, Colors.warn)

        w.panel.show_result(result, bool(result.ran_checks))

        if w._task is None:
            return

        # Code review shows after every run: the verdict said the code does
        # not work, and the review — what it does to a reader's eyes.
        w._refresh_review(announce=result.ran_checks and result.all_passed)
        task = w._task

        if not result.ran_checks:
            w.status_msg.setText(_tr("Код виконано"))
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
        """Draws what the core decided: XP, status, review queue."""
        w = self.w
        if update.passed:
            w.sidebar.mark(task.id, "done")
            parts = [_tr("Задача здана! +{xp} XP").format(xp=update.xp)]
            if update.bonus_xp:
                parts.append(_tr("бонус за повторення +{xp} XP").format(
                    xp=update.bonus_xp))
            w._log(_tr("Усі перевірки пройдено · {parts}").format(
                parts=" · ".join(parts)), Colors.success)
            for note in update.notes:
                w._log(f"» {note}", Colors.muted if "повторення" in note else Colors.warn)
            if cold:
                w._log(_tr("❄ Холодне повторення: згадав без підказок ✓"),
                       Colors.success)
            if update.mastered:
                w._log(_tr("Задача утримана — більше не в черзі повторень 🎯"),
                       Colors.success)
            w.status_msg.setText(parts[0])
        else:
            w.sidebar.mark(task.id, "current")
            w._log(_tr("Пройдено {passed} із {total}").format(
                passed=result.passed_count, total=len(result.checks)),
                Colors.warn)
            for note in update.notes:
                w._log(f"» {note}", Colors.muted)
            if cold:
                w._log(
                    _tr("❄ Холодне повторення: не згадав — задача повернеться в "
                        "чергу. Це нормально: саме такі прогалини й ловляться."),
                    Colors.warn,
                )
            w.status_msg.setText(_tr("Є помилки — дивись вкладку «Тести»"))


__all__ = ["RunFlow"]
