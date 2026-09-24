"""Правила навчання: XP, розклад повторень і серія днів.

Тут тільки сухі функції без бази даних та інтерфейсу — тому їх легко
перевіряти тестами й змінювати, не чіпаючи решту застосунку.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

# Скільки XP «з'їдає» кожна відкрита підказка
HINT_PENALTY = 0.15
# Нижня межа: навіть з усіма підказками задача дає частину XP
MIN_FACTOR = 0.4
# За повторне здавання задачі — лише частина XP
REPEAT_FACTOR = 0.3
# Розклад повторень у днях: 1 → 3 → 7 → 30 (потім задача вважається засвоєною)
INTERVALS = (1, 3, 7, 30)

# Скільки «підказок» зараховуємо, якщо людина скористалась повним розв'язком
SOLUTION_HINT_LEVELS = 3

# Скільки від базового XP дає одне успішне повторення (множиться на глибину інтервалу)
REVIEW_BONUS_RATE = 0.2


class HasBaseXp(Protocol):
    """Мінімум, який нам потрібен від задачі."""

    base_xp: int


def xp_for(
    task: HasBaseXp,
    *,
    hints_used: int = 0,
    first_time: bool = True,
    solution_used: bool = False,
) -> int:
    """Скільки XP дати за здану задачу.

    Якщо людина скористалась повним розв'язком, це рахується як мінімум
    SOLUTION_HINT_LEVELS підказок — інакше вставлений розв'язок коштував би
    стільки ж XP, як самостійна робота.
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
    """XP за повторне здавання задачі.

    Чим довший інтервал витримав — тим цінніше згадати: перше повторення
    дає 20% базового XP, друге — 40%, третє — 60%, четверте — 80%.
    Без цього повторювати було б невигідно порівняно з бігом уперед.
    """
    effective = max(hints_used, SOLUTION_HINT_LEVELS) if solution_used else hints_used
    factor = max(MIN_FACTOR, 1 - HINT_PENALTY * effective)
    depth = min(1.0, REVIEW_BONUS_RATE * (max(0, interval_index) + 1))
    return int(round(task.base_xp * depth * factor / 5) * 5)


def next_interval(index: int, ok: bool) -> tuple[int, int | None]:
    """Наступний інтервал повторення.

    Повертає (новий_індекс, днів_до_повторення). Днів = None означає,
    що задача засвоєна і з черги повторень зникає.
    """
    if not ok:
        return 0, INTERVALS[0]
    new_index = index + 1
    if new_index >= len(INTERVALS):
        return new_index, None
    return new_index, INTERVALS[new_index]


def needs_review(*, solved: bool, attempts: int, solution_used: bool = False) -> bool:
    """Чи треба повернути задачу на повторення."""
    if not solved:
        return True
    if attempts > 1:
        return True
    return solution_used


def due_date(days: int, today: date | None = None) -> str:
    today = today or date.today()
    return (today + timedelta(days=days)).isoformat()


def streak_from_days(days: list[str], today: date | None = None) -> int:
    """Серія днів поспіль із активністю.

    Сьогоднішній день зараховується, якщо активність уже була; якщо ні —
    серія рахується від учора, щоб не «згорала» до вечора.
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
