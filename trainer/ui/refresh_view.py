"""Refreshing the side panels: progress, reviews, mistakes, plan, stats.

Extracted from `MainWindow` (split slice 3). The controller holds a pointer
to the window (`w`) and reads its `db`/`session`, drawing via `sidebar`,
`panel` and the window badges.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication

from curriculum import CURRICULUM, find_task, study_tasks

from ..core import scoring
from ..core.digest import weekly_digest
from ..core.mistakes import mistake_states
from ..core.plan import daily_plan
from ..core.stats import overall, weak_topics
from .theme import Colors

if TYPE_CHECKING:
    from .main_window import MainWindow


def _tr(text: str) -> str:
    return QCoreApplication.translate("RefreshView", text)


def _human_when(iso: str) -> str:
    """2026-09-25 → "сьогодні" ("today"), "учора" ("yesterday") or "25.09"."""
    try:
        target = date.fromisoformat(iso)
    except ValueError:
        return iso
    delta = (date.today() - target).days
    if delta == 0:
        return _tr("сьогодні")
    if delta == 1:
        return _tr("учора")
    return target.strftime("%d.%m")


def _human_date(iso: str) -> str:
    """2026-09-26 → "26.09 · через 2 дн." ("26.09 · in 2 days")."""
    try:
        target = date.fromisoformat(iso)
    except ValueError:
        return iso
    text = target.strftime("%d.%m")
    days = (target - date.today()).days
    if days < 0:
        return _tr("{date} · прострочено").format(date=text)
    if days == 0:
        return _tr("{date} · сьогодні").format(date=text)
    return _tr("{date} · через {n} дн.").format(date=text, n=days)


class RefreshView:
    """Recompute of everything database-dependent."""

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
        """Mistake journal: what exactly failed and how many times.

        A mistake stays listed until the task is passed **cleanly** — no
        hints, no solution. Who passed with support sees the yellow "closed
        with help": the list neither pretends all is well nor turns into a
        suffering history — both extremes harm equally.
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
                "tooltip": f'{state.check or _tr("перевірка")}\n'
                           f'{task.level} · {task.base_xp} XP\n\n'
                           + (_tr("Закрито з допомогою — згадай задачу холодним "
                                  "повторенням") if state.status == "helped"
                              else _tr("Натисни, щоб повернутися до задачі")),
            })
        rows.sort(key=lambda row: row["status"] != "open")   # open ones first
        w.sidebar.set_mistakes(rows)

    def refresh_digest(self) -> None:
        """Weekly digest — the same numbers for the page, the menu and the window.

        Recomputed on every progress refresh: a few database queries, and
        thanks to it an open digest window never shows stale numbers.
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
                "when": _tr("{date} · інтервал {n} дн.").format(
                    date=_human_date(row["due_date"]),
                    n=scoring.INTERVALS[depth]),
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
        w.review_badge.setText(_tr("На повторення: {n}").format(n=len(due_rows)))

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
            _tr("Серія: {n} дн.").format(n=streak) if streak != 1
            else _tr("Серія: 1 день")
        )
        self.update_today_badge(streak)

    def update_today_badge(self, streak: int) -> None:
        """Today-practice reminder — the day streak does not wait."""
        w = self.w
        today = w.db.attempts_per_day(days=1).get(date.today().isoformat(), 0)
        if today:
            w.today_badge.setText(_tr("Сьогодні: {n} запусків ✓").format(n=today))
            w.today_badge.setStyleSheet(f"color: {Colors.success};")
            return

        if streak:
            w.today_badge.setText(_tr("Сьогодні: 0 — не втрать серію"))
            w.today_badge.setStyleSheet(f"color: {Colors.warn};")
        else:
            w.today_badge.setText(_tr("Сьогодні: 0 запусків"))
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
