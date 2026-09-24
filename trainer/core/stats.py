"""Статистика по темах: де ти вже впевнений, а де провалюєшся.

Мета цього модуля — не «показати красиві цифри», а знайти теми, які треба
повторити. Тому головна функція тут — weak_topics().
"""

from __future__ import annotations

from dataclasses import dataclass

from curriculum import study_tasks, topic_of

# Тема вважається слабкою, якщо є достатньо спроб і низький відсоток успіху
WEAK_MIN_ATTEMPTS = 3
WEAK_MAX_RATE = 0.6


@dataclass
class TopicStat:
    """Успішність однієї теми."""

    name: str
    done: int = 0
    total: int = 0
    attempts: int = 0
    passes: int = 0
    hints: int = 0

    @property
    def success_rate(self) -> float:
        """Частка успішних спроб (1.0 — усе з першого разу)."""
        return self.passes / self.attempts if self.attempts else 1.0

    @property
    def completion(self) -> float:
        return self.done / self.total if self.total else 0.0

    @property
    def is_weak(self) -> bool:
        return self.attempts >= WEAK_MIN_ATTEMPTS and self.success_rate < WEAK_MAX_RATE


def topic_stats(rows) -> list[TopicStat]:
    """Складає статистику по темах із рядків бази даних."""
    stats: dict[str, TopicStat] = {}

    for task in study_tasks():
        name = topic_of(task.id)
        entry = stats.setdefault(name, TopicStat(name=name))
        entry.total += 1

    for row in rows:
        name = topic_of(row["task_id"])
        entry = stats.setdefault(name, TopicStat(name=name))
        if row["status"] == "done":
            entry.done += 1
        entry.attempts += int(row["attempts"] or 0)
        entry.passes += int(row["passes"] or 0)
        entry.hints += int(row["hints_used"] or 0)

    return sorted(stats.values(), key=lambda item: item.name)


def weak_topics(rows) -> list[TopicStat]:
    """Теми, які варто повторити: багато спроб і мало успіху."""
    weak = [stat for stat in topic_stats(rows) if stat.is_weak]
    return sorted(weak, key=lambda item: item.success_rate)


def overall(rows) -> dict:
    """Загальні цифри для верхніх карток статистики.

    Ключова різниця: «здано» — це задача, яку ти вже розв'язав, а «утримано» —
    та, що більше не потребує повторень. Друга цифра чесніша щодо знань.
    """
    tasks = topic_stats(rows)
    ready_ids = {task.id for task in study_tasks()}
    done = sum(stat.done for stat in tasks)
    total = sum(stat.total for stat in tasks)
    attempts = sum(stat.attempts for stat in tasks)
    passes = sum(stat.passes for stat in tasks)
    mastered = sum(
        1
        for row in rows
        if row["status"] == "done"
        and row["task_id"] in ready_ids
        and row["due_date"] is None
    )
    return {
        "done": done,
        "total": total,
        "mastered": mastered,
        "attempts": attempts,
        "passes": passes,
        "success_rate": passes / attempts if attempts else 0.0,
        "hints": sum(stat.hints for stat in tasks),
    }
