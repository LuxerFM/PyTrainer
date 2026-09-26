"""Виконання чужого файлу тим самим інтерпретатором — режим `--exec-runner`.

Навіщо це окремий режим. Код користувача завжди виконується в **окремому**
процесі: інакше `while True` у розв'язку повісив би весь тренажер. Поки
застосунок запускається з коду, окремий процес — це просто `python`. Але в
зібраному `.exe` `sys.executable` вказує на **сам тренажер**, і тоді звичний
запуск робить не те, що треба: замість розв'язку стартує друге вікно
PyTrainer. Вердикт не приходить ніколи, процес переживає таймаут і тримає
тимчасові файли, тому їх ще й не вдається прибрати.

Тому `.exe` запускає сам себе з прапорцем `--exec-runner`: цей режим виконує
вказаний файл як `__main__` — вбудованим інтерпретатором, без Qt і без вікна —
і повертає його код виходу. Для runner-а різниці не видно: там, де раніше
був `python`, тепер `.exe`, і код користувача працює так само.

Дивись також `trainer/cli.py` — там порядок, у якому цей режим перевіряється
раніше за імпорт PySide6, і `ensure_streams()` — чому без правки кодування
український вивід у `.exe` стає сміттям.
"""

from __future__ import annotations

import io
import os
import runpy
import sys
import traceback

from ..paths import is_frozen

FLAG = "--exec-runner"


def script_from(argv: list[str]) -> str:
    """Файл, який треба виконати (порожній рядок, якщо його не передали)."""
    if FLAG not in argv:
        return ""
    for item in argv[argv.index(FLAG) + 1:]:
        if not item.startswith("-"):
            return item
    return ""


def _attach(index: int, mode: str) -> object:
    """Текстовий потік на справжній дескриптор 0, 1 або 2."""
    try:
        buffering = 1 if mode == "w" else -1
        return os.fdopen(index, mode, encoding="utf-8", buffering=buffering, closefd=False)
    except OSError:
        return open(os.devnull, mode, encoding="utf-8")


def ensure_streams() -> None:
    """Робить стандартні потоки UTF-8 — інакше кирилиця перетворюється в сміття.

    Тут дві різні біди з одним коренем. Віконний `.exe` може лишити `sys.stdout`
    порожнім — тоді `print` у коді користувача просто зникає, а не потрапляє в
    файл, який читає runner. А якщо не лишити, PyInstaller приєднує потоки з
    ANSI-кодуванням системи (у нас cp1251) — і тоді весь український вивід
    перетворюється на «??????». Runner читає цей вивід як UTF-8, тому кодування
    мусить збігатись **завжди**: інакше «код виводить не те» виглядало б як
    помилка в розв'язку, якої там немає.

    Кодування перевіряємо лише в зібраному `.exe`: у консолі ж із коду воно
    своє й правильне, і переводити його в UTF-8 навмання означало б зіпсувати
    кирилицю в старому консольному вікні Windows.
    """
    frozen = is_frozen()
    for index, name, mode in ((0, "stdin", "r"), (1, "stdout", "w"), (2, "stderr", "w")):
        stream = getattr(sys, name, None)
        if stream is None:
            setattr(sys, name, _attach(index, mode))
            continue
        encoding = getattr(stream, "encoding", None)
        if not frozen or encoding is None:
            continue
        if encoding.lower().replace("-", "_") in ("utf_8", "utf8"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, OSError, ValueError, io.UnsupportedOperation):
            # Не текстовий потік, який уміє переналаштуватись (тести, підмінені
            # потоки) — лишаємо як є, це не той випадок, який ми лікуємо.
            pass


def _exit_code(code: object) -> int:
    """Код виходу з `SystemExit` — так само, як це робить CPython."""
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    print(code, file=sys.stderr or sys.stdout)
    return 1


def main(argv: list[str] | None = None) -> int:
    """Виконує файл із `--exec-runner` і повертає код його виходу."""
    argv = list(sys.argv if argv is None else argv)
    script = script_from(argv)
    ensure_streams()
    if not script:
        print(f"{FLAG}: не вказано файл для виконання", file=sys.stderr)
        return 2

    # Усе як у звичайного `python файл.py`: абсолютний шлях у sys.argv[0],
    # папка файла першою в sys.path (тому `import utils` зі своєї ж теки
    # працює) і та сама тека як робоча.
    arguments = [item for item in argv[argv.index(FLAG) + 1:] if not item.startswith("-")]
    script = os.path.abspath(script)
    folder = os.path.dirname(script)
    sys.argv = [script] + arguments[1:]
    if folder not in sys.path:
        sys.path.insert(0, folder)
    os.chdir(folder)

    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as stop:
        return _exit_code(stop.code)
    except BaseException:
        # Помилку друкуємо самі, а не віддаємо її "назовні": у зібраному
        # віконному .exe необроблений виняток перетворюється на діалог із
        # кнопкою «ОК». Діалог чекав би на клік, тому звичайна помилка в
        # розв'язку виглядала б як таймаут — і без пояснення.
        traceback.print_exc()
        return 1
    return 0


__all__ = ["FLAG", "ensure_streams", "main", "script_from"]
