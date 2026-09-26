"""Вибір режиму запуску: вікно, виконання чужого коду, самоперевірка.

Порядок тут не випадковий. Службові режими перевіряються **до** імпорту
PySide6, і це не мікрооптимізація:

* `--exec-runner` виконує код користувача, тобто окремий запуск на кожну
  перевірку. У зібраному `.exe` кожен такий запуск ще й розпаковує архів
  PyInstaller-а, тому зайвий імпорт Qt додавав би до кожної перевірки
  помітну частку секунди;
* `--self-test` перевіряє саме ці запуски — і в CI, де Qt може бути взагалі
  не потрібен, він не має тягнути за собою інтерфейс.

Звичайний запуск (без прапорців) іде у `trainer/app.py`.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    from .core.exec_runner import FLAG as RUN_FLAG, main as run_main

    if RUN_FLAG in argv:
        return run_main(argv)

    from .core.selfcheck import FLAG as TEST_FLAG, main as test_main

    if TEST_FLAG in argv:
        return test_main(argv)

    from .app import main as window_main

    return window_main(argv)


__all__ = ["main"]
