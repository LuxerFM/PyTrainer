"""Learning rules in one place — without a single line of Qt.

Everything about progress is decided here: passed or not, how much XP,
whether the task joins the review queue, whether it is "retained" and what
exactly to show the human. The UI only calls these methods and draws the
result.

So the rules are testable without a window, and the same code can drive a
command line or a future web version.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from curriculum import find_task, study_tasks
from curriculum.schema import Task

from . import scoring
from .db import Database
from .runner import RunResult


@dataclass
class StudyUpdate:
    """What changed after the attempt — everything the UI needs to redraw."""

    task_id: str
    passed: bool = False
    first_try: bool = False
    xp: int = 0
    bonus_xp: int = 0
    status: str = "todo"
    review_days: int | None = None
    review_index: int = 0
    mastered: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def total_xp(self) -> int:
        return self.xp + self.bonus_xp


class StudySession:
    """One study session: reading the plan + writing results to the database."""

    def __init__(self, db: Database, lookup=find_task) -> None:
        self.db = db
        self._lookup = lookup

    # ------------------------------------------------------------------
    # state questions
    # ------------------------------------------------------------------

    def task(self, task_id: str) -> Task | None:
        return self._lookup(task_id)

    def preview_xp(self, task: Task) -> int:
        """How much XP the task grants now, given hints and attempts."""
        return scoring.xp_for(
            task,
            hints_used=self.db.hints_used(task.id),
            first_time=self.db.status(task.id) != "done",
            solution_used=self.db.solution_used(task.id),
        )

    def is_mastered(self, task_id: str) -> bool:
        """Retained: the task is passed and needs no more reviews."""
        return (
            self.db.status(task_id) == "done" and self.db.review(task_id) is None
        )

    def summary(self) -> dict:
        """Numbers for the progress screen."""
        ready = study_tasks()
        rows = self.db.task_results()
        done_rows = [row for row in rows if row["status"] == "done"]
        mastered = sum(
            1 for row in done_rows
            if row["due_date"] is None and row["task_id"] in {t.id for t in ready}
        )
        return {
            "total": len(ready),
            "done": len(done_rows),
            "mastered": mastered,
            "xp": self.db.total_xp(),
            "streak": self.db.streak(),
        }

    # ------------------------------------------------------------------
    # hints and manual items
    # ------------------------------------------------------------------

    def record_hint(self, task: Task, level: int, is_solution: bool) -> int:
        """Records an opened hint. Returns the new XP forecast."""
        self.db.reveal_hint(task.id, level, is_solution)
        return self.preview_xp(task)

    def use_solution(self, task: Task) -> int:
        """The human pasted the solution into the editor — the priciest hint."""
        self.db.mark_solution_used(task.id)
        return self.preview_xp(task)

    def mark_manual_done(self, task: Task, xp: int = 0) -> None:
        """Item done outside the trainer (venv, Git, pytest): tick it."""
        self.db.mark_solved(task.id, xp)

    # ------------------------------------------------------------------
    # the main thing: recording an attempt's result
    # ------------------------------------------------------------------

    def record_result(
        self, task: Task, result: RunResult, *, review_mode: bool = False
    ) -> StudyUpdate | None:
        """Records the check result and returns everything that changed.

        None means a plain run with no checks — progress untouched.
        """
        if not result.ran_checks:
            self.db.record_attempt(task.id, ok=False, with_checks=False)
            return None

        update = StudyUpdate(task_id=task.id, passed=result.all_passed)
        solved_before = self.db.status(task.id) == "done"
        update.first_try = not solved_before
        xp = self.preview_xp(task)

        # "Clean" — passed with no hints and no pasted solution. The mistake
        # journal uses this flag to decide what is truly closed.
        clean = (
            result.all_passed
            and self.db.hints_used(task.id) == 0
            and not self.db.solution_used(task.id)
        )

        # The journal records not just "failed" but what exactly tripped —
        # that later becomes the "your mistakes" list.
        self.db.record_attempt(
            task.id,
            ok=result.all_passed,
            with_checks=True,
            xp=xp if result.all_passed else 0,
            failed_check=result.first_failed_check,
            error_kind=result.failure_kind,
            clean=clean,
        )

        if result.all_passed:
            if solved_before:
                self.db.mark_repeat_passed(task.id, xp)
                update.notes.append("повторне здавання")
            else:
                self.db.mark_solved(task.id, xp)
            update.xp = xp
            self._handle_success(task, update, solved_before, review_mode)
        else:
            self.db.schedule_from_result(task.id, False)
            update.notes.append("у черзі повторень — спробуй ще раз")

        update.status = self.db.status(task.id)
        update.mastered = self.is_mastered(task.id)
        update.preview_xp = self.preview_xp(task)
        return update

    def _handle_success(
        self, task: Task, update: StudyUpdate, solved_before: bool, review_mode: bool
    ) -> None:
        """Updates the review queue and grants review XP."""
        if review_mode:
            previous = self.db.review(task.id)
            if previous is None:
                # Task already out of the queue (retained). A successful cold
                # recall does not put it back on schedule — otherwise
                # "retained" would break on every training — it only grants
                # the most generous bonus, as for the longest survived
                # interval.
                depth = len(scoring.INTERVALS) - 1
                days = None
                update.review_index = 0
            else:
                depth = max(0, previous["interval_index"])
                index, days = self.db.schedule_from_result(task.id, True)
                update.review_index = index
            update.review_days = days

            bonus = scoring.review_xp(
                task,
                interval_index=depth,
                hints_used=self.db.hints_used(task.id),
                solution_used=self.db.solution_used(task.id),
            )
            self.db.add_bonus_xp(task.id, bonus)
            update.bonus_xp = bonus
            if previous is None:
                update.notes.append("задачу вже утримано — черга не змінилась")
            elif days is None:
                update.notes.append("усі повторення пройдено — задачу засвоєно")
            else:
                update.notes.append(f"наступне повторення через {days} дн.")
            return

        attempts = max(1, self.db.attempts_count(task.id))
        if solved_before or scoring.needs_review(
            solved=True,
            attempts=attempts,
            solution_used=self.db.solution_used(task.id),
        ):
            index, days = self.db.schedule_from_result(task.id, False)
            update.review_index = index
            update.review_days = days
            update.notes.append("задачу додано в чергу повторень")
        else:
            self.db.clear_review(task.id)
            update.notes.append("здано чисто — повторення не потрібні")
