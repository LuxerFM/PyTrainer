"""Журнал помилок: що ще «висить», а що вже закрито — і чим саме закрито.

Ідея проста: помилка зникає зі списку не тоді, коли задачу «якось здано», а
тоді, коли її здано **сам**. Тому три стани, а не два:

    відкрито          — після останньої помилки чистого проходу не було
    закрито з допомогою — здав, але з підказкою або вставленим розв'язком
    закрито           — здав сам, без підказок і без розв'язку

Навіщо третій стан: якщо вважати «закрито» будь-яке здавання, найкорисніший
список у тренажері перетворюється на історію страждань, яку людина привчиться
ігнорувати. А якщо рахувати закритим лише чисте здавання, то старий NameError
висить вічно навіть після того, як усе давно працює. Середній варіант чесний:
«ти це виправив, але з опорою — варто повернутись холодним повторенням».

Модуль не знає ні про Qt, ні про тижневий огляд: він лише читає базу й
класифікує записи, тому його легко перевіряти тестами.
"""

from __future__ import annotations

from dataclasses import dataclass

OPEN = "open"
HELPED = "helped"
CLOSED = "closed"

STATUS_LABEL = {
    OPEN: "відкрито",
    HELPED: "закрито з допомогою",
    CLOSED: "закрито",
}


@dataclass(frozen=True)
class MistakeState:
    """Одна помилка з журналу разом із тим, що з нею сталося далі."""

    task_id: str
    kind: str
    times: int
    last_at: str
    check: str = ""                   # назва перевірки, на якій спіткнувся
    status: str = OPEN
    passed_at: str | None = None      # коли задачу здали (хоч якось)
    clean_at: str | None = None       # коли здали чисто
    manual: bool = False              # зроблено поза тренажером, підказок не було

    @property
    def is_open(self) -> bool:
        return self.status == OPEN

    @property
    def is_closed(self) -> bool:
        return self.status == CLOSED

    @property
    def label(self) -> str:
        return STATUS_LABEL.get(self.status, self.status)


def mistake_states(db, limit: int = 12) -> list[MistakeState]:
    """Класифікує помилки з бази — найсвіжіші першими."""
    states: list[MistakeState] = []
    for row in db.mistake_history(limit):
        task_id = row["task_id"]
        passed_id, clean_id = row["pass_id"], row["clean_id"]
        solved = db.status(task_id) == "done"
        clean_hands = (
            db.hints_used(task_id) == 0 and not db.solution_used(task_id)
        )
        manual = solved and passed_id is None      # галочка за роботу поза тренажером

        if manual:
            status = CLOSED
        elif clean_id is not None and clean_id >= row["last_id"]:
            status = CLOSED
        elif passed_id is not None and passed_id >= row["last_id"]:
            status = CLOSED if clean_hands else HELPED
        else:
            status = OPEN

        states.append(MistakeState(
            task_id=task_id,
            kind=row["error_kind"],
            times=int(row["times"]),
            last_at=row["last_at"],
            check=row["failed_check"] or "",
            status=status,
            passed_at=row["pass_at"],
            clean_at=row["clean_at"],
            manual=manual,
        ))
    return states


def open_states(states: list[MistakeState]) -> list[MistakeState]:
    """Ті, що справді варто тримати перед очима."""
    return [state for state in states if not state.is_closed]


__all__ = [
    "CLOSED",
    "HELPED",
    "OPEN",
    "STATUS_LABEL",
    "MistakeState",
    "mistake_states",
    "open_states",
]
