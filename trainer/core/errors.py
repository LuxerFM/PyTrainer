"""Людські пояснення помилок Python.

Traceback англійською лякає новачка. Тут ми перекладаємо найчастіші помилки
українською, показуємо рядок коду, де все почалося, і підказуємо, що робити.

Модуль не залежить від Qt — ним користується і runner (для панелі «Тести»),
і будь-який майбутній CLI.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    """Розбір однієї помилки: що це, де і що робити."""

    kind: str                 # NameError, TypeError, …
    message: str              # те, що сказав Python (лапки прибираємо)
    meaning: str              # що це означає простою мовою
    advice: str               # що зробити
    line: int | None = None   # номер рядка у файлі користувача
    source: str = ""          # сам рядок коду

    @property
    def headline(self) -> str:
        return f"{self.kind}: {self.message}" if self.message else self.kind

    def as_text(self) -> str:
        """Готовий текст для консолі / панелі тестів.

        Назву помилки лишаємо — це частина навчання: за тиждень людина
        впізнає NameError з першого погляду.
        """
        parts = [f"{self.kind} — {self.meaning}"]
        if self.source:
            where = f"рядок {self.line}: " if self.line else ""
            parts.append(f"Твій код → {where}{self.source}")
        elif self.line:
            parts.append(f"Це сталося в рядку {self.line}.")
        parts.append(f"Що робити: {self.advice}")
        return "\n".join(parts)


# Що означає помилка і що з нею робити.
EXPLANATIONS: dict[str, tuple[str, str]] = {
    "NameError": (
        "Python не знає такого імені — десь друкарська помилка або змінна "
        "ще не створена.",
        "Перевір написання (print ≠ Print, True ≠ true) і чи створив змінну "
        "вище. Текстові значення беруться в лапки: name = \"Аня\".",
    ),
    "UnboundLocalError": (
        "Ти використав змінну всередині функції до того, як їй щось присвоїв.",
        "Або присвой значення до використання, або передавай його як "
        "параметр, а не як глобальну змінну.",
    ),
    "TypeError": (
        "Ти змішав несумісні типи — найчастіше рядок із числом.",
        "Перетвори значення: int(text), float(text), str(number). Пам'ятай, "
        "що input() завжди повертає рядок. Для None-значень перевір, чи "
        "функція щось повертає (забутий return — класика).",
    ),
    "ValueError": (
        "Тип правильний, але значення не підходить.",
        "Найчастіше це int(\"щось\") або розпакування не тієї кількості "
        "значень. Перевір дані перед перетворенням.",
    ),
    "IndentationError": (
        "Поламані відступи — Python визначає блоки коду саме ними.",
        "Відступ — рівно 4 пробіли на кожен рівень. Після if / for / while / "
        "def ставиться двокрапка, а тіло зсувається на 4 пробіли. Не мішай "
        "табуляцію з пробілами.",
    ),
    "TabError": (
        "В одному файлі змішані табуляції й пробіли.",
        "Увімкни в редакторі «Insert spaces» і перероби відступи пробілами.",
    ),
    "SyntaxError": (
        "Python навіть не зміг прочитати код — десь ламається синтаксис.",
        "Шукай у вказаному рядку (і рядком вище) незакриту дужку, лапку, "
        "забуту двокрапку після if/for/def або зайву кому.",
    ),
    "KeyError": (
        "У словнику немає такого ключа.",
        "Скористайся .get(key) або .get(key, 0) — вони не падають. Або "
        "перевір ключ до звернення: if key in data.",
    ),
    "IndexError": (
        "Ти звернувся до елемента, якого немає — індекс за межами списку.",
        "Пам'ятай: індекси з нуля, останній — len(items) - 1. Для останнього "
        "елемента є items[-1]. Перевір len(items) перед циклом.",
    ),
    "ZeroDivisionError": (
        "Ділення на нуль.",
        "Перевір знаменник перед діленням: if count: average = total / count. "
        "Класика — ділення на len() порожнього списку, тому перевіряй, чи "
        "список не порожній.",
    ),
    "AttributeError": (
        "У цього об'єкта немає такого методу або поля.",
        "Перевір тип: type(value). Часто причина — забутий виклик методу: "
        "text.lower() замість text.lower, або значення не того типу.",
    ),
    "FileNotFoundError": (
        "Python не знайшов файл за вказаною адресою.",
        "Перевір ім'я й папку. У тренажері файли задачі лежать поряд із "
        "кодом, тому достатньо імені без шляху. Для свого файлу — "
        "Path(\"data.txt\").exists().",
    ),
    "RecursionError": (
        "Функція викликає себе занадто багато разів — немає умови зупинки.",
        "Додай базовий випадок: if простий_випадок: return ...",
    ),
    "ModuleNotFoundError": (
        "Немає такого модуля — він або не встановлений, або названий інакше.",
        "Перевір імпорт. Для задачі з кількома файлами переконайся, що "
        "імпортуєш саме той файл, який є в умові задачі.",
    ),
    "ImportError": (
        "Модуль є, але з нього не вдалось імпортувати потрібне ім'я.",
        "Перевір назву функції чи класу в import ... from ...",
    ),
    "StopIteration": (
        "Ти взяв елемент із next(), а ітератор уже скінчився.",
        "Скористайся звичайним for або next(iterator, default).",
    ),
    "OverflowError": (
        "Число вийшло за межі, які підтримує тип.",
        "Перевір, чи не зациклилась формула — часто це безмежний цикл, "
        "який множить число.",
    ),
    "MemoryError": (
        "Програмі забракло пам'яті.",
        "Найчастіше це список, який росте в нескінченному циклі. Перевір "
        "умову виходу з while.",
    ),
    "PermissionError": (
        "Немає дозволу читати або писати цей файл.",
        "Закрий файл у Excel або іншій програмі й спробуй знову.",
    ),
    "AssertionError": (
        "Перевірка значення не зійшлась: код працює, але результат не той, "
        "який очікували.",
        "Подивись, що саме повертає твоя функція — додай тимчасово "
        "print(результат) і порівняй із умовою задачі. Перевір тип: "
        "іноді потрібен рядок, а виходить число.",
    ),
    "TimeoutError": (
        "Операція не встигла завершитись за відведений час.",
        "Перевір умову виходу з циклу.",
    ),
    "JSONDecodeError": (
        "Текст не схожий на коректний JSON.",
        "У JSON лапки тільки подвійні, коми після останнього елемента немає, "
        "а ключі завжди в лапках.",
    ),
}

# Exception з інших бібліотек: name → (що це, що робити)
_KIND_RE = re.compile(
    r"^(?P<kind>[A-Za-z_][A-Za-z0-9_.]*"
    r"(?:Error|Exception|Warning|Exit|Interrupt|Iteration))"
    r"(?::\s*(?P<message>.*))?$"
)

_LOCATION_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)')

# Ім'я файлу, у який тренажер складає код користувача
_ENTRYPOINT = "solution.py"

# «Порожні» повідомлення, які нічого не додають
_EMPTY_MESSAGES = {"", "None"}


def _strip_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def _find_exception(stderr: str) -> tuple[str, str] | None:
    """Шукає останній рядок traceback виду `NameError: ...`."""
    for line in reversed(stderr.strip().splitlines()):
        match = _KIND_RE.match(line.strip())
        if match:
            return match.group("kind"), (match.group("message") or "").strip()
    return None


def _is_user_file(name: str) -> bool:
    """Чи цей файл із traceback належить коду користувача.

    Python 3.11+ пише у traceback **абсолютний** шлях, а не просто
    «solution.py» — саме на цьому ламався пошук рядка. Тому порівнюємо
    базове ім'я, а як запасний варіант відкидаємо явно не наші файли:
    псевдофайли (`<тест>`, `<string>`) і все зі стандартної бібліотеки.
    """
    base = os.path.basename(name)
    if base == _ENTRYPOINT:
        return True
    if name.startswith("<") and name.endswith(">"):
        return False
    if name.startswith(sys.prefix) or "site-packages" in name:
        return False
    if base.startswith("frozen") or base == "runpy.py":
        return False
    return True


def _find_location(stderr: str) -> tuple[int | None, str]:
    """Знаходить рядок коду користувача з traceback.

    Повертає (номер рядка, сам код). Спершу шукаємо кадр саме з файлу
    користувача (solution.py) — він найточніший, — і лише якщо такого немає,
    беремо найглибший кадр, який не схожий на бібліотечний.
    """
    lines = stderr.splitlines()
    fallback: tuple[int, str] | None = None

    for index in range(len(lines) - 1, -1, -1):
        match = _LOCATION_RE.search(lines[index])
        if not match or not _is_user_file(match.group("file")):
            continue

        number = int(match.group("line"))
        source = ""
        if index + 1 < len(lines):
            candidate = lines[index + 1]
            stripped = candidate.strip()
            if stripped and not stripped.startswith("File "):
                source = stripped

        if os.path.basename(match.group("file")) == _ENTRYPOINT:
            return number, source
        if fallback is None:
            fallback = (number, source)

    return fallback if fallback is not None else (None, "")


def _build(kind: str, message: str, line: int | None, source: str) -> Explanation:
    """Пояснення для конкретного типу помилки."""
    known = EXPLANATIONS.get(kind)
    if known is not None:
        meaning, advice = known
    else:
        # невідомий тип — пояснюємо загально, але не вигадуємо зайвого
        meaning = (
            f"Python зупинився з помилкою {kind}. Назва типу підказує, у чому "
            "річ: …Error означає збій під час виконання."
        )
        advice = (
            "Прочитай повідомлення вище: там сказано, на чому саме "
            "спіткнувся код. У 9 випадках із 10 винен рядок, який щойно "
            "додав."
        )

    if message in _EMPTY_MESSAGES:
        message = ""
    elif kind == "AssertionError":
        message = _strip_quotes(message)

    return Explanation(
        kind=kind, message=message, meaning=meaning, advice=advice,
        line=line, source=source,
    )


def analyse(stderr: str) -> Explanation | None:
    """Розбирає stderr і повертає пояснення (або None, якщо помилки немає)."""
    if not stderr or not stderr.strip():
        return None

    found = _find_exception(stderr)
    line, source = _find_location(stderr)

    if found is None:
        # немає розпізнаної помилки, але текст є (наприклад, обрізаний traceback)
        return Explanation(
            kind="Помилка",
            message="",
            meaning="Програма не завершилась нормально, але повний текст "
                    "помилки ми не розпізнали.",
            advice="Подивись консоль нижче: останній рядок зазвичай і є "
                   "причиною.",
            line=line,
            source=source,
        )

    return _build(found[0], found[1], line, source)


def analyse_short(text: str) -> Explanation | None:
    """Розбирає короткий текст помилки без traceback.

    Потрібно для прихованих перевірок: харнес ловить виняток і зберігає лише
    один рядок на кшталт «AssertionError: 2 != 3». Повертає None, якщо це не
    схоже на помилку з назвою типу (наприклад, «У виводі немає «Привіт»»),
    щоб не видавати вигадане пояснення за справжнє.
    """
    if not text or not text.strip():
        return None
    found = _find_exception(text.splitlines()[-1])
    if found is None:
        return None
    return _build(found[0], found[1], None, "")


def explain(stderr: str) -> str:
    """Короткий готовий текст для інтерфейсу (порожньо, якщо все гаразд)."""
    found = analyse(stderr)
    return found.as_text() if found else ""


def kind_of(stderr: str) -> str:
    """Лише назва помилки — для компактного підпису в списку перевірок."""
    found = analyse(stderr)
    return found.kind if found else ""


__all__ = ["Explanation", "analyse", "analyse_short", "explain", "kind_of",
           "EXPLANATIONS"]
