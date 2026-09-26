"""Перегенеровує Python-Roadmap.md із навчального плану та бази прогресу.

Застосунок робить це сам після кожної здачі задачі, але інколи треба
оновити файл вручну:

    .venv\\Scripts\\python.exe tools/generate_roadmap.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # щоб запускати скрипт із будь-якої папки

from curriculum.roadmap_md import write  # noqa: E402
from trainer.core.db import Database  # noqa: E402


def main() -> int:
    db = Database()
    target = write(
        ROOT / "Python-Roadmap.md",
        db.statuses(),
        {"xp": db.total_xp(), "streak": db.streak()},
    )
    print(f"Роадмап оновлено: {target}")

    from trainer.paths import atomic_write_text

    snapshot = atomic_write_text(
        ROOT / "progress.json",
        json.dumps(db.snapshot(), ensure_ascii=False, indent=2),
    )
    print(f"Прогрес збережено: {snapshot}")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
