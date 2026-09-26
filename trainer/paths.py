"""Paths to data and resources — equally correct from code and from .exe.

Two different kinds of files live here, and they must not be mixed:

* **Resources** (icon, images) ship inside the app: in the built `.exe` —
  in the `sys._MEIPASS` unpack folder, from code — in the project root.
  `resource()` is for them.
* **Human data** (the long-lived progress database, db copies) lives in the
  system service folder: `%LOCALAPPDATA%\\PyTrainer` on Windows,
  `~/.local/share/PyTrainer` elsewhere. `data_folder()` is for it.

Why data is not next to the `.exe` anymore: on this machine the desktop is
redirected to OneDrive, so "next to the .exe" meant "in a synced folder".
SQLite in such a folder is a broken database sooner or later: the cloud reads
and writes the file whenever it feels like it, possibly mid-transaction. So
the database and its copies moved to the service folder, while `progress.json`
and `Python-Roadmap.md` stayed next to the `.exe` — plain text files for a
human, sync does not hurt them, quite the opposite: handy in Git or on a
flash drive.

The move runs **once** and insured: the old file is copied to the new folder
first, and only after a successful copy renamed to `*.moved`. So the worst
case is two copies of the progress instead of none.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

APP_NAME = "PyTrainer"
BACKUP_FOLDER = "backups"
DATA_ENV = "PYTRAINER_DATA_DIR"


def is_frozen() -> bool:
    """True when running from the built .exe (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def app_folder() -> Path:
    """App folder: plain run — project root, .exe — the .exe folder.

    Files **for a human** live here: the generated roadmap and `progress.json`,
    which can be moved to another machine or kept in Git.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def data_folder() -> Path:
    """Folder for the database, copies and logs — outside synced folders.

    Resolution order:

    1. `--data-dir DIRECTORY` or the `PYTRAINER_DATA_DIR` variable — portable
       mode: everything in one folder you can carry around;
    2. the system service folder — the typical case.
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
    """The progress database file."""
    return data_folder() / "pytrainer.db"


def apply_data_dir(argv: list[str]) -> str | None:
    """Applies `--data-dir DIRECTORY` from the command line.

    Must be called **before** importing `trainer.core.db`: the db path is
    computed once at import time, so changing the data folder later is
    impossible.
    """
    if "--data-dir" in argv:
        index = argv.index("--data-dir")
        if index + 1 < len(argv):
            os.environ[DATA_ENV] = argv[index + 1]
            return argv[index + 1]
    return None


def resource(*parts: str) -> Path:
    """A file inside the app (icon, images)."""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parents[1]
    return root.joinpath(*parts)


def atomic_write_text(path: str | Path, text: str,
                      encoding: str = "utf-8") -> Path:
    """Writes a text file atomically: tmp nearby + `os.replace`.

    Why: `progress.json` and the roadmap used to be rewritten with a plain
    `write_text` on every verdict — an interruption mid-write (power loss,
    killed process) left half a file. Here the reader sees either the whole
    old file or the whole new one, nothing in between. `os.replace` is atomic
    on both Windows and POSIX when tmp sits in the same folder.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target.parent),
                               prefix=target.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return target


def migrate_data(folder: Path | None = None,
                 legacy: Path | None = None) -> list[str]:
    """Moves the database and copies from the app folder to the data folder. Once.

    Returns the list of what was moved (empty — if there is nothing to move):
    `trainer/app.py` prints that list as a console line so the move does not
    look like vanished progress.

    Order matters: **copy** first, then rename the old. If copying breaks off
    (no space, file busy), the old file stays put and the progress goes
    nowhere.
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
        for suffix in ("-wal", "-shm"):     # WAL traces, if any
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
    """Renames the old file to `*.moved` so it is never read by accident.

    Failure is fine: the data is already copied, and a spare file only takes
    space. Hence no exceptions here.
    """
    try:
        path.rename(path.with_name(path.name + ".moved"))
    except OSError:                      # file busy or folder read-only
        pass


__all__ = [
    "APP_NAME",
    "BACKUP_FOLDER",
    "DATA_ENV",
    "app_folder",
    "apply_data_dir",
    "atomic_write_text",
    "data_folder",
    "database_path",
    "is_frozen",
    "migrate_data",
    "resource",
]
