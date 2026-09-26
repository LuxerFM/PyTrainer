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

Портативний режим (дані в одній теці з .exe — на флешці чи в архіві):
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

# Іконка лежить усередині застосунку, тому беремо її через `resource()`:
# у зібраному .exe це тека розпакування, а не корінь проєкту.
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
    """Не дає відкрити другу копію застосунку на тій самій базі.

    Два вікна на одній базі — це не лише плутанина на екрані: це паралельні
    записи в SQLite, два різні «активні секунди» й дві черги повторень, які
    перезаписують одна одну.

    Чому саме `QLockFile`, а не іменований канал: `QLocalServer` на Windows
    спокійно дозволяє кільком процесам слухати одне й те саме ім'я (це
    перевірено), тому як замок він не працює. `QLockFile` робить рівно те,
    що треба: атомарно створює файл-замок із номером процесу всередині, а якщо
    програму вбили — замок уважається застарілим (Qt перевіряє, чи живий той
    PID) і наступний запуск його прибирає.

    Замок лежить у теці даних, тому портативний режим (`--data-dir`) — це
    окремий застосунок зі своїм замком, а не «вже запущено».
    """

    def __init__(self, folder: str | Path) -> None:
        self.path = Path(folder) / "pytrainer.lock"
        self.lock = None
        self.holder = ""
        self.recovered = False

    def claim(self) -> bool:
        """True — ми перші; False — працює інша копія (її PID — у `holder`)."""
        from PySide6.QtCore import QLockFile

        self.holder = ""
        self.recovered = False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(self.path))
        lock.setStaleLockTime(30_000)
        # 200 мс — не очікування, а друга спроба: за цей час Qt устигає
        # прибрати замок від процесу, який аварійно завершився.
        if lock.tryLock(200):
            self.lock = lock
            return True

        info = lock.getLockInfo()
        pid = info[0] if info else 0
        name = info[2] if len(info) >= 3 else ""
        if not pid and lock.removeStaleLockFile() and lock.tryLock(200):
            # Жива копія завжди пише у замок свій PID і номер завантаження
            # системи, тому замок, з якого Qt не може прочитати нічого, — це
            # не процес, а сміття: обірваний запис, зіпсований файл, чужий
            # файл із такою назвою. Без цього кроку такий замок лишався б
            # назавжди, і застосунок більше не відкрився б — із повідомленням
            # «уже запущено» про нікого. Відібрати замок у живої копії при
            # цьому не вийде: Windows не дає видалити відкритий файл, і тоді
            # ми чемно поступаємось місцем, як і раніше.
            self.lock = lock
            self.recovered = True
            return True
        if pid:
            self.holder = f"{name or 'PyTrainer'}, PID {pid}"
        return False

    def release(self) -> None:
        """Відпускає замок — потрібно тестам і службовим запускам зі знімками."""
        if self.lock is not None:
            self.lock.unlock()
            self.lock = None


def open_database(factory, target: Path) -> tuple[object, str]:
    """Відкриває базу, а якщо файл побитий — відсуває його й починає нову.

    Побитий файл не видаляємо: людина має мати можливість віддати його
    комусь, щоб той спробував витягти дані. Поруч завжди лежить тиха копія
    попереднього запуску, тому найгірший випадок — втрата одного запуску.

    Повертає пару (база, зауваження для людини); зауваження порожнє, якщо все
    гаразд.
    """
    try:
        database = factory(target)
    except sqlite3.DatabaseError as error:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        broken = target.with_name(f"{target.name}.broken-{stamp}")
        for suffix in ("", "-wal", "-shm"):          # сам файл і сліди WAL
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

    # Найперше — тека даних: шлях до бази обчислюється під час імпорту
    # `trainer.core.db`, тому `--data-dir` має бути врахований раніше.
    apply_data_dir(argv)

    from .core.crashlog import version_line

    if "--version" in argv or "-V" in argv:
        print(version_line())
        return 0

    # У зібраному .exe PyInstaller приєднує вивід із кодуванням системи, і
    # будь-яке «…» у ньому зриває друк у консольних режимах (`--demo`,
    # `--screenshot`). Див. `core/exec_runner.ensure_streams`.
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

    # Якщо застосунок уже створено (вбудований запуск, тести) — беремо його:
    # другий QApplication у одному процесі Qt не дозволяє.
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

    # Друга копія на тій самій базі — це два різні прогреси, які затирають
    # один одного. Тому другий запуск лише каже, де шукати відкрите вікно, і
    # виходить. Демо-режим виняток: він працює на тимчасовій базі й навмисно
    # запускається багато разів підряд (тести, скрипт знімків).
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
        backup_database()          # тиха копія перед роботою
        window = MainWindow(db=database)
        # Поки людина читає умову першої задачі, дитина вже розпаковується —
        # інакше перший вердикт у .exe чекав би на це кілька секунд.
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

    # Демо-база тимчасова — прибираємо її після виходу. Інакше кожен запуск
    # (а їх у тестах і в CI десятки) лишав би в %TEMP% теку pytrainer_demo_*,
    # і через місяць там лежали б сотні копій однієї й тієї ж демо-бази.
    # Видаляємо саме тут, а не в closeEvent: база вже закрита вікном, а якщо
    # процес уб'ють силою — прибирати нічого не зламає.
    if demo_folder is not None:
        shutil.rmtree(demo_folder, ignore_errors=True)
    return code


def _demo_window(database) -> tuple["MainWindow", Path]:
    """Вікно на тимчасовій базі з демонстраційним прогресом.

    Повертає ще й теку цієї бази — її прибирає `main()` після виходу.
    Демо навмисно не чіпає ні теку даних, ні справжній `progress.json`:
    його можна запускати скільки завгодно разів поспіль.
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
        settings_path=None,        # демо не має пам'ятати стан справжнього застосунку
    )
    return window, folder
