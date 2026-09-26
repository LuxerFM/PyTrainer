"""Per-topic stats: where you are already confident and where you fail.

This module's goal is not "pretty numbers" but finding topics to repeat.
So the main function here is weak_topics().
"""

from __future__ import annotations

from dataclasses import dataclass

from curriculum import study_tasks, topic_of

# A topic counts as weak with enough attempts and a low pass rate
WEAK_MIN_ATTEMPTS = 3
WEAK_MAX_RATE = 0.6


@dataclass
class TopicStat:
    """One topic's pass rate."""

    name: str
    done: int = 0
    total: int = 0
    attempts: int = 0
    passes: int = 0
    hints: int = 0

    @property
    def success_rate(self) -> float:
        """Share of passed attempts (1.0 — everything first try)."""
        return self.passes / self.attempts if self.attempts else 1.0

    @property
    def completion(self) -> float:
        return self.done / self.total if self.total else 0.0

    @property
    def is_weak(self) -> bool:
        return self.attempts >= WEAK_MIN_ATTEMPTS and self.success_rate < WEAK_MAX_RATE


def topic_stats(rows) -> list[TopicStat]:
    """Builds per-topic stats from database rows."""
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
    """Topics worth repeating: many attempts, little success."""
    weak = [stat for stat in topic_stats(rows) if stat.is_weak]
    return sorted(weak, key=lambda item: item.success_rate)


def overall(rows) -> dict:
    """Totals for the top stats cards.

    The key difference: "passed" is a task you already solved, while
    "retained" needs no more reviews. The second number is more honest about
    knowledge.
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
