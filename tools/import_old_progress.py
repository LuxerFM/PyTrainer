"""Carries already-done items from the old text roadmap into the trainer database.

The Python-Roadmap.md file (from before the trainer) had ticked items you had
already covered: installing Python, print() and variables, conditions, loops,
the calculator, the "Guess the number" game. This script moves them into the
database so the trainer does not force you to start from zero.

No XP is granted for these tasks — they are only marked as passed.

Run:
    .venv\\Scripts\\python.exe tools/import_old_progress.py            (move)
    .venv\\Scripts\\python.exe tools/import_old_progress.py --dry-run  (show only)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from curriculum import find_task  # noqa: E402
from trainer.core.db import Database  # noqa: E402

# What was ticked [x] in the old roadmap → trainer tasks
ALREADY_DONE = {
    "w1-hello": "встановлення Python і перші print()",
    "w1-vars": "змінні та типи даних",
    "w1-input": "input() і перші умови",
    "w1-if-even": "умови if / elif / else",
    "w1-calc": "мініпроєкт: калькулятор у консолі",
    "w2-for": "цикли for і while",
    "w2-guess": "мініпроєкт: гра «Вгадай число»",
}


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    db = Database()

    print(f"База: {db.path}")
    print("Переношу позначки зі старого роадмапу:\n")

    for task_id, reason in ALREADY_DONE.items():
        task = find_task(task_id)
        if task is None:
            print(f"  ? {task_id} — немає в плані, пропускаю")
            continue

        if db.status(task_id) == "done":
            print(f"  = {task.title} — уже позначено, пропускаю")
            continue

        print(f"  + {task.title} ({reason})")
        if not dry_run:
            db.mark_solved(task_id, xp=0)

    if dry_run:
        print("\nЦе був --dry-run: у базу нічого не записано.")
    else:
        print("\nГотово. Відкрий тренажер — ці задачі вже з галочками.")
        print("Якщо це не те, що треба: у застосунку «Навчання → Скинути прогрес цієї задачі».")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
