"""Створює окрему демонстраційну базу (не чіпаючи твою).

    .venv\\Scripts\\python.exe tools/demo_data.py

Далі цю базу можна подивитись, підмінивши файл, або просто запустити
застосунок у демо-режимі: python main.py --demo
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trainer.core.db import Database  # noqa: E402
from trainer.core.demo import seed_database  # noqa: E402


def main() -> int:
    target = ROOT / "pytrainer-demo.db"
    if target.exists():
        target.unlink()
    db = Database(target)
    seed_database(db)
    tasks = len(db.statuses())
    print(f"Демо-база: {target}")
    print(f"Задач із прогресом: {tasks} · XP: {db.total_xp()} · серія: {db.streak()} дн.")
    print("Переглянути: скопіюй її в pytrainer.db або запусти main.py --demo")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
