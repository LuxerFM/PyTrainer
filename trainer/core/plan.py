"""План на сьогодні: що конкретно робити за ці 1,5–2 години.

Найбільше рішення, яке щодня вбиває навчання, — «з чого почати?». Тому замість
списку з 47 задач тренажер складає короткий порядок дій:

1. **Повторення** — те, що ось-ось забудеться. Це завжди перше, бо інакше
   черга росте, а знання вивітрюються.
2. **Слабка тема** — якщо статистика вже бачить провали, добиваємо їх.
3. **Нова задача** — далі за планом, поки не вичерпано час.

Модуль не знає ні про Qt, ні про планування в календарі: це чиста функція від
бази до списку кроків, тому її легко перевіряти тестами.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from curriculum import find_task, study_tasks, topic_of

from .stats import weak_topics

# Скільки хвилин у типовому дні за планом роадмапу (1,5–2 години)
DEFAULT_BUDGET = 100
REVIEW_MINUTES = 8
MAX_REVIEWS = 4


@dataclass
class PlanStep:
    """Один крок плану: що робити і чому саме це."""

    kind: str                  # review | weak | new
    title: str
    reason: str
    minutes: int = 10
    task_id: str | None = None
    topic: str = ""
    done: bool = False


@dataclass
class DailyPlan:
    """План на один день + підсумок."""

    steps: list[PlanStep] = field(default_factory=list)
    budget: int = DEFAULT_BUDGET

    @property
    def minutes(self) -> int:
        return sum(step.minutes for step in self.steps)

    @property
    def empty(self) -> bool:
        return not self.steps

    def as_lines(self) -> list[str]:
        """Короткий текстовий вигляд — для консолі й тестів."""
        return [
            f"{index}. [{step.kind}] {step.title} · ~{step.minutes} хв — {step.reason}"
            for index, step in enumerate(self.steps, start=1)
        ]


def daily_plan(db, *, budget: int = DEFAULT_BUDGET) -> DailyPlan:
    """Складає план на день із того, що вже є в базі.

    Порядок кроків: повторення → слабка тема → нові задачі. Час обмежений
    бюджетом, тому план завжди реально виконати за один вечір.
    """
    plan = DailyPlan(budget=budget)
    statuses = db.statuses()
    left = budget

    # 1. Повторення, які вже час зробити
    for row in db.due_reviews()[:MAX_REVIEWS]:
        task = find_task(row["task_id"])
        if task is None or task.stub:
            continue
        when = "прострочено" if row["due_date"] < date.today().isoformat() \
            else "сьогодні"
        plan.steps.append(PlanStep(
            kind="review",
            title=task.title,
            reason=f"черга повторень · {when}",
            minutes=REVIEW_MINUTES,
            task_id=task.id,
            topic=topic_of(task.id),
        ))
        left -= REVIEW_MINUTES

    # 2. Слабка тема, у якій є незадана задача
    weak = _pick_weak_task(db, statuses)
    if weak is not None and left > 10:
        task, topic_name, rate = weak
        plan.steps.append(PlanStep(
            kind="weak",
            title=task.title,
            reason=f"слабка тема «{topic_name}» · успішних спроб "
                   f"{round(rate * 100)}%",
            minutes=max(10, task.minutes),
            task_id=task.id,
            topic=topic_name,
        ))
        left -= max(10, task.minutes)

    # 3. Нові задачі за планом, поки є час
    for task in study_tasks():
        if left <= 8:
            break
        if statuses.get(task.id) == "done":
            continue
        if any(step.task_id == task.id for step in plan.steps):
            continue
        plan.steps.append(PlanStep(
            kind="new",
            title=task.title,
            reason=f"нова задача · {topic_of(task.id)}",
            minutes=task.minutes,
            task_id=task.id,
            topic=topic_of(task.id),
        ))
        left -= task.minutes

    return plan


def _pick_weak_task(db, statuses):
    """Перша незадана задача з найслабшої теми (None, якщо таких немає)."""
    weak = weak_topics(db.task_results())
    by_topic: dict[str, list] = {}
    for task in study_tasks():
        by_topic.setdefault(topic_of(task.id), []).append(task)

    for stat in weak:
        for task in by_topic.get(stat.name, []):
            if statuses.get(task.id) != "done":
                return task, stat.name, stat.success_rate
    return None


__all__ = ["DailyPlan", "PlanStep", "daily_plan", "DEFAULT_BUDGET"]
