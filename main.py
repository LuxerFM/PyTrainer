"""Точка входу PyTrainer.

Запуск:
    .venv\\Scripts\\python.exe main.py        (Windows)
    .venv/bin/python main.py                 (Linux/macOS)

Службовий режим (для розробки — зробити знімок вікна):
    .venv\\Scripts\\python.exe main.py --screenshot screenshots/demo.png
    .venv\\Scripts\\python.exe main.py --screenshot progress.png --view progress
"""

from __future__ import annotations

import sys

HELP = """
PySide6 не знайдено у поточному Python.

Запускай застосунок інтерпретатором із віртуального оточення:
    Windows:  .venv\\Scripts\\python.exe main.py
    Linux:    .venv/bin/python main.py

Якщо оточення ще немає, створи його так:
    python -m venv .venv
    .venv\\Scripts\\python.exe -m pip install pyside6
"""


def main() -> int:
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(HELP)
        return 1

    from trainer.ui.main_window import MainWindow
    from trainer.ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("PyTrainer")
    apply_theme(app)

    window = MainWindow()
    window.show()

    # --screenshot <шлях>: показати вікно, зберегти знімок і вийти
    if "--screenshot" in sys.argv:
        path = sys.argv[sys.argv.index("--screenshot") + 1]
        view = "roadmap"
        if "--view" in sys.argv:
            view = sys.argv[sys.argv.index("--view") + 1]
        pages = {"roadmap": 0, "reviews": 1, "progress": 2}

        def capture() -> None:
            window.sidebar.set_mode(pages.get(view, 0))
            window.grab().save(path)
            print(f"Знімок збережено: {path}")
            app.quit()

        QTimer.singleShot(1200, capture)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
