"""Mistake journal: what still "hangs" vs already closed — and closed by what.

The idea is simple: a mistake leaves the list not when the task is "somehow
passed" but when it is passed **alone**. Hence three states, not two:

    open              — no clean pass since the last mistake
    closed with help  — passed, but with a hint or a pasted solution
    closed            — passed alone, no hints, no solution

Why the third state: counting any pass as "closed" turns the most useful list
in the trainer into a history of suffering the human learns to ignore. But
counting only clean passes leaves an old NameError hanging forever after
everything long works. The middle is honest: "you fixed it, but with support —
worth a cold-review revisit".

The module knows neither Qt nor the weekly digest: it only reads the database
and classifies rows, so tests cover it easily.
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
    """One journal mistake together with what happened to it next."""

    task_id: str
    kind: str
    times: int
    last_at: str
    check: str = ""                   # name of the check tripped on
    status: str = OPEN
    passed_at: str | None = None      # when the task was passed (somehow)
    clean_at: str | None = None       # when passed cleanly
    manual: bool = False              # done outside the trainer, no hints involved

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
    """Classifies database mistakes — newest first."""
    states: list[MistakeState] = []
    for row in db.mistake_history(limit):
        task_id = row["task_id"]
        passed_id, clean_id = row["pass_id"], row["clean_id"]
        solved = db.status(task_id) == "done"
        clean_hands = (
            db.hints_used(task_id) == 0 and not db.solution_used(task_id)
        )
        manual = solved and passed_id is None      # tick for work outside the trainer

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
    """The ones truly worth keeping in sight."""
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
