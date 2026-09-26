"""Learning rules: XP, review schedule and day streak.

Only dry functions here, no database and no UI — so tests cover them easily
and they change without touching the rest of the app.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

# How much XP each opened hint "eats"
HINT_PENALTY = 0.15
# Floor: even with all hints a task grants some XP
MIN_FACTOR = 0.4
# Re-passing a task grants only part of the XP
REPEAT_FACTOR = 0.3
# Review schedule in days: 1 → 3 → 7 → 30 (then the task counts as retained)
INTERVALS = (1, 3, 7, 30)

# How many "hints" a full-solution use counts as
SOLUTION_HINT_LEVELS = 3

# How much of base XP one successful review grants (times interval depth)
REVIEW_BONUS_RATE = 0.2


class HasBaseXp(Protocol):
    """The minimum we need from a task."""

    base_xp: int


def xp_for(
    task: HasBaseXp,
    *,
    hints_used: int = 0,
    first_time: bool = True,
    solution_used: bool = False,
) -> int:
    """How much XP a passed task grants.

    Using the full solution counts as at least SOLUTION_HINT_LEVELS hints —
    otherwise a pasted solution would cost as much XP as working alone.
    """
    effective = max(hints_used, SOLUTION_HINT_LEVELS) if solution_used else hints_used
    factor = max(MIN_FACTOR, 1 - HINT_PENALTY * effective)
    if not first_time:
        factor *= REPEAT_FACTOR
    return int(round(task.base_xp * factor / 5) * 5)


def review_xp(
    task: HasBaseXp,
    *,
    interval_index: int = 0,
    hints_used: int = 0,
    solution_used: bool = False,
) -> int:
    """XP for re-passing a task.

    The longer the survived interval, the more recall is worth: the first
    review grants 20% of base XP, the second 40%, the third 60%, the fourth
    80%. Without this, reviewing would pay worse than running ahead.
    """
    effective = max(hints_used, SOLUTION_HINT_LEVELS) if solution_used else hints_used
    factor = max(MIN_FACTOR, 1 - HINT_PENALTY * effective)
    depth = min(1.0, REVIEW_BONUS_RATE * (max(0, interval_index) + 1))
    return int(round(task.base_xp * depth * factor / 5) * 5)


def next_interval(index: int, ok: bool) -> tuple[int, int | None]:
    """Next review interval.

    Returns (new_index, days_until_review). Days = None means the task is
    retained and leaves the review queue.
    """
    if not ok:
        return 0, INTERVALS[0]
    new_index = index + 1
    if new_index >= len(INTERVALS):
        return new_index, None
    return new_index, INTERVALS[new_index]


def needs_review(*, solved: bool, attempts: int, solution_used: bool = False) -> bool:
    """Whether the task should return to review."""
    if not solved:
        return True
    if attempts > 1:
        return True
    return solution_used


def due_date(days: int, today: date | None = None) -> str:
    today = today or date.today()
    return (today + timedelta(days=days)).isoformat()


def streak_from_days(days: list[str], today: date | None = None) -> int:
    """Streak of active days in a row.

    Today counts if there was activity already; if not, the streak counts
    from yesterday so it does not "burn out" before evening.
    """
    today = today or date.today()
    unique = sorted({date.fromisoformat(day) for day in days}, reverse=True)
    if not unique:
        return 0

    if unique[0] == today:
        cursor = today
    elif unique[0] == today - timedelta(days=1):
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    for day in unique:
        if day == cursor:
            streak += 1
            cursor -= timedelta(days=1)
        elif day < cursor:
            break
    return streak
