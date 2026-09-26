"""Правила навчання в одному місці — без єдиного рядка Qt.

Тут вирішується все, що стосується прогресу: здано чи ні, скільки XP,
чи йти задачі в чергу повторень, чи задача «утримана» і що саме показати
людині. Інтерфейс лише викликає ці методи й малює результат.

Завдяки цьому правила можна перевіряти тестами без вікна, а той самий код
можна використати в командному рядку або в майбутній вебверсії.
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
    """Що змінилося після спроби — усе, що потрібно інтерфейсу, щоб оновити екран."""

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
    """Одна навчальна сесія: читання плану + запис результатів у базу."""

    def __init__(self, db: Database, lookup=find_task) -> None:
        self.db = db
        self._lookup = lookup

    # ------------------------------------------------------------------
    # запитання до стану
    # ------------------------------------------------------------------

    def task(self, task_id: str) -> Task | None:
        return self._lookup(task_id)

    def preview_xp(self, task: Task) -> int:
        """Скільки XP дасть задача зараз, з урахуванням підказок і спроб."""
        return scoring.xp_for(
            task,
            hints_used=self.db.hints_used(task.id),
            first_time=self.db.status(task.id) != "done",
            solution_used=self.db.solution_used(task.id),
        )

    def is_mastered(self, task_id: str) -> bool:
        """Утримано: задача здана й більше не потребує повторень."""
        return (
            self.db.status(task_id) == "done" and self.db.review(task_id) is None
        )

    def summary(self) -> dict:
        """Цифри для екрана прогресу."""
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
    # підказки й ручні пункти
    # ------------------------------------------------------------------

    def record_hint(self, task: Task, level: int, is_solution: bool) -> int:
        """Фіксує відкриту підказку. Повертає новий прогноз XP."""
        self.db.reveal_hint(task.id, level, is_solution)
        return self.preview_xp(task)

    def use_solution(self, task: Task) -> int:
        """Людина вставила розв'язок у редактор — це найдорожча підказка."""
        self.db.mark_solution_used(task.id)
        return self.preview_xp(task)

    def mark_manual_done(self, task: Task, xp: int = 0) -> None:
        """Пункт, зроблений поза тренажером (venv, Git, pytest): ставимо галочку."""
        self.db.mark_solved(task.id, xp)

    # ------------------------------------------------------------------
    # головне: запис результату спроби
    # ------------------------------------------------------------------

    def record_result(
        self, task: Task, result: RunResult, *, review_mode: bool = False
    ) -> StudyUpdate | None:
        """Записує результат перевірки й повертає все, що змінилось.

        None означає, що це був звичайний запуск без перевірок — прогрес не чіпаємо.
        """
        if not result.ran_checks:
            self.db.record_attempt(task.id, ok=False, with_checks=False)
            return None

        update = StudyUpdate(task_id=task.id, passed=result.all_passed)
        solved_before = self.db.status(task.id) == "done"
        update.first_try = not solved_before
        xp = self.preview_xp(task)

        # «Чисто» — здано без підказок і без вставленого розв'язку. За цією
        # ознакою журнал помилок вирішує, що закрито по-справжньому.
        clean = (
            result.all_passed
            and self.db.hints_used(task.id) == 0
            and not self.db.solution_used(task.id)
        )

        # Пишемо в журнал не лише «не здав», а й на чому саме спіткнувся —
        # з цього потім складається список «твої помилки».
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
        """Оновлює чергу повторень і нараховує XP за повторення."""
        if review_mode:
            previous = self.db.review(task.id)
            if previous is None:
                # Задача вже поза чергою (утримана). Успішне холодне згадування
                # не повертає її в розклад — інакше «утримано» ламалося б від
                # кожного тренування — лише дає найщедріший бонус, як за
                # найдовший витриманий інтервал.
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
