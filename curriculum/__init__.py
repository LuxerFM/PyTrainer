"""Навчальний план тренажера: усі місяці, теми й задачі в одному місці.

Застосунок читає план звідси, а файл Python-Roadmap.md генерується з нього —
тому галочки в роадмапі й прогрес у застосунку не можуть розійтися.
"""

from __future__ import annotations

from . import month1, month2, months34, months56, months79
from .schema import Check, Hint, Month, Task, Topic

CURRICULUM: tuple[Month, ...] = (
    month1.MONTH,
    month2.MONTH,
    months34.MONTH,
    months56.MONTH,
    months79.MONTH,
)


def months() -> tuple[Month, ...]:
    return CURRICULUM


def all_tasks() -> list[Task]:
    """Усі задачі, разом із задачами-позначками."""
    return [task for month in CURRICULUM for topic in month.topics for task in topic.tasks]


def study_tasks() -> list[Task]:
    """Лише задачі, які вже можна розв'язувати."""
    return [task for task in all_tasks() if not task.stub]


def find_task(task_id: str) -> Task | None:
    for task in all_tasks():
        if task.id == task_id:
            return task
    return None


def topic_of(task_id: str) -> str:
    """Назва теми для задачі — показується в панелі задачі."""
    for month in CURRICULUM:
        for topic in month.topics:
            if any(task.id == task_id for task in topic.tasks):
                return f"{month.title.split('·')[0].strip()} · {topic.title}"
    return ""


def first_unfinished(statuses: dict[str, str]) -> Task | None:
    """Перша задача, яку ще не здано — її й відкриваємо на старті."""
    for task in study_tasks():
        if statuses.get(task.id) != "done":
            return task
    return None


__all__ = [
    "CURRICULUM",
    "Check",
    "Hint",
    "Month",
    "Task",
    "Topic",
    "all_tasks",
    "find_task",
    "first_unfinished",
    "months",
    "study_tasks",
    "topic_of",
]
