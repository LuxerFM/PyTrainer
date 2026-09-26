"""Шляхи до даних і ресурсів — однаково правильні і з коду, і з .exe.

Тут два різні роди файлів, і плутати їх не можна:

* **Ресурси** (іконка, картинки) лежать усередині застосунку: у зібраному
  `.exe` — у теці розпакування `sys._MEIPASS`, з коду — у корені проєкту.
  Для них є `resource()`.
* **Дані людини** (база з багаторічним прогресом, копії бази) живуть у
  службовій теці системи: `%LOCALAPPDATA%\\PyTrainer` на Windows,
  `~/.local/share/PyTrainer` в інших. Для них є `data_folder()`.

Чому дані не поруч із `.exe`, як було раніше: на цій машині робочий стіл
перенаправлено в OneDrive, тому «поруч із .exe» означало «в синхронізованій
теці». SQLite у такій теці — це побита база рано чи пізно: хмара читає й пише
файл тоді, коли їй захочеться, і може зробити це посеред транзакції. Тому база
й копії переїхали в службову теку, а `progress.json` і `Python-Roadmap.md`
лишились поруч із `.exe` — це текстові файли для людини, їм синхронізація не
заважає, а навпаки: їх зручно тримати в Git або на флешці.

Перенос робиться **один раз** і зі страховкою: старий файл копіюється в нову
теку, і лише після успішного копіювання перейменовується в `*.moved`. Так
найгірший випадок — дві копії прогресу замість жодної.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "PyTrainer"
BACKUP_FOLDER = "backups"
DATA_ENV = "PYTRAINER_DATA_DIR"


def is_frozen() -> bool:
    """True, якщо код запущено зі зібраного .exe (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def app_folder() -> Path:
    """Тека застосунку: звичайний запуск — корінь проєкту, .exe — тека .exe.

    Тут лежать файли **для людини**: генерований роадмап і `progress.json`,
    який можна перенести на інший комп'ютер або покласти в Git.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def data_folder() -> Path:
    """Тека для бази, копій і журналів — поза синхронізованими теками.

    Порядок визначення:

    1. `--data-dir ДИРЕКТОРІЯ` або змінна `PYTRAINER_DATA_DIR` — портативний
       режим: усе в одній теці, яку можна носити з собою;
    2. службова тека системи — типовий випадок.
    """
    override = os.environ.get(DATA_ENV)
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def database_path() -> Path:
    """Файл бази з прогресом."""
    return data_folder() / "pytrainer.db"


def apply_data_dir(argv: list[str]) -> str | None:
    """Враховує `--data-dir ДИРЕКТОРІЯ` з командного рядка.

    Мусить викликатись **до** імпорту `trainer.core.db`: шлях до бази
    обчислюється один раз при імпорті, тому змінити теку даних пізніше вже
    неможливо.
    """
    if "--data-dir" in argv:
        index = argv.index("--data-dir")
        if index + 1 < len(argv):
            os.environ[DATA_ENV] = argv[index + 1]
            return argv[index + 1]
    return None


def resource(*parts: str) -> Path:
    """Файл усередині застосунку (іконка, картинки)."""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parents[1]
    return root.joinpath(*parts)


def migrate_data(folder: Path | None = None,
                 legacy: Path | None = None) -> list[str]:
    """Переносить базу й копії з теки застосунку в теку даних. Один раз.

    Повертає список того, що перенесено (порожній — якщо переносити нічого):
    за цим списком `trainer/app.py` пише людині рядок у консоль, щоб переїзд
    не виглядав як зникнення прогресу.

    Порядок важливий: спершу **копіюємо**, потім перейменовуємо старе. Якщо
    копіювання обірветься (немає місця, файл зайнятий), старий файл лишиться
    на місці, і прогрес нікуди не дінеться.
    """
    target_folder = Path(folder) if folder else data_folder()
    legacy_folder = Path(legacy) if legacy else app_folder()
    moved: list[str] = []

    old_db = legacy_folder / "pytrainer.db"
    if old_db.exists():
        target_folder.mkdir(parents=True, exist_ok=True)
        target_db = target_folder / old_db.name
        if not target_db.exists():
            shutil.copy2(old_db, target_db)
            moved.append(old_db.name)
        for suffix in ("-wal", "-shm"):     # сліди WAL, якщо були
            sidecar = Path(str(old_db) + suffix)
            if sidecar.exists():
                try:
                    sidecar.unlink()
                except OSError:
                    pass
        _retire(old_db, "переїхала у теку даних")
        moved.append(f"{old_db.name}.moved")

    old_backups = legacy_folder / BACKUP_FOLDER
    if old_backups.is_dir():
        target_backups = target_folder / BACKUP_FOLDER
        target_backups.mkdir(parents=True, exist_ok=True)
        copied = 0
        for item in sorted(old_backups.glob("*.db")):
            destination = target_backups / item.name
            if not destination.exists():
                shutil.copy2(item, destination)
                copied += 1
        if copied:
            moved.append(f"{BACKUP_FOLDER}/ ({copied} шт.)")
        if not any(old_backups.iterdir()):
            old_backups.rmdir()
        else:
            _retire(old_backups, "переїхали у теку даних")

    return moved


def _retire(path: Path, reason: str) -> None:
    """Перейменовує старий файл у `*.moved`, щоб не читався випадково.

    Не вдалося — не біда: дані вже скопійовані, а зайвий файл лише займає
    місце. Тому тут жодних винятків.
    """
    try:
        path.rename(path.with_name(path.name + ".moved"))
    except OSError:                      # файл зайнятий або тека лише для читання
        pass


__all__ = [
    "APP_NAME",
    "BACKUP_FOLDER",
    "DATA_ENV",
    "app_folder",
    "apply_data_dir",
    "data_folder",
    "database_path",
    "is_frozen",
    "migrate_data",
    "resource",
]
