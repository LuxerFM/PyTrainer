"""Робить усі знімки для README — однією командою й без твого прогресу.

    .venv\\Scripts\\python.exe tools/make_screenshots.py

Кожен знімок — це справжній рендер вікна (жодних макетів): застосунок
запускається на демонстраційній базі (`trainer/core/demo.py`), відкриває
потрібну задачу, за потреби реально проганяє її тести — і зберігає
`window.grab()` у `docs/images/`.

Чому саме скрипт, а не «зробив руками»: знімки в README тьмяніють швидко —
змінилася верстка панелі, і картинки вже брешуть. Одна команда повертає їх
до правди. Працює без екрана (QT_QPA_PLATFORM=offscreen), тому запускається
і в CI, і по SSH.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from trainer.core.db import Database  # noqa: E402
from trainer.core.demo import seed_database  # noqa: E402
from trainer.ui.main_window import MainWindow  # noqa: E402
from trainer.ui.task_panel import TAB_CHEATSHEET, TAB_HINTS, TAB_REVIEW  # noqa: E402
from trainer.ui.theme import apply_theme  # noqa: E402

TARGET = ROOT / "docs" / "images"
VIEW_ROADMAP, VIEW_REVIEWS, VIEW_PROGRESS = 0, 1, 2

# Код, який «написав учень»: він працює, але саме на такому розбір коду
# показує свою користь — і жодне з цих зауважень не про тести.
SLOPPY_SAMPLE = '''\
import math
import random


def AvgOfMarks(marks):
    total = 0
    for i in range(len(marks)):
        total = total + marks[i]
    avg = total / len(marks)
    if avg == None:
        return 0
    if avg >= 4.5:
        return True
    else:
        return False
'''


@dataclass
class Shot:
    """Один кадр: що відкрити, що запустити і як це підписати."""

    name: str
    caption: str
    task: str | None = None
    view: int = VIEW_ROADMAP
    solution: bool = False
    run: bool = False
    tab: int | None = None
    theme: str = "dark"
    cold: bool = False          # почати холодне повторення замість відкриття задачі
    code: str = ""              # текст у редакторі (наприклад код із помилками стилю)
    digest: bool = False        # зняти вікно тижневого огляду, а не головне вікно


SHOTS: tuple[Shot, ...] = (
    Shot(
        "01-roadmap",
        "Головне вікно: план зліва, редактор по центру, умова й перевірки справа",
    ),
    Shot(
        "02-checks",
        "Перевірка коду: приховані тести, вердикт і консоль із виводом",
        task="w2-list",
        solution=True,
        run=True,
    ),
    Shot(
        "03-progress",
        "Режим «Прогрес»: здано / утримано, XP, серія днів, слабкі місця",
        view=VIEW_PROGRESS,
    ),
    Shot(
        "04-reviews",
        "Режим «Повторення»: черга задач, які час згадати",
        view=VIEW_REVIEWS,
    ),
    Shot(
        "05-error-help",
        "Пояснення помилки українською: що це означає, у якому рядку і що робити",
        task="m4-debug-average",
        run=True,
    ),
    Shot(
        "06-cheatsheet",
        "Міні-довідка з теми задачі — вкладка «Довідка»",
        task="m3-lc-two-sum",
        tab=TAB_CHEATSHEET,
    ),
    Shot(
        "07-light",
        "Світла тема й масштаб тексту — перемикається в меню «Вигляд»",
        task="w2-list",
        solution=True,
        run=True,
        theme="light",
    ),
    Shot(
        "08-cold-review",
        "Холодне повторення: здана задача із заготовки, підказки й розв'язок "
        "замкнено, іде зворотний відлік",
        view=VIEW_REVIEWS,
        tab=TAB_HINTS,
        cold=True,
    ),
    Shot(
        "09-code-review",
        "Рев'ю коду: тренажер читає твій код і каже, що в ньому не так — і як "
        "виправити",
        task="w1-marks",
        tab=TAB_REVIEW,
        code=SLOPPY_SAMPLE,
    ),
    Shot(
        "10-weekly-digest",
        "Тижневий огляд: що сталося за сім днів і що робити далі",
        view=VIEW_PROGRESS,
        digest=True,
    ),
)


def run_checks_and_wait(window: MainWindow, app: QApplication) -> None:
    """Проганяє перевірки й чекає на результат (у застосунку це окремий потік)."""
    loop = QEventLoop()
    window.run_finished.connect(lambda *_: loop.quit())
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(20_000)
    window.run_checks()
    loop.exec()
    app.processEvents()


def settle(app: QApplication, rounds: int = 3) -> None:
    """Дає Qt домалювати: розкладка, переноси рядків, кольори."""
    for _ in range(rounds):
        app.processEvents()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PyTrainer")
    apply_theme(app, "dark")

    TARGET.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="pytrainer_shots_"))
    db = Database(folder / "demo.db")
    seed_database(db)

    # settings_path=None — щоб знімки не залежали від того, як ти востаннє
    # розтягнув вікно у справжньому застосунку.
    window = MainWindow(
        db=db,
        roadmap_path=folder / "Python-Roadmap.md",
        progress_path=folder / "progress.json",
        settings_path=None,
    )
    window.show()
    settle(app)

    try:
        for shot in SHOTS:
            apply_theme(app, shot.theme)
            window.sidebar.set_mode(shot.view)
            if shot.task:
                window.open_task(shot.task)
                if shot.solution and window._task is not None:
                    window.editor.setPlainText(window._task.solution_hint.text)
            if shot.cold:
                window.start_cold_review()
            if shot.code:
                window.editor.setPlainText(shot.code)
                window.review_current_code()
            settle(app)

            if shot.run:
                run_checks_and_wait(window, app)
            if shot.tab is not None:
                window.panel.tabs.setCurrentIndex(shot.tab)
            if shot.digest:
                window.show_digest()
            settle(app, 5)

            # Вікно огляду — окремий віджет, тому знімаємо саме його.
            frame = window.digest_dialog if shot.digest else window
            path = TARGET / f"{shot.name}.png"
            if not frame.grab().save(str(path)):
                print(f"Не вдалося зберегти {path}")
                return 1
            if shot.digest:
                window.digest_dialog.close()
            print(f"{path.name:22} {shot.caption}")
    finally:
        window.close()
        db.close()
        shutil.rmtree(folder, ignore_errors=True)

    print(f"\nГотово: {len(SHOTS)} знімки у {TARGET}")
    print("Подивитись їх одним файлом: "
          ".venv\\Scripts\\python.exe tools/preview_screenshot.py docs/images/*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
