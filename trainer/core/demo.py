"""Демонстраційний прогрес — щоб подивитись застосунок «живим» і не чіпати свій.

Використовується двома способами:

    python main.py --demo         # запуск на тимчасовій базі з цим прогресом
    python tools/demo_data.py     # створити демо-базу й показати шлях до неї

Це також те, з чого зроблені знімки для README.
"""

from __future__ import annotations

from datetime import date, timedelta

from .db import Database

# (id задачі, XP, скільки підказок було відкрито)
SOLVED = [
    ("w1-hello", 100, 0),
    ("w1-vars", 100, 0),
    ("w1-input", 85, 1),
    ("w1-if-even", 150, 0),
    ("w1-if-marks", 128, 1),
    ("w1-calc", 250, 0),
    ("w2-for", 150, 0),
    ("w2-strings", 150, 0),
    ("m2-class-expense", 150, 0),
]

# задачі, у яких були провали — вони й творять «слабкі місця»
STRUGGLED = ["w2-list", "w2-list", "w2-list", "w3-dict", "w4-errors", "w4-errors"]

REVIEWS = [("w1-input", 1, 0), ("w1-if-marks", 3, 1)]
IN_PROGRESS = "w2-list"

# (скільки днів тому, скільки спроб) — для календаря активності й серії
ACTIVITY = [(0, 4), (1, 6), (2, 3), (3, 5), (4, 2), (6, 4), (7, 1), (9, 3),
            (11, 5), (14, 2), (17, 4), (21, 1), (24, 3), (30, 2)]


def seed_database(db: Database, *, today: date | None = None) -> None:
    """Наповнює базу правдоподібним прогрессом за кілька тижнів навчання."""
    today = today or date.today()

    for task_id, xp, hints in SOLVED:
        db.mark_solved(task_id, xp)
        if hints:
            db.reveal_hint(task_id, hints)
        db.add_active_seconds(task_id, 420 + xp)
        db.record_attempt(task_id, ok=True, with_checks=True, xp=xp)

    for task_id in STRUGGLED:
        db.record_attempt(task_id, ok=False, with_checks=True)

    db.reveal_hint("w2-list", 1)
    db.add_active_seconds("w2-list", 780)
    db.mark_in_progress(IN_PROGRESS)

    for task_id, days, index in REVIEWS:
        db.schedule_review(task_id, days, index)

    _seed_activity_days(db, today)


def _seed_activity_days(db: Database, today: date) -> None:
    """Додає спроби в минулі дні — інакше календар і серія були б порожні."""
    for days_ago, count in ACTIVITY:
        day = today - timedelta(days=days_ago)
        for _ in range(count):
            db.connection.execute(
                "INSERT INTO attempts (task_id, created_at, ok, with_checks, xp) "
                "VALUES (?, ?, 1, 1, 0)",
                ("w1-hello", f"{day.isoformat()}T19:30:00"),
            )
    db.connection.commit()
