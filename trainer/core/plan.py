"""Today's plan: exactly what to do in these 1.5–2 hours.

The biggest decision killing learning every day is "where to start?". So
instead of a 47-task list the trainer composes a short order of actions:

1. **Reviews** — what is about to be forgotten. Always first, otherwise the
   queue grows and knowledge evaporates.
2. **Weak topic** — if stats already see failures, finish them off.
3. **New task** — further down the plan while time remains.

The module knows neither Qt nor calendar scheduling: a pure function from the
database to a step list, so tests cover it easily.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from curriculum import find_task, study_tasks, topic_of

from .stats import weak_topics

# Minutes in a typical roadmap-plan day (1.5–2 hours)
DEFAULT_BUDGET = 100
REVIEW_MINUTES = 8
MAX_REVIEWS = 4


@dataclass
class PlanStep:
    """One plan step: what to do and why exactly this."""

    kind: str                  # review | weak | new
    title: str
    reason: str
    minutes: int = 10
    task_id: str | None = None
    topic: str = ""
    done: bool = False


@dataclass
class DailyPlan:
    """One day's plan + summary."""

    steps: list[PlanStep] = field(default_factory=list)
    budget: int = DEFAULT_BUDGET

    @property
    def minutes(self) -> int:
        return sum(step.minutes for step in self.steps)

    @property
    def empty(self) -> bool:
        return not self.steps

    def as_lines(self) -> list[str]:
        """Short text view — for the console and tests."""
        return [
            f"{index}. [{step.kind}] {step.title} · ~{step.minutes} хв — {step.reason}"
            for index, step in enumerate(self.steps, start=1)
        ]


def daily_plan(db, *, budget: int = DEFAULT_BUDGET) -> DailyPlan:
    """Composes the day's plan from what is already in the database.

    Step order: reviews → weak topic → new tasks. Time is budget-capped, so
    the plan is always doable in one evening.
    """
    plan = DailyPlan(budget=budget)
    statuses = db.statuses()
    left = budget

    # 1. Reviews already due
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

    # 2. Weak topic with an unpassed task
    weak = pick_weak_task(db, statuses)
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

    # 3. New tasks down the plan, while time remains
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


def pick_weak_task(db, statuses):
    """First unpassed task of the weakest topic (None if there is none)."""
    weak = weak_topics(db.task_results())
    by_topic: dict[str, list] = {}
    for task in study_tasks():
        by_topic.setdefault(topic_of(task.id), []).append(task)

    for stat in weak:
        for task in by_topic.get(stat.name, []):
            if statuses.get(task.id) != "done":
                return task, stat.name, stat.success_rate
    return None


__all__ = ["DailyPlan", "PlanStep", "daily_plan", "DEFAULT_BUDGET",
           "pick_weak_task"]
