"""Опис структури навчального плану і маленькі конструктори для файлів-даних.

Ієрархія проста: Місяць → Тема → Задача. У задачі є умова, заготовка коду,
приховані перевірки та підказки.

Щоб не писати довгі словники руками, у файлах-даних користуємось короткими
функціями: task(), code(), stdout(), hint(), solution(), stub().
Приклад:

    task(
        id="w1-hello",
        title="Перший вивід",
        level="Легко",
        statement="<p>Виведи привітання</p>",
        starter='print("...")',
        checks=[stdout("виводить привітання", contains="Привіт")],
        hints=[hint("де шукати", "Тобі потрібна функція print()")],
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Скільки XP дає задача залежно від рівня (якщо не вказано свій xp)
LEVEL_XP = {"Легко": 100, "Середньо": 150, "Складно": 200, "Проєкт": 250}

# Через скільки хвилин активної роботи відкривається розв'язок
DEFAULT_MINUTES = 10


@dataclass(frozen=True)
class Check:
    """Одна прихована перевірка.

    Може бути двох видів:
      * перевірка коду — assert-вираз, який виконується після коду користувача;
      * перевірка виводу — що саме програма надрукувала при заданому вводі.
    """

    name: str
    code: str | None = None
    stdout_contains: str | None = None
    stdout_not_contains: str | None = None
    stdout_equals: str | None = None
    stdout_lines: int | None = None
    stdin: str | None = None

    @property
    def is_stdout(self) -> bool:
        return any(
            value is not None
            for value in (
                self.stdout_contains,
                self.stdout_not_contains,
                self.stdout_equals,
                self.stdout_lines,
            )
        )


@dataclass(frozen=True)
class Hint:
    """Підказка. solution=True — це повний розв'язок, він відкривається по таймеру."""

    title: str
    text: str
    solution: bool = False


@dataclass(frozen=True)
class Task:
    """Одна задача тренажера."""

    id: str
    title: str
    statement: str = ""
    starter: str = ""
    level: str = "Легко"
    xp: int = 0
    stdin: str = ""              # ввід для звичайного запуску (кнопка «Запустити»)
    minutes: int = DEFAULT_MINUTES
    checks: tuple[Check, ...] = ()
    hints: tuple[Hint, ...] = ()
    stub: bool = False           # True — задача ще не написана, тільки позначка в плані

    @property
    def base_xp(self) -> int:
        return self.xp or LEVEL_XP.get(self.level, 100)

    @property
    def solution_hint(self) -> Hint | None:
        for hint_item in self.hints:
            if hint_item.solution:
                return hint_item
        return None

    @property
    def clue_hints(self) -> tuple[Hint, ...]:
        return tuple(h for h in self.hints if not h.solution)


@dataclass(frozen=True)
class Topic:
    title: str
    tasks: tuple[Task, ...] = ()


@dataclass(frozen=True)
class Month:
    title: str
    subtitle: str = ""
    topics: tuple[Topic, ...] = ()


# --------------------------------------------------------------------------
# Конструктори для файлів-даних — щоб дані читались як звичайний текст
# --------------------------------------------------------------------------


def code(name: str, source: str) -> Check:
    """Перевірка коду користувача: assert-вираз.

        code("повертає рядок", "assert isinstance(greet('X'), str)")
    """
    return Check(name=name, code=source)


def stdout(
    name: str,
    *,
    contains: str | None = None,
    not_contains: str | None = None,
    equals: str | None = None,
    lines: int | None = None,
    stdin: str | None = None,
) -> Check:
    """Перевірка того, що програма надрукувала.

        stdout("вітається", contains="Привіт, Аня", stdin="Аня\\n")
    """
    return Check(
        name=name,
        stdout_contains=contains,
        stdout_not_contains=not_contains,
        stdout_equals=equals,
        stdout_lines=lines,
        stdin=stdin,
    )


def hint(title: str, text: str) -> Hint:
    """Підказка без розв'язку."""
    return Hint(title=title, text=text)


def solution(text: str, title: str = "повний розв'язок") -> Hint:
    """Розв'язок: відкривається після таймера активної роботи."""
    return Hint(title=title, text=text, solution=True)


def task(
    id: str,
    title: str,
    statement: str = "",
    starter: str = "",
    *,
    level: str = "Легко",
    xp: int = 0,
    stdin: str = "",
    minutes: int = DEFAULT_MINUTES,
    checks: list[Check] | None = None,
    hints: list[Hint] | None = None,
) -> Task:
    return Task(
        id=id,
        title=title,
        statement=statement,
        starter=starter,
        level=level,
        xp=xp,
        stdin=stdin,
        minutes=minutes,
        checks=tuple(checks or ()),
        hints=tuple(hints or ()),
    )


def stub(id: str, title: str) -> Task:
    """Задача-позначка: план уже є, зміст напишемо пізніше."""
    return Task(id=id, title=title, stub=True)


def topic(title: str, *tasks: Task) -> Topic:
    return Topic(title=title, tasks=tuple(tasks))
