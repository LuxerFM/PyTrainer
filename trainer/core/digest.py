"""Тижневий огляд: що сталося за сім днів і що з цим робити.

Щоденний план відповідає на питання «що робити сьогодні». Раз на тиждень
потрібне інше питання: «і що з цього вийшло?». Без нього навчання
перетворюється на стрічку справ: задачі здаються, помилки накопичуються, а чи
стає легше — не видно нізвідки.

Модуль не знає ні про Qt, ні про календар: він бере журнал спроб, чергу
повторень і журнал помилок — і складає з них те, що можна прочитати за дві
хвилини. Тому його легко перевіряти тестами, а той самий звіт можна надрукувати
в консоль або зберегти у файл.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from curriculum import find_task, study_tasks, topic_of

from .mistakes import MistakeState, mistake_states
from .plan import pick_weak_task
from .stats import weak_topics

DAYS = 7
MAX_WEAK = 3
MAX_HARDEST = 3
NEXT_TASKS = 3

MONTHS = (
    "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
)


def _human_day(iso: str) -> str:
    """2026-09-26 → «26 вересня»."""
    try:
        day = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{day.day} {MONTHS[day.month - 1]}"


def _range_text(start: str, end: str) -> str:
    """«20–26 вересня» або «29 вересня – 5 жовтня», якщо місяці різні."""
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first.month == last.month:
        return f"{first.day}–{last.day} {MONTHS[last.month - 1]}"
    return f"{_human_day(start)} – {_human_day(end)}"


@dataclass(frozen=True)
class WeeklyDigest:
    """Один тиждень навчання в числах і списках."""

    start: str
    end: str
    solved: list[tuple[str, str]] = field(default_factory=list)      # (id, назва)
    passes: int = 0
    failures: int = 0
    days_active: int = 0
    streak: int = 0
    xp: int = 0
    weakest: list[tuple[str, float]] = field(default_factory=list)
    hardest: list[tuple[str, int, str]] = field(default_factory=list)  # id, назва, провалів
    mistakes: list[MistakeState] = field(default_factory=list)
    reviews_due: int = 0
    weak_pick: tuple[str, str] | None = None                          # (id, назва)
    weak_topic: str = ""                # до якої слабкої теми ця задача
    next_tasks: list[tuple[str, str]] = field(default_factory=list)

    # ---------- те, що читає людина ----------

    @property
    def title(self) -> str:
        return f"Тиждень {_range_text(self.start, self.end)}"

    @property
    def active(self) -> bool:
        return bool(self.passes or self.failures)

    @property
    def checks(self) -> int:
        return self.passes + self.failures

    @property
    def open_mistakes(self) -> list[MistakeState]:
        return [state for state in self.mistakes if state.is_open]

    @property
    def helped_mistakes(self) -> list[MistakeState]:
        return [state for state in self.mistakes if state.status == "helped"]

    @property
    def closed_mistakes(self) -> list[MistakeState]:
        return [state for state in self.mistakes if state.is_closed]

    @property
    def verdict(self) -> str:
        """Одне речення, з яким людина закриває тиждень."""
        if not self.active:
            return (
                "Цього тижня занять не було. Один вечір на 30 хвилин — і "
                "тиждень уже не порожній; головне не пропустити два рази підряд."
            )
        if self.days_active <= 2:
            return (
                f"Тиждень вийшов рваним: {self.days_active} з 7 днів. Прогрес "
                "дає ритм, а не подвиг — краще п'ять днів по 40 хвилин, ніж "
                "один вечір на чотири години."
            )
        if self.open_mistakes:
            return (
                f"Тиждень робочий: {self.checks} перевірок. Почни наступний з "
                f"відкритих помилок — їх {len(self.open_mistakes)}."
            )
        return (
            f"Тиждень закрито чисто: {self.passes} успішних перевірок і жодної "
            "відкритої помилки. Так тримати."
        )

    def as_lines(self) -> list[str]:
        """Короткий текстовий вигляд — для консолі й тестів."""
        lines = [
            self.title,
            f"Здано нових: {len(self.solved)} · перевірок: {self.checks} "
            f"({self.passes} успішних) · днів із роботою: {self.days_active} із {DAYS}",
            f"Серія: {self.streak} дн. · XP загалом: {self.xp}",
            f"Помилки: {len(self.open_mistakes)} відкрито · "
            f"{len(self.helped_mistakes)} закрито з допомогою · "
            f"{len(self.closed_mistakes)} закрито",
            self.verdict,
        ]
        for task_id, title in self.solved:
            lines.append(f"  ✓ {title} ({task_id})")
        for task_id, title, count in self.hardest:
            lines.append(f"  ⚠ {title} — {count} провалів ({task_id})")
        return lines

    def as_markdown(self, *, generated: datetime | None = None) -> str:
        """Звіт, який можна зберегти й перечитати через місяць."""
        moment = (generated or datetime.now()).strftime("%d.%m.%Y %H:%M")
        out = [
            f"# {self.title}",
            "",
            f"_Звіт створено {moment}. Файл генерується тренажером — "
            "правки перезапишуться._",
            "",
            "| | |",
            "|---|---|",
            f"| Здано нових задач | {len(self.solved)} |",
            f"| Перевірок | {self.checks} ({self.passes} успішних) |",
            f"| Днів із роботою | {self.days_active} із {DAYS} |",
            f"| Серія | {self.streak} дн. |",
            f"| XP загалом | {self.xp} |",
            "",
            f"**{self.verdict}**",
            "",
        ]

        out += ["## Що здано", ""]
        out += [f"- {title} (`{task_id}`)" for task_id, title in self.solved] \
            or ["- Нічого — і це нормально, якщо тиждень був важкий."]
        out.append("")

        out += ["## Найважче", ""]
        out += [f"- {title} — {count} провалів (`{task_id}`)"
                for task_id, title, count in self.hardest] \
            or ["- Провалів не було."]
        out.append("")

        out += ["## Помилки", ""]
        if self.mistakes:
            out += ["| Задача | Помилка | Разів | Стан |", "|---|---|---|---|"]
            out += [
                f"| {self._task_title(state.task_id)} | `{state.kind}` | "
                f"{state.times} | {state.label} |"
                for state in self.mistakes
            ]
        else:
            out.append("За тиждень жодної помилки в журналі.")
        out.append("")

        out += ["## Слабкі теми", ""]
        out += [f"- {name} — успішних спроб {round(rate * 100)}%"
                for name, rate in self.weakest] or ["- Слабких тем не видно."]
        out.append("")

        out += ["## Що робити далі", ""]
        if self.reviews_due:
            out.append(f"- Час повторити: {self.reviews_due} задач — вони вже "
                       "в черзі повторень.")
        if self.weak_pick:
            topic = f"«{self.weak_topic}»" if self.weak_topic else ""
            out.append(f"- Слабка тема{topic}: {self.weak_pick[1]} "
                       f"(`{self.weak_pick[0]}`)")
        for task_id, title in self.next_tasks:
            out.append(f"- Нова задача: {title} (`{task_id}`)")
        out.append("")
        return "\n".join(out)

    @staticmethod
    def _task_title(task_id: str) -> str:
        task = find_task(task_id)
        return task.title if task else task_id


def weekly_digest(db, *, today: date | None = None, days: int = DAYS) -> WeeklyDigest:
    """Складає огляд за останні `days` днів (останній день — сьогодні)."""
    last = today or date.today()
    first = last - timedelta(days=max(1, days) - 1)
    start, end = first.isoformat(), last.isoformat()

    attempts = db.attempts_between(start, end)
    passes = sum(1 for row in attempts if row["ok"])
    failures = len(attempts) - passes
    days_active = len({row["created_at"][:10] for row in attempts})

    statuses = db.statuses()
    solved = []
    for task_id in db.solved_between(start, end):
        task = find_task(task_id)
        if task is not None:
            solved.append((task_id, task.title))

    hard: dict[str, int] = {}
    for row in attempts:
        if not row["ok"] and row["with_checks"]:
            hard[row["task_id"]] = hard.get(row["task_id"], 0) + 1
    hardest = sorted(hard.items(), key=lambda item: (-item[1], item[0]))[:MAX_HARDEST]
    hardest_tasks = [
        (task_id, task.title if (task := find_task(task_id)) else task_id, count)
        for task_id, count in hardest
    ]

    weak = weak_topics(db.task_results())[:MAX_WEAK]
    picked = pick_weak_task(db, statuses)
    weak_pick = (picked[0].id, picked[0].title) if picked else None
    weak_topic = picked[1] if picked else ""

    next_tasks = [
        (task.id, task.title)
        for task in study_tasks()
        if statuses.get(task.id) != "done"
    ][:NEXT_TASKS]

    mistakes = [
        state for state in mistake_states(db)
        if state.last_at[:10] >= start
    ]

    return WeeklyDigest(
        start=start,
        end=end,
        solved=solved,
        passes=passes,
        failures=failures,
        days_active=days_active,
        streak=db.streak(),
        xp=db.total_xp(),
        weakest=[(stat.name, stat.success_rate) for stat in weak],
        hardest=hardest_tasks,
        mistakes=mistakes,
        reviews_due=len(db.due_reviews(last)),
        weak_pick=weak_pick,
        weak_topic=weak_topic,
        next_tasks=next_tasks,
    )


def write_digest(path: str | Path, digest: WeeklyDigest,
                 *, generated: datetime | None = None) -> Path:
    """Зберігає звіт у файл (markdown) і повертає шлях до нього."""
    target = Path(path)
    target.write_text(digest.as_markdown(generated=generated), encoding="utf-8")
    return target


__all__ = [
    "DAYS",
    "MAX_HARDEST",
    "MAX_WEAK",
    "NEXT_TASKS",
    "WeeklyDigest",
    "weekly_digest",
    "write_digest",
]
