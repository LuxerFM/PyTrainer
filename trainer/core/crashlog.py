"""Креш-лог і версія — щоб «закрилось і мовчить» стало «закрилось і видно чому».

Що робить модуль (усе — стандартна бібліотека):

* `version()` — єдина версія з `trainer/__init__.py`, плюс дата збірки,
  якщо її записав `tools/build_exe.py` (файл `trainer/_build.py`);
* `setup_crashlog()` — включає `logging` у файл `logs/pytrainer.log`
  у теці даних і ставить `sys.excepthook`, який кожен неперехоплений виняток
  пише ще й в окремий `logs/crash-<дата>.log` з версією, платформою й argv.

Викликається один раз на старті (`trainer/app.py` і `trainer/cli.py`
для `--self-test`). Ідемпотентно: повторний виклик нічого не міняє.
"""

from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_FOLDER = "logs"


def version() -> str:
    """Версія застосунку, напр. «0.2.0»."""
    from trainer import __version__

    return __version__


def build_info() -> str:
    """Дата збірки .exe або «з коду» для звичайного запуску."""
    try:
        from trainer import _build as build  # type: ignore

        stamp = getattr(build, "BUILD_DATE", "")
        if stamp:
            return f"збірка {stamp}"
    except ImportError:
        pass
    return "з коду"


def version_line() -> str:
    """Один рядок для --version, заголовка вікна й шапки креш-логу."""
    return f"PyTrainer {version()} ({build_info()})"


def log_folder(folder: str | Path | None = None) -> Path:
    """Тека журналів усередині теки даних."""
    from ..paths import data_folder

    target = Path(folder) if folder else data_folder() / LOG_FOLDER
    target.mkdir(parents=True, exist_ok=True)
    return target


def _header() -> str:
    from ..paths import is_frozen

    argv = " ".join(sys.argv)
    return (
        f"{version_line()}\n"
        f"Python {sys.version.split()[0]} on {sys.platform} "
        f"({'exe' if is_frozen() else 'код'})\n"
        f"Запуск: {argv}\n"
    )


_configured_for: str | None = None
_hook_installed = False
_previous_hook = None
_handler: logging.Handler | None = None
_folder: str | None = None


def setup_crashlog(folder: str | Path | None = None) -> Path:
    """Вмикає файл-журнал і перехоплення неперехоплених винятків.

    Повертає шлях до основного журналу (`pytrainer.log`).
    """
    global _configured_for, _hook_installed, _previous_hook, _handler, _folder

    target = log_folder(folder)
    _folder = str(target)
    log_path = target / "pytrainer.log"
    if str(log_path) != _configured_for:
        root = logging.getLogger()
        if _handler is not None:
            root.removeHandler(_handler)
            _handler.close()
            _handler = None
        handler = logging.FileHandler(str(log_path), encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        _handler = handler
        root.info(_header().replace("\n", " | "))
        _configured_for = str(log_path)

    if not _hook_installed or sys.excepthook is not _excepthook:
        _previous_hook = sys.excepthook
        if _previous_hook is _excepthook:
            _previous_hook = sys.__excepthook__
        sys.excepthook = _excepthook
        _hook_installed = True
    return log_path


def _excepthook(kind, value, tb) -> None:
    try:
        target = Path(_folder) if _folder else log_folder()
        target.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        crash = target / f"crash-{stamp}.log"
        crash.write_text(
            _header() + "\n"
            + "".join(traceback.format_exception(kind, value, tb)),
            encoding="utf-8",
        )
        logging.getLogger("pytrainer.crash").critical(
            "Неперехоплений виняток, подробиці в %s", crash.name,
        )
    except OSError:
        pass
    previous = _previous_hook
    if previous is not None and previous is not _excepthook:
        previous(kind, value, tb)
    else:
        sys.__excepthook__(kind, value, tb)


def reset_for_tests() -> None:
    """Скидає стан модуля — лише для тестів."""
    global _configured_for, _hook_installed, _previous_hook, _handler, _folder
    if _handler is not None:
        logging.getLogger().removeHandler(_handler)
        _handler.close()
        _handler = None
    if _hook_installed and sys.excepthook is _excepthook:
        sys.excepthook = _previous_hook or sys.__excepthook__
    _configured_for = None
    _hook_installed = False
    _previous_hook = None
    _folder = None


__all__ = [
    "LOG_FOLDER",
    "build_info",
    "log_folder",
    "reset_for_tests",
    "setup_crashlog",
    "version",
    "version_line",
]
