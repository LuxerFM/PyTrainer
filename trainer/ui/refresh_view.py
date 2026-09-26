"""Оновлення бічних панелей: прогрес, повторення, помилки, план, статистика.

Витягнуто з `MainWindow` (зріз 3 розпилу). Контролер тримає вказівник на
вікно (`w`) і читає його `db`/`session`, а малює через `sidebar`, `panel`
і бейджі вікна.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from curriculum import CURRICULUM, find_task, study_tasks

from ..core import scoring
from ..core.digest import weekly_digest
from ..core.mistakes import mistake_states
from ..core.plan import daily_plan
from ..core.stats import overall, weak_topics
from .theme import Colors

if TYPE_CHECKING:
    from .main_window import MainWindow


def _human_when(iso: str) -> str:
    """2026-09-25 → «сьогодні», «учора» або «25.09»."""
    try:
        target = date.fromisoformat(iso)
    except ValueError:
        return iso
    delta = (date.today() - target).days
    if delta == 0:
        return "сьогодні"
    if delta == 1:
        return "учора"
    return target.strftime("%d.%m")


def _human_date(iso: str) -> str:
    """2026-09-26 → «26.09 · через 2 дн.»"""
    try:
        target = date.fromisoformat(iso)
    except ValueError:
        return iso
    text = target.strftime("%d.%m")
    days = (target - date.today()).days
    if days < 0:
        return f"{text} · прострочено"
    if days == 0:
        return f"{text} · сьогодні"
    return f"{text} · через {days} дн."


class RefreshView:
    """Перерахунок усього, що залежить від бази."""

    def __init__(self, window: MainWindow) -> None:
        self.w = window

    def refresh_all(self) -> None:
        w = self.w
        w.sidebar.load_curriculum(CURRICULUM, w.db.statuses())
        self.refresh_progress()
        self.refresh_reviews()
        self.refresh_mistakes()
        self.refresh_plan()
        self.refresh_stats()
        self.refresh_digest()

    def refresh_mistakes(self) -> None:
        """Журнал помилок: що саме не пройшло й скільки разів.

        Помилка лишається у списку, доки задачу не здано **чисто** — без
        підказок і розв'язку. Хто здав із опорою, бачить жовте «закрито з
        допомогою»: список не вдає, ніби все гаразд, і не перетворюється на
        історію страждань — обидві крайнощі однаково шкідливі.
        """
        w = self.w
        rows = []
        for state in mistake_states(w.db):
            task = find_task(state.task_id)
            if task is None or state.is_closed:
                continue
            rows.append({
                "task_id": task.id,
                "title": task.title,
                "kind": state.kind,
                "times": state.times,
                "when": _human_when(state.last_at[:10]),
                "status": state.status,
                "status_label": state.label,
                "tooltip": f'{state.check or "перевірка"}\n'
                           f'{task.level} · {task.base_xp} XP\n\n'
                           + ("Закрито з допомогою — згадай задачу холодним "
                              "повторенням" if state.status == "helped"
                              else "Натисни, щоб повернутися до задачі"),
            })
        rows.sort(key=lambda row: row["status"] != "open")   # спершу відкриті
        w.sidebar.set_mistakes(rows)

    def refresh_digest(self) -> None:
        """Тижневий огляд — одні розрахунки на сторінку, меню й вікно.

        Рахуємо на кожне оновлення прогресу: це кілька запитів до бази, і
        завдяки цьому відкрите вікно огляду ніколи не показує старих цифр.
        """
        w = self.w
        w._digest = weekly_digest(w.db)
        w.sidebar.set_digest_summary(w._digest)
        if w.digest_dialog is not None:
            w.digest_dialog.set_digest(w._digest)

    def refresh_plan(self) -> None:
        self.w.sidebar.set_plan(daily_plan(self.w.db))

    def refresh_progress(self) -> None:
        self.w.sidebar.set_progress(self.done_count(), len(study_tasks()))

    def done_count(self) -> int:
        return sum(1 for task in study_tasks()
                   if self.w.db.status(task.id) == "done")

    def refresh_reviews(self) -> None:
        w = self.w
        due_rows = []
        for row in w.db.due_reviews():
            task = find_task(row["task_id"])
            if task is None:
                continue
            depth = min(row["interval_index"], len(scoring.INTERVALS) - 1)
            due_rows.append({
                "task_id": task.id,
                "title": task.title,
                "when": f'{_human_date(row["due_date"])} · '
                        f'інтервал {scoring.INTERVALS[depth]} дн.',
                "tooltip": f"{task.level} · {task.base_xp} XP",
            })

        later_rows = []
        for row in w.db.upcoming_reviews():
            task = find_task(row["task_id"])
            if task is None:
                continue
            later_rows.append({
                "task_id": task.id,
                "title": task.title,
                "when": _human_date(row["due_date"]),
                "tooltip": f"{task.level} · {task.base_xp} XP",
            })

        w.sidebar.set_reviews(due_rows, later_rows)
        w.review_badge.setText(f"На повторення: {len(due_rows)}")

    def refresh_stats(self) -> None:
        w = self.w
        rows = w.db.task_results()
        summary = w.session.summary()
        w.sidebar.set_stats(
            overall(rows),
            weak_topics(rows),
            w.db.attempts_per_day(),
            summary["xp"],
            summary["streak"],
            w.db.total_active_seconds(),
            w.db.xp_by_day(),
        )
        w.xp_badge.setText(f'XP {summary["xp"]}')
        streak = summary["streak"]
        w.streak_badge.setText(
            f"Серія: {streak} дн." if streak != 1 else "Серія: 1 день"
        )
        self.update_today_badge(streak)

    def update_today_badge(self, streak: int) -> None:
        """Нагадування про сьогоднішню практику — серія днів не чекає."""
        w = self.w
        today = w.db.attempts_per_day(days=1).get(date.today().isoformat(), 0)
        if today:
            w.today_badge.setText(f"Сьогодні: {today} запусків ✓")
            w.today_badge.setStyleSheet(f"color: {Colors.success};")
            return

        if streak:
            w.today_badge.setText("Сьогодні: 0 — не втрать серію")
            w.today_badge.setStyleSheet(f"color: {Colors.warn};")
        else:
            w.today_badge.setText("Сьогодні: 0 запусків")
            w.today_badge.setStyleSheet(f"color: {Colors.muted};")

    def load_history(self, task_id: str) -> None:
        w = self.w
        w.panel.set_history(
            w.db.history(task_id),
            solved=w.db.status(task_id) == "done",
            best_xp=w.db.best_xp(task_id) + w.db.bonus_xp(task_id),
            hints_used=w.db.hints_used(task_id),
            active_seconds=w.db.active_seconds(task_id),
        )


__all__ = ["RefreshView"]
