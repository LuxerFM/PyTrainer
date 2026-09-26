"""Cold review: a random already-passed task — no hints, no solution.

The cheapest way to fool yourself is recognising your own code. Once a task is
passed, its solution sits in the editor, hints are open, and it feels like you
remember everything. The opposite pays off: pulling the solution from memory
with no support. So this mode takes a random passed task, hides hints and
solution, and caps the time.

The order is simple: first what already asks for review (it is about to be
forgotten), and if the queue is empty — any passed task: a surprise recall
holds knowledge better than one more look at a familiar solution.

The module knows neither Qt nor SQLite: `statuses()` and `due_reviews()`
methods are enough. So the choice is easy to test without a window.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from curriculum import study_tasks
from curriculum.schema import Task

# Minutes granted for a cold recall
COLD_MINUTES = 10
# …but a shorter task still deserves some thinking time
MIN_COLD_MINUTES = 3


@dataclass(frozen=True)
class ColdReview:
    """What exactly was recalled, where it came from and how much time it gets."""

    task: Task
    from_queue: bool = False
    seconds: int = COLD_MINUTES * 60

    @property
    def minutes(self) -> int:
        return max(1, round(self.seconds / 60))


def solved_tasks(db, *, exclude: str | None = None) -> list[Task]:
    """Passed tasks worth recalling.

    Off-trainer items (venv, Git, pytest) do not count: they have neither
    code nor checks — nothing to recall there.
    """
    statuses = db.statuses()
    return [
        task
        for task in study_tasks()
        if statuses.get(task.id) == "done" and task.id != exclude
    ]


def due_tasks(db, *, exclude: str | None = None) -> list[Task]:
    """Passed tasks already due for review."""
    due_ids = {row["task_id"] for row in db.due_reviews()}
    return [task for task in solved_tasks(db, exclude=exclude) if task.id in due_ids]


def cold_seconds(task: Task) -> int:
    """How many seconds a cold recall gets.

    At most COLD_MINUTES: in unfamiliar work it is easy to sit an hour, and
    the benefit does not grow. At least MIN_COLD_MINUTES: even a simple task
    needs time to collect your thoughts.
    """
    minutes = min(COLD_MINUTES, max(MIN_COLD_MINUTES, task.minutes))
    return minutes * 60


def pick_cold_task(db, *, exclude: str | None = None,
                   rng: random.Random | None = None) -> ColdReview | None:
    """Picks a cold-review task (None — if nothing is passed).

    `exclude` — id of the currently open task: repeating what is before your
    eyes makes no sense. Tests pass `rng` so the pick is predictable.
    """
    rng = rng or random.Random()
    due = due_tasks(db, exclude=exclude)
    pool = due or solved_tasks(db, exclude=exclude)
    if not pool:
        return None

    task = rng.choice(pool)
    return ColdReview(task=task, from_queue=bool(due), seconds=cold_seconds(task))


__all__ = [
    "COLD_MINUTES",
    "MIN_COLD_MINUTES",
    "ColdReview",
    "cold_seconds",
    "due_tasks",
    "pick_cold_task",
    "solved_tasks",
]
