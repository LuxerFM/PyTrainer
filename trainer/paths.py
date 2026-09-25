"""Шляхи до даних і ресурсів — однаково правильні і з коду, і з .exe.

Проблема, яку вирішує цей модуль: зібраний PyInstaller-ом `.exe` розпаковує
себе в тимчасову теку, яку прибирає після виходу. Якщо рахувати шляхи від
`__file__`, то база з прогресом, роадмап і налаштування опиняться в тій
тимчасовій теці — тобто **весь прогрес зникав би після кожного закриття**.
Тому файли, які належать людині, лежать поруч із самим `.exe`.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """True, якщо код запущено зі зібраного .exe (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def app_folder() -> Path:
    """Тека для файлів користувача: база, роадмап, налаштування.

    Звичайний запуск — корінь проєкту. Зібраний .exe — тека, де лежить
    сам .exe.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource(*parts: str) -> Path:
    """Файл усередині застосунку (іконка, картинки).

    У зібраному .exe ресурси лежать у теці розпакування `sys._MEIPASS`.
    """
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parents[1]
    return root.joinpath(*parts)


__all__ = ["app_folder", "is_frozen", "resource"]
