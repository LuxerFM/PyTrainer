"""Уся пам'ять тренажера — у базі SQLite (файл pytrainer.db).

SQLite вбудований у Python, тому нічого встановлювати не треба. Таблиці:

    progress  — стан кожної задачі (todo/current/done), XP, підказки, час
    attempts  — кожен запуск коду з вердиктом (звідси вся статистика)
    reviews   — черга повторень: коли задачу треба згадати знову

Дати зберігаємо рядками у форматі ISO (2026-09-24) — так їх можна сортувати
й порівнювати як звичайний текст.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from . import scoring

DB_PATH = Path(__file__).resolve().parents[2] / "pytrainer.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS progress (
    task_id        TEXT PRIMARY KEY,
    status         TEXT NOT NULL DEFAULT 'todo',
    started_at     TEXT,
    solved_at      TEXT,
    best_xp        INTEGER NOT NULL DEFAULT 0,
    hints_used     INTEGER NOT NULL DEFAULT 0,
    solution_used  INTEGER NOT NULL DEFAULT 0,
    active_seconds REAL NOT NULL DEFAULT 0,
    bonus_xp       INTEGER NOT NULL DEFAULT 0,
    code           TEXT
);

CREATE TABLE IF NOT EXISTS attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    ok          INTEGER NOT NULL,
    with_checks INTEGER NOT NULL,
    xp          INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS attempts_task_idx ON attempts (task_id);
CREATE INDEX IF NOT EXISTS attempts_date_idx ON attempts (created_at);

CREATE TABLE IF NOT EXISTS reviews (
    task_id        TEXT PRIMARY KEY,
    due_date       TEXT NOT NULL,
    interval_index INTEGER NOT NULL DEFAULT 0,
    last_result    INTEGER,
    updated_at     TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


class Database:
    """Обгортка над SQLite з методами під задачі тренажера."""

    def __init__(self, path: str | Path = DB_PATH) -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self._migrate()
        self.connection.commit()

    def _migrate(self) -> None:
        """Додає нові колонки у базу, створену попередньою версією."""
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(progress)")
        }
        if "code" not in columns:
            self.connection.execute("ALTER TABLE progress ADD COLUMN code TEXT")
        if "bonus_xp" not in columns:
            self.connection.execute(
                "ALTER TABLE progress ADD COLUMN bonus_xp INTEGER NOT NULL DEFAULT 0"
            )

    def close(self) -> None:
        self.connection.close()

    # ------------------------------------------------------------------
    # прогрес
    # ------------------------------------------------------------------

    def statuses(self) -> dict[str, str]:
        rows = self.connection.execute("SELECT task_id, status FROM progress")
        return {row["task_id"]: row["status"] for row in rows}

    def status(self, task_id: str) -> str:
        row = self.connection.execute(
            "SELECT status FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return row["status"] if row else "todo"

    def _ensure(self, task_id: str) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO progress (task_id, status) VALUES (?, 'todo')",
            (task_id,),
        )

    def mark_in_progress(self, task_id: str) -> None:
        """Позначає, що задача відкрита (якщо вона ще не здана)."""
        self._ensure(task_id)
        self.connection.execute(
            """
            UPDATE progress
               SET status = 'current',
                   started_at = COALESCE(started_at, ?)
             WHERE task_id = ? AND status != 'done'
            """,
            (_now(), task_id),
        )
        self.connection.commit()

    def mark_solved(self, task_id: str, xp: int) -> None:
        self._ensure(task_id)
        self.connection.execute(
            """
            UPDATE progress
               SET status = 'done',
                   solved_at = COALESCE(solved_at, ?),
                   best_xp = MAX(best_xp, ?)
             WHERE task_id = ?
            """,
            (_now(), xp, task_id),
        )
        self.connection.commit()

    def mark_repeat_passed(self, task_id: str, xp: int) -> None:
        """Повторення пройдено: задача лишається зданою, XP додається до best_xp."""
        self.connection.execute(
            "UPDATE progress SET best_xp = MAX(best_xp, ?) WHERE task_id = ?",
            (xp, task_id),
        )
        self.connection.commit()

    def add_bonus_xp(self, task_id: str, xp: int) -> None:
        """XP за повторення — окремо від best_xp, щоб його не «з'їдав» MAX()."""
        self._ensure(task_id)
        self.connection.execute(
            "UPDATE progress SET bonus_xp = bonus_xp + ? WHERE task_id = ?",
            (xp, task_id),
        )
        self.connection.commit()

    def bonus_xp(self, task_id: str) -> int:
        row = self.connection.execute(
            "SELECT bonus_xp FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return int(row["bonus_xp"]) if row else 0

    def best_xp(self, task_id: str) -> int:
        row = self.connection.execute(
            "SELECT best_xp FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return int(row["best_xp"]) if row else 0

    def saved_code(self, task_id: str) -> str | None:
        """Код, який користувач лишив у редакторі минулого разу."""
        row = self.connection.execute(
            "SELECT code FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return row["code"] if row else None

    def save_code(self, task_id: str, code: str) -> None:
        self._ensure(task_id)
        self.connection.execute(
            "UPDATE progress SET code = ? WHERE task_id = ?", (code, task_id)
        )
        self.connection.commit()

    def hints_used(self, task_id: str) -> int:
        row = self.connection.execute(
            "SELECT hints_used FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return row["hints_used"] if row else 0

    def solution_used(self, task_id: str) -> bool:
        row = self.connection.execute(
            "SELECT solution_used FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return bool(row["solution_used"]) if row else False

    def mark_solution_used(self, task_id: str) -> None:
        """Людина скористалась повним розв'язком (не чіпає лічильник підказок)."""
        self._ensure(task_id)
        self.connection.execute(
            "UPDATE progress SET solution_used = 1 WHERE task_id = ?", (task_id,)
        )
        self.connection.commit()

    def reveal_hint(self, task_id: str, level: int, is_solution: bool = False) -> None:
        self._ensure(task_id)
        self.connection.execute(
            """
            UPDATE progress
               SET hints_used = MAX(hints_used, ?),
                   solution_used = MAX(solution_used, ?)
             WHERE task_id = ?
            """,
            (level, 1 if is_solution else 0, task_id),
        )
        self.connection.commit()

    def active_seconds(self, task_id: str) -> float:
        row = self.connection.execute(
            "SELECT active_seconds FROM progress WHERE task_id = ?", (task_id,)
        ).fetchone()
        return float(row["active_seconds"]) if row else 0.0

    def add_active_seconds(self, task_id: str, seconds: float) -> float:
        self._ensure(task_id)
        self.connection.execute(
            "UPDATE progress SET active_seconds = active_seconds + ? WHERE task_id = ?",
            (seconds, task_id),
        )
        self.connection.commit()
        return self.active_seconds(task_id)

    # ------------------------------------------------------------------
    # спроби
    # ------------------------------------------------------------------

    def record_attempt(
        self, task_id: str, *, ok: bool, with_checks: bool, xp: int = 0
    ) -> None:
        self._ensure(task_id)
        self.connection.execute(
            """
            INSERT INTO attempts (task_id, created_at, ok, with_checks, xp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, _now(), 1 if ok else 0, 1 if with_checks else 0, xp),
        )
        self.connection.commit()

    def attempts_count(self, task_id: str, *, with_checks: bool = True) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS total FROM attempts
             WHERE task_id = ? AND (? = 0 OR with_checks = 1)
            """,
            (task_id, 1 if with_checks else 0),
        ).fetchone()
        return int(row["total"])

    def passes_count(self, task_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS total FROM attempts WHERE task_id = ? AND ok = 1",
            (task_id,),
        ).fetchone()
        return int(row["total"])

    def history(self, task_id: str, limit: int = 30) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                """
                SELECT created_at, ok, with_checks, xp FROM attempts
                 WHERE task_id = ?
                 ORDER BY id DESC LIMIT ?
                """,
                (task_id, limit),
            )
        )

    # ------------------------------------------------------------------
    # повторення
    # ------------------------------------------------------------------

    def schedule_review(self, task_id: str, days: int, interval_index: int) -> None:
        self.connection.execute(
            """
            INSERT INTO reviews (task_id, due_date, interval_index, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                due_date = excluded.due_date,
                interval_index = excluded.interval_index,
                updated_at = excluded.updated_at
            """,
            (task_id, scoring.due_date(days), interval_index, _now()),
        )
        self.connection.commit()

    def schedule_from_result(self, task_id: str, ok: bool) -> tuple[int, int | None]:
        """Оновлює чергу після спроби. Повертає (індекс, днів)."""
        row = self.review(task_id)
        index = row["interval_index"] if row else -1
        new_index, days = scoring.next_interval(index, ok)
        if days is None:
            self.clear_review(task_id)
        else:
            self.schedule_review(task_id, days, new_index)
        return new_index, days

    def clear_review(self, task_id: str) -> None:
        self.connection.execute("DELETE FROM reviews WHERE task_id = ?", (task_id,))
        self.connection.commit()

    def review(self, task_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM reviews WHERE task_id = ?", (task_id,)
        ).fetchone()

    def due_reviews(self, on: date | None = None) -> list[sqlite3.Row]:
        """Задачі, які час повторити (дата настала)."""
        target = (on or date.today()).isoformat()
        return list(
            self.connection.execute(
                "SELECT * FROM reviews WHERE due_date <= ? ORDER BY due_date",
                (target,),
            )
        )

    def upcoming_reviews(self, on: date | None = None) -> list[sqlite3.Row]:
        target = (on or date.today()).isoformat()
        return list(
            self.connection.execute(
                "SELECT * FROM reviews WHERE due_date > ? ORDER BY due_date",
                (target,),
            )
        )

    def all_reviews(self) -> list[sqlite3.Row]:
        return list(
            self.connection.execute("SELECT * FROM reviews ORDER BY due_date")
        )

    # ------------------------------------------------------------------
    # статистика
    # ------------------------------------------------------------------

    def total_xp(self) -> int:
        row = self.connection.execute(
            "SELECT COALESCE(SUM(best_xp + bonus_xp), 0) AS total FROM progress"
        ).fetchone()
        return int(row["total"])

    def total_active_seconds(self) -> float:
        row = self.connection.execute(
            "SELECT COALESCE(SUM(active_seconds), 0) AS total FROM progress"
        ).fetchone()
        return float(row["total"])

    def activity_days(self, limit: int = 120) -> list[str]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT DATE(created_at) AS day FROM attempts
             ORDER BY day DESC LIMIT ?
            """,
            (limit,),
        )
        return [row["day"] for row in rows]

    def streak(self) -> int:
        return scoring.streak_from_days(self.activity_days())

    def attempts_per_day(self, days: int = 56) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT DATE(created_at) AS day, COUNT(*) AS total FROM attempts
             WHERE DATE(created_at) >= DATE('now', ?)
             GROUP BY day
            """,
            (f"-{days} days",),
        )
        return {row["day"]: int(row["total"]) for row in rows}

    def task_results(self) -> list[sqlite3.Row]:
        """Зведення по задачах: спроби, успіхи, XP, черга повторень."""
        return list(
            self.connection.execute(
                """
                SELECT p.task_id,
                       p.status,
                       p.best_xp,
                       p.bonus_xp,
                       p.hints_used,
                       p.solution_used,
                       r.due_date,
                       r.interval_index,
                       COALESCE(a.total, 0)  AS attempts,
                       COALESCE(a.passes, 0) AS passes
                  FROM progress AS p
                  LEFT JOIN (
                       SELECT task_id,
                              COUNT(*) AS total,
                              SUM(ok)  AS passes
                         FROM attempts
                        WHERE with_checks = 1
                        GROUP BY task_id
                  ) AS a ON a.task_id = p.task_id
                  LEFT JOIN reviews AS r ON r.task_id = p.task_id
                """
            )
        )

    # ------------------------------------------------------------------
    # перенесення прогресу (файл progress.json)
    # ------------------------------------------------------------------

    PROGRESS_FIELDS = (
        "task_id", "status", "solved_at", "best_xp", "bonus_xp",
        "hints_used", "solution_used", "active_seconds",
    )

    def snapshot(self) -> dict:
        """Стан прогресу у вигляді словника — його можна зберегти у файл."""
        fields = ", ".join(self.PROGRESS_FIELDS)
        return {
            "version": 1,
            "saved_at": _now(),
            "progress": [
                dict(row)
                for row in self.connection.execute(
                    f"SELECT {fields} FROM progress WHERE status != 'todo'"
                )
            ],
            "reviews": [
                dict(row)
                for row in self.connection.execute(
                    "SELECT task_id, due_date, interval_index, last_result FROM reviews"
                )
            ],
        }

    def restore(self, data: dict) -> int:
        """Відновлює прогрес зі словника. Повертає кількість відновлених задач."""
        restored = 0
        for row in data.get("progress", []):
            self._ensure(row["task_id"])
            self.connection.execute(
                """
                UPDATE progress
                   SET status = ?, solved_at = ?, best_xp = ?, bonus_xp = ?,
                       hints_used = ?, solution_used = ?, active_seconds = ?
                 WHERE task_id = ?
                """,
                (
                    row.get("status", "todo"), row.get("solved_at"),
                    int(row.get("best_xp") or 0), int(row.get("bonus_xp") or 0),
                    int(row.get("hints_used") or 0), int(row.get("solution_used") or 0),
                    float(row.get("active_seconds") or 0), row["task_id"],
                ),
            )
            restored += 1

        for row in data.get("reviews", []):
            self.connection.execute(
                """
                INSERT INTO reviews (task_id, due_date, interval_index, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    due_date = excluded.due_date,
                    interval_index = excluded.interval_index,
                    updated_at = excluded.updated_at
                """,
                (row["task_id"], row["due_date"], int(row.get("interval_index") or 0), _now()),
            )
        self.connection.commit()
        return restored

    def reset_task(self, task_id: str) -> None:
        """Повністю прибирає прогрес задачі (для кнопки «почати спочатку»)."""
        self.connection.execute("DELETE FROM attempts WHERE task_id = ?", (task_id,))
        self.connection.execute("DELETE FROM reviews WHERE task_id = ?", (task_id,))
        self.connection.execute("DELETE FROM progress WHERE task_id = ?", (task_id,))
        self.connection.commit()
