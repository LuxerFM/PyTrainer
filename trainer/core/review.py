"""Холодне повторення: випадкова вже здана задача — без підказок і розв'язку.

Найдешевший спосіб обманути себе — упізнати власний код. Коли задача вже
здана, її розв'язок лежить у редакторі, підказки відкриті, і здається, що
ти все пам'ятаєш. Користь дає протилежне: дістати рішення з пам'яті без
опори. Тому цей режим бере випадкову здану задачу, ховає підказки й розв'язок
і обмежує час.

Черговість проста: спершу те, що вже просить повторення (воно от-от
забудеться), а якщо черга порожня — будь-яка здана задача: несподівана
згадка тримає знання краще, ніж ще один перегляд знайомого розв'язку.

Модуль не знає ні про Qt, ні про SQLite: йому достатньо методів `statuses()`
і `due_reviews()`. Тому вибір легко перевіряти тестами без вікна.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from curriculum import study_tasks
from curriculum.schema import Task

# Скільки хвилин дається на холодне згадування
COLD_MINUTES = 10
# …але коротша задача має дістати хоч трохи часу на роздуми
MIN_COLD_MINUTES = 3


@dataclass(frozen=True)
class ColdReview:
    """Що саме дістали з пам'яті, звідки воно взялось і скільки на нього часу."""

    task: Task
    from_queue: bool = False
    seconds: int = COLD_MINUTES * 60

    @property
    def minutes(self) -> int:
        return max(1, round(self.seconds / 60))


def solved_tasks(db, *, exclude: str | None = None) -> list[Task]:
    """Здані задачі, які має сенс згадувати.

    Пункти поза тренажером (venv, Git, pytest) не рахуються: у них немає ні
    коду, ні перевірок — згадувати там нічого.
    """
    statuses = db.statuses()
    return [
        task
        for task in study_tasks()
        if statuses.get(task.id) == "done" and task.id != exclude
    ]


def due_tasks(db, *, exclude: str | None = None) -> list[Task]:
    """Здані задачі, які вже час повторити."""
    due_ids = {row["task_id"] for row in db.due_reviews()}
    return [task for task in solved_tasks(db, exclude=exclude) if task.id in due_ids]


def cold_seconds(task: Task) -> int:
    """Скільки секунд дається на холодне згадування.

    Не більше COLD_MINUTES: у незнайомій роботі легко просидіти годину, а
    користь від цього не росте. Не менше MIN_COLD_MINUTES: навіть на просту
    задачу треба час, щоб зібратися з думками.
    """
    minutes = min(COLD_MINUTES, max(MIN_COLD_MINUTES, task.minutes))
    return minutes * 60


def pick_cold_task(db, *, exclude: str | None = None,
                   rng: random.Random | None = None) -> ColdReview | None:
    """Вибирає задачу для холодного повторення (None — якщо зданих немає).

    `exclude` — id задачі, яка зараз відкрита: повторювати те, що перед
    очима, немає сенсу. `rng` передають тести, щоб вибір був передбачуваним.
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
