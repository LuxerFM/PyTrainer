"""Launching the PyTrainer app.

Plain run:
    .venv\\Scripts\\python.exe main.py
    .venv\\Scripts\\python.exe -m trainer          (same)

Demo mode (leaves your progress alone — runs on a temp database):
    python main.py --demo

Service modes for development (to take README screenshots):
    ... --screenshot screenshots/main.png --demo
    ... --screenshot progress.png --view progress --demo
    ... --screenshot checks.png --task w2-list --solution --run-checks --demo

Theme and text scale can be given right on the command line:
    python main.py --theme light
    python main.py --scale 1.2

Portable mode (data in one folder with the .exe — on a flash drive or in an archive):
    python main.py --data-dir D:\\PyTrainer
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
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

from .core.exec_runner import ensure_streams  # noqa: E402

# The icon ships inside the app, so take it via `resource()`:
# in the built .exe that is the unpack folder, not the project root.
from .paths import (  # noqa: E402
    apply_data_dir,
    data_folder,
    database_path,
    migrate_data,
    resource,
)

ICON_PATH = resource("assets", "icon.png")
VIEWS = {"roadmap": 0, "reviews": 1, "progress": 2, "plan": 3}


class InstanceGuard:
    """Keeps a second copy of the app from opening on the same database.

    Two windows on one database is not just screen confusion: parallel writes
    to SQLite, two different "active seconds" and two review queues overwriting
    each other.

    Why `QLockFile` and not a named pipe: `QLocalServer` on Windows calmly
    lets several processes listen on the same name (verified), so as a lock it
    does not work. `QLockFile` does exactly what is needed: atomically creates
    a lock file with the process number inside, and if the program was killed —
    the lock counts as stale (Qt checks whether that PID is alive) and the next
    launch removes it.

    The lock lives in the data folder, so portable mode (`--data-dir`) is a
    separate app with its own lock, not "already running".
    """

    def __init__(self, folder: str | Path) -> None:
        self.path = Path(folder) / "pytrainer.lock"
        self.lock = None
        self.holder = ""
        self.recovered = False

    def claim(self) -> bool:
        """True — we are first; False — another copy runs (its PID is in `holder`)."""
        from PySide6.QtCore import QLockFile

        self.holder = ""
        self.recovered = False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(self.path))
        lock.setStaleLockTime(30_000)
        # 200 ms is not a wait but a second try: Qt manages to remove
        # a crashed process's lock within that time.
        if lock.tryLock(200):
            self.lock = lock
            return True

        info = lock.getLockInfo()
        pid = info[0] if info else 0
        name = info[2] if len(info) >= 3 else ""
        if not pid and lock.removeStaleLockFile() and lock.tryLock(200):
            # A live copy always writes its PID and boot number into the lock,
            # so a lock Qt can read nothing from is not a process but garbage:
            # a torn record, a corrupted file, someone else's file with that
            # name. Without this step such a lock would stay forever, and the
            # app would never open again — with an "already running" message
            # about nobody. Taking the lock from a live copy still fails:
            # Windows does not let you delete an open file, so we politely
            # yield our place as before.
            self.lock = lock
            self.recovered = True
            return True
        if pid:
            self.holder = f"{name or 'PyTrainer'}, PID {pid}"
        return False

    def release(self) -> None:
        """Releases the lock — needed by tests and screenshot service runs."""
        if self.lock is not None:
            self.lock.unlock()
            self.lock = None


def open_database(factory, target: Path) -> tuple[object, str]:
    """Opens the database, and if the file is broken — slides it aside and starts fresh.

    A broken file is never deleted: the human must be able to hand it to
    someone to try data recovery. A quiet copy of the previous launch always
    sits nearby, so the worst case is losing one launch.

    Returns a (database, note for the human) pair; the note is empty when all
    is well.
    """
    try:
        database = factory(target)
    except sqlite3.DatabaseError as error:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        broken = target.with_name(f"{target.name}.broken-{stamp}")
        for suffix in ("", "-wal", "-shm"):          # the file itself and WAL traces
            side = Path(str(target) + suffix)
            if side.exists():
                try:
                    side.rename(Path(str(broken) + suffix))
                except OSError:
                    pass
        database = factory(target)
        return database, (
            f"База була пошкоджена ({error}), тому її відсунуто в "
            f"{broken.name}. Починаємо нову; попередній прогрес лежить у "
            f"{broken.name} і в теці копій:\n{data_folder()}"
        )
    if not database.quick_check():
        return database, (
            "Перевірка цілісності бази не пройшла — далі працювати ризиковано. "
            f"Копії попередніх запусків лежать у {data_folder()}"
        )
    return database, ""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    # First — the data folder: the db path is computed at import time of
    # `trainer.core.db`, so `--data-dir` must be applied earlier.
    apply_data_dir(argv)

    from .core.crashlog import version_line

    if "--version" in argv or "-V" in argv:
        print(version_line())
        return 0

    # In the built .exe PyInstaller attaches output with the system encoding,
    # and any non-ASCII there breaks printing in console modes (`--demo`,
    # `--screenshot`). See `core/exec_runner.ensure_streams`.
    ensure_streams()

    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ImportError:
        print(HELP)
        return 1

    from .core.crashlog import setup_crashlog
    from .core.db import Database, backup_database
    from .core.runner import warm_up_interpreter
    from .ui.main_window import MainWindow
    from .ui.theme import apply_theme

    log_path = setup_crashlog()
    print(f"Журнал: {log_path}")

    # If the app already exists (embedded launch, tests) — take it:
    # Qt forbids a second QApplication in one process.
    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName("PyTrainer")
    app.setApplicationDisplayName("PyTrainer")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    if "--scale" in argv:
        from .ui.theme import set_scale

        set_scale(float(argv[argv.index("--scale") + 1]))
    theme = argv[argv.index("--theme") + 1] if "--theme" in argv else None
    apply_theme(app, theme)

    # A second copy on the same database is two different progresses wiping
    # each other. So the second launch only tells where the open window is
    # and exits. Demo mode is the exception: it runs on a temp database and
    # is deliberately launched many times in a row (tests, screenshot script).
    demo = "--demo" in argv
    guard = None if demo else InstanceGuard(data_folder())
    if guard is not None and not guard.claim():
        print("PyTrainer уже запущено"
              + (f" ({guard.holder})" if guard.holder else ""))
        QMessageBox.information(
            None, "PyTrainer уже запущено",
            "На цій самій базі вже відкрито вікно тренажера"
            + (f" ({guard.holder})" if guard.holder else "")
            + ".\n\nПрогрес пишеться в один файл, тому два вікна затирали б одне "
              "одного. Перемкнись на відкрите вікно або закрий його й запусти "
              "заново.",
        )
        return 0

    if guard is not None and guard.recovered:
        print("Замок попереднього запуску був пошкоджений — прибрано, працюю далі.")

    demo_folder: Path | None = None
    if demo:
        window, demo_folder = _demo_window(Database)
    else:
        for what in migrate_data():
            print(f"Дані перенесено в {data_folder()}: {what}")

        database, note = open_database(Database, database_path())
        backup_database()          # quiet copy before work
        window = MainWindow(db=database)
        # While the human reads the first task, the child already unpacks —
        # otherwise the first verdict in the .exe would wait seconds on it.
        warm_up_interpreter()
        if note:
            QMessageBox.warning(None, "База даних", note)
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

    code = app.exec()

    # The demo database is temp — remove it on exit. Otherwise every launch
    # (dozens in tests and CI) would leave a pytrainer_demo_* folder in %TEMP%,
    # and in a month there would be hundreds of copies of the same demo base.
    # Remove exactly here, not in closeEvent: the window already closed the db,
    # and force-killing the process breaks no cleanup.
    if demo_folder is not None:
        shutil.rmtree(demo_folder, ignore_errors=True)
    return code


def _demo_window(database) -> tuple["MainWindow", Path]:
    """Window on a temp database with demo progress.

    Also returns that base's folder — `main()` removes it on exit. Demo
    deliberately touches neither the data folder nor the real `progress.json`:
    it can be launched any number of times in a row.
    """
    from .core.demo import seed_database
    from .ui.main_window import MainWindow

    folder = Path(tempfile.mkdtemp(prefix="pytrainer_demo_"))
    db = database(folder / "demo.db")
    seed_database(db)
    print(f"Демо-режим: тимчасова база {db.path}")
    window = MainWindow(
        db=db,
        roadmap_path=folder / "Python-Roadmap.md",
        progress_path=folder / "progress.json",
        settings_path=None,        # demo must not remember the real app's state
    )
    return window, folder
