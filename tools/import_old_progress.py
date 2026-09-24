"""Переносить уже виконане зі старого текстового роадмапу в базу тренажера.

У файлі Python-Roadmap.md (до появи тренажера) були відмічені пункти, які ти
вже пройшов: встановлення Python, print() і змінні, умови, цикли, калькулятор,
гра «Вгадай число». Цей скрипт переносить їх у базу, щоб тренажер не змушував
починати з нуля.

XP за ці задачі не нараховується — вони лише позначаються як пройдені.

Запуск:
    .venv\\Scripts\\python.exe tools/import_old_progress.py            (перенести)
    .venv\\Scripts\\python.exe tools/import_old_progress.py --dry-run  (тільки показати)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from curriculum import find_task  # noqa: E402
from trainer.core.db import Database  # noqa: E402

# Що було відмічено [x] у старому роадмапі → задачі тренажера
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
