"""Запуск застосунку PyTrainer.

Звичайний запуск:
    .venv\\Scripts\\python.exe main.py
    .venv\\Scripts\\python.exe -m trainer          (те саме)

Демо-режим (не чіпає твій прогрес — працює на тимчасовій базі):
    python main.py --demo

Службові режими для розробки (щоб робити знімки для README):
    ... --screenshot screenshots/main.png --demo
    ... --screenshot progress.png --view progress --demo
    ... --screenshot checks.png --task w2-list --solution --run-checks --demo

Можна вказати тему й масштаб тексту прямо в командному рядку:
    python main.py --theme light
    python main.py --scale 1.2
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HELP = """
PySide6 не знайдено у поточному Python.

Запускай застосунок інтерпретатором із віртуального оточення:
    Windows:  .venv\\Scripts\\python.exe main.py
    Linux:    .venv/bin/python main.py

Якщо оточення ще немає, створи його так:
    python -m venv .venv
    .venv\\Scripts\\python.exe -m pip install -r requirements.txt
"""

# Іконка лежить усередині застосунку, тому беремо її через `resource()`:
# у зібраному .exe це тека розпакування, а не корінь проєкту.
from .paths import resource  # noqa: E402

ICON_PATH = resource("assets", "icon.png")
VIEWS = {"roadmap": 0, "reviews": 1, "progress": 2, "plan": 3}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(HELP)
        return 1

    from .core.db import Database, backup_database
    from .ui.main_window import MainWindow
    from .ui.theme import apply_theme

    app = QApplication(argv)
    app.setApplicationName("PyTrainer")
    app.setApplicationDisplayName("PyTrainer")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    if "--scale" in argv:
        from .ui.theme import set_scale

        set_scale(float(argv[argv.index("--scale") + 1]))
    theme = argv[argv.index("--theme") + 1] if "--theme" in argv else None
    apply_theme(app, theme)

    if "--demo" in argv:
        window = _demo_window(Database)
    else:
        # Тиха копія бази перед роботою: прогрес за місяці не має залежати
        # від одного файлу.
        backup_database()
        window = MainWindow()
    window.show()

    if "--task" in argv:
        window.open_task(argv[argv.index("--task") + 1])
    if "--solution" in argv and window._task is not None:
        window.editor.setPlainText(window._task.solution_hint.text)
    if "--run-checks" in argv:
        window.run_checks()

    if "--screenshot" in argv:
        path = argv[argv.index("--screenshot") + 1]
        view = argv[argv.index("--view") + 1] if "--view" in argv else "roadmap"

        def capture() -> None:
            window.sidebar.set_mode(VIEWS.get(view, 0))
            window.grab().save(path)
            print(f"Знімок збережено: {path}")
            app.quit()

        QTimer.singleShot(2500, capture)

    return app.exec()


def _demo_window(database) -> "MainWindow":
    """Вікно на тимчасовій базі з демонстраційним прогресом."""
    from .core.demo import seed_database
    from .ui.main_window import MainWindow

    folder = Path(tempfile.mkdtemp(prefix="pytrainer_demo_"))
    db = database(folder / "demo.db")
    seed_database(db)
    print(f"Демо-режим: тимчасова база {db.path}")
    return MainWindow(
        db=db,
        roadmap_path=folder / "Python-Roadmap.md",
        progress_path=folder / "progress.json",
        settings_path=None,        # демо не має пам'ятати стан справжнього застосунку
    )
