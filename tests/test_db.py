"""Тести бази даних тренажера."""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from trainer.core import scoring
from trainer.core.db import Database, backup_database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    # ---------- прогрес ----------

    def test_new_task_is_todo(self):
        self.assertEqual(self.db.status("w1-hello"), "todo")
        self.assertEqual(self.db.statuses(), {})

    def test_mark_in_progress(self):
        self.db.mark_in_progress("w1-hello")
        self.assertEqual(self.db.status("w1-hello"), "current")

    def test_mark_solved_keeps_best_xp(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.mark_solved("w1-hello", 60)
        self.assertEqual(self.db.status("w1-hello"), "done")
        self.assertEqual(self.db.best_xp("w1-hello"), 100)

    def test_solved_stays_done_when_opened_again(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.mark_in_progress("w1-hello")
        self.assertEqual(self.db.status("w1-hello"), "done")

    def test_saved_code_roundtrip(self):
        self.db.save_code("w1-hello", 'print("привіт")')
        self.assertEqual(self.db.saved_code("w1-hello"), 'print("привіт")')
        self.assertIsNone(self.db.saved_code("w1-vars"))

    # ---------- спроби ----------

    def test_attempts_and_history(self):
        self.db.record_attempt("w1-hello", ok=False, with_checks=True)
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.assertEqual(self.db.attempts_count("w1-hello"), 2)
        self.assertEqual(self.db.passes_count("w1-hello"), 1)
        self.assertEqual(len(self.db.history("w1-hello")), 2)

    def test_runs_without_checks_are_not_counted_as_attempts(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=False)
        self.assertEqual(self.db.attempts_count("w1-hello"), 0)

    # ---------- підказки й час ----------

    def test_hints_and_solution_flags(self):
        self.db.reveal_hint("w3-greet", 1)
        self.db.reveal_hint("w3-greet", 2, is_solution=True)
        self.assertEqual(self.db.hints_used("w3-greet"), 2)
        self.assertTrue(self.db.solution_used("w3-greet"))

    def test_hint_level_never_goes_back(self):
        self.db.reveal_hint("w3-greet", 2)
        self.db.reveal_hint("w3-greet", 1)
        self.assertEqual(self.db.hints_used("w3-greet"), 2)

    def test_mark_solution_used_does_not_touch_hint_counter(self):
        self.db.mark_solution_used("m2-sql")
        self.assertTrue(self.db.solution_used("m2-sql"))
        self.assertEqual(self.db.hints_used("m2-sql"), 0)

    def test_active_seconds_accumulate(self):
        self.db.add_active_seconds("w1-hello", 5)
        self.db.add_active_seconds("w1-hello", 7)
        self.assertEqual(self.db.active_seconds("w1-hello"), 12)

    # ---------- повторення ----------

    def test_review_progression_after_failures(self):
        self.db.schedule_from_result("w2-for", False)
        self.assertEqual(self.db.review("w2-for")["interval_index"], 0)

    def test_review_grows_after_success(self):
        self.db.schedule_from_result("w2-for", False)
        for expected_days, expected_index in ((3, 1), (7, 2), (30, 3)):
            index, days = self.db.schedule_from_result("w2-for", True)
            self.assertEqual((index, days), (expected_index, expected_days))

    def test_review_is_removed_when_mastered(self):
        # 1 → 3 → 7 → 30 днів, п'яте успішне повторення знімає задачу з черги
        for _ in range(5):
            self.db.schedule_from_result("w2-for", True)
        self.assertIsNone(self.db.review("w2-for"))

    def test_fail_in_review_resets_schedule(self):
        self.db.schedule_from_result("w2-for", True)
        self.db.schedule_from_result("w2-for", True)
        self.db.schedule_from_result("w2-for", False)
        self.assertEqual(self.db.review("w2-for")["interval_index"], 0)

    def test_due_and_upcoming_reviews(self):
        # schedule_review рахує дату від реального сьогодні, тому беремо
        # сьогоднішню дату — інакше тест ламався б наступного ж дня.
        today = date.today()
        self.db.schedule_review("w1-hello", 0, 0)   # час повторювати вже сьогодні
        self.db.schedule_review("w2-for", 3, 1)     # ще через три дні

        due = self.db.due_reviews(on=today)
        self.assertEqual([row["task_id"] for row in due], ["w1-hello"])

        upcoming = self.db.upcoming_reviews(on=today)
        self.assertEqual([row["task_id"] for row in upcoming], ["w2-for"])

    # ---------- статистика ----------

    def test_total_xp_sums_best_results(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.mark_solved("w1-vars", 85)
        self.assertEqual(self.db.total_xp(), 185)

    def test_streak_uses_attempt_days(self):
        today = date.today()
        for day in (today, today - timedelta(days=1), today - timedelta(days=2)):
            self.db.connection.execute(
                "INSERT INTO attempts (task_id, created_at, ok, with_checks, xp) "
                "VALUES ('w1-hello', ?, 1, 1, 10)",
                (f"{day.isoformat()}T12:00:00",),
            )
        self.db.connection.commit()
        self.assertEqual(self.db.streak(), 3)

    def test_attempts_per_day_counts(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.db.record_attempt("w1-hello", ok=False, with_checks=True)
        activity = self.db.attempts_per_day()
        self.assertEqual(activity.get(date.today().isoformat()), 2)

    def test_task_results_join(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.record_attempt("w1-hello", ok=False, with_checks=True)
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        row = [r for r in self.db.task_results() if r["task_id"] == "w1-hello"][0]
        self.assertEqual(row["attempts"], 2)
        self.assertEqual(row["passes"], 1)
        self.assertEqual(row["status"], "done")

    def test_bonus_xp_adds_to_total(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.add_bonus_xp("w1-hello", 20)
        self.db.add_bonus_xp("w1-hello", 30)
        self.assertEqual(self.db.bonus_xp("w1-hello"), 50)
        self.assertEqual(self.db.total_xp(), 150)

    def test_bonus_xp_is_separate_from_best_xp(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.add_bonus_xp("w1-hello", 20)
        # повторний прохід з меншим XP не має обнуляти бонус
        self.db.mark_repeat_passed("w1-hello", 30)
        self.assertEqual(self.db.best_xp("w1-hello"), 100)
        self.assertEqual(self.db.total_xp(), 120)

    def test_snapshot_skips_untouched_tasks(self):
        self.db.save_code("w1-hello", "код")        # лише відкрита, але не здана
        self.db.mark_solved("w1-vars", 85)
        snapshot = self.db.snapshot()
        ids = [row["task_id"] for row in snapshot["progress"]]
        self.assertEqual(ids, ["w1-vars"])

    def test_restore_brings_back_progress_and_reviews(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.add_bonus_xp("w1-hello", 20)
        self.db.schedule_review("w1-vars", 3, 1)
        snapshot = self.db.snapshot()

        other = Database(":memory:")
        try:
            restored = other.restore(snapshot)
            self.assertEqual(restored, 1)
            self.assertEqual(other.total_xp(), 120)
            self.assertIsNotNone(other.review("w1-vars"))
            self.assertEqual(other.review("w1-vars")["interval_index"], 1)
        finally:
            other.close()

    def test_total_active_seconds(self):
        self.db.add_active_seconds("w1-hello", 60)
        self.db.add_active_seconds("w1-vars", 30)
        self.assertEqual(self.db.total_active_seconds(), 90)

    def test_task_results_include_review_state(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.schedule_review("w1-hello", 1, 0)
        row = [r for r in self.db.task_results() if r["task_id"] == "w1-hello"][0]
        self.assertIsNotNone(row["due_date"])
        self.assertEqual(row["interval_index"], 0)

    def test_reset_task_clears_everything(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.db.schedule_review("w1-hello", 1, 0)
        self.db.reset_task("w1-hello")
        self.assertEqual(self.db.status("w1-hello"), "todo")
        self.assertEqual(self.db.total_xp(), 0)
        self.assertEqual(self.db.attempts_count("w1-hello"), 0)
        self.assertIsNone(self.db.review("w1-hello"))


class MistakeLogTests(unittest.TestCase):
    """Журнал помилок: що саме людина не здала, скільки разів — і чи вже закрито.

    Рішення «закрито / закрито з допомогою / відкрито» ухвалює `core/mistakes`,
    але всі дані для нього віддає цей запит — тому перевіряємо його тут, разом
    із `id` спроб: за часом дві спроби в одну секунду не розрізнити.
    """

    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_empty_log(self):
        self.assertEqual(self.db.mistake_history(), [])

    def test_successful_attempt_is_not_a_mistake(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100,
                               error_kind="AssertionError")
        self.assertEqual(self.db.mistake_history(), [])

    def test_runs_without_checks_are_not_mistakes(self):
        self.db.record_attempt("w1-hello", ok=False, with_checks=False)
        self.assertEqual(self.db.mistake_history(), [])

    def test_wrong_output_without_a_kind_is_not_logged(self):
        """«У виводі немає…» — не помилка Python, у журнал не пишемо."""
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               failed_check="виводить привітання", error_kind="")
        self.assertEqual(self.db.mistake_history(), [])

    def test_groups_by_task_and_kind(self):
        for _ in range(3):
            self.db.record_attempt("m3-lc-two-sum", ok=False, with_checks=True,
                                   failed_check="простий випадок",
                                   error_kind="NameError")
        self.db.record_attempt("m3-lc-two-sum", ok=False, with_checks=True,
                               failed_check="два однакові числа",
                               error_kind="AssertionError")

        rows = self.db.mistake_history()
        self.assertEqual(len(rows), 2)          # дві різні помилки, не чотири
        by_kind = {row["error_kind"]: row for row in rows}
        self.assertEqual(by_kind["NameError"]["times"], 3)
        self.assertEqual(by_kind["AssertionError"]["times"], 1)
        self.assertEqual(by_kind["NameError"]["task_id"], "m3-lc-two-sum")

    def test_newest_mistakes_come_first(self):
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               error_kind="NameError")
        self.db.connection.execute(
            "UPDATE attempts SET created_at = '2020-01-01T10:00:00'"
        )
        self.db.connection.commit()
        self.db.record_attempt("w1-vars", ok=False, with_checks=True,
                               error_kind="TypeError")
        rows = self.db.mistake_history()
        self.assertEqual(rows[0]["task_id"], "w1-vars")

    def test_limit_is_respected(self):
        for index in range(5):
            self.db.record_attempt(f"task-{index}", ok=False, with_checks=True,
                                   error_kind="ValueError")
        self.assertEqual(len(self.db.mistake_history(limit=2)), 2)

    def test_reset_clears_the_log(self):
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               error_kind="NameError")
        self.db.reset_task("w1-hello")
        self.assertEqual(self.db.mistake_history(), [])


class XpHistoryTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_xp_by_day_collects_successful_attempts(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.db.record_attempt("w1-vars", ok=True, with_checks=True, xp=50)
        self.db.record_attempt("w1-input", ok=False, with_checks=True, xp=0)

        by_day = self.db.xp_by_day()
        self.assertEqual(list(by_day.values()), [150])
        self.assertEqual(list(by_day)[0], date.today().isoformat())

    def test_xp_by_day_is_empty_without_passes(self):
        self.assertEqual(self.db.xp_by_day(), {})

    def test_old_days_are_cut_off(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.db.connection.execute(
            "UPDATE attempts SET created_at = '2020-01-01T10:00:00'"
        )
        self.db.connection.commit()
        self.assertEqual(self.db.xp_by_day(days=28), {})


class MigrationTests(unittest.TestCase):
    """База зі старої версії тренажера не має ламатись."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "old.db"

    def tearDown(self):
        self.tmp.cleanup()

    def _make_old_database(self) -> None:
        """Схема до журналу помилок: без failed_check/error_kind."""
        import sqlite3

        connection = sqlite3.connect(self.path)
        connection.executescript(
            """
            CREATE TABLE progress (
                task_id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'todo',
                started_at TEXT, solved_at TEXT,
                best_xp INTEGER NOT NULL DEFAULT 0, hints_used INTEGER NOT NULL DEFAULT 0,
                solution_used INTEGER NOT NULL DEFAULT 0,
                active_seconds REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                created_at TEXT NOT NULL, ok INTEGER NOT NULL,
                with_checks INTEGER NOT NULL, xp INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE reviews (
                task_id TEXT PRIMARY KEY, due_date TEXT NOT NULL,
                interval_index INTEGER NOT NULL DEFAULT 0, last_result INTEGER,
                updated_at TEXT NOT NULL
            );
            INSERT INTO progress (task_id, status, best_xp) VALUES ('w1-hello', 'done', 100);
            INSERT INTO attempts (task_id, created_at, ok, with_checks, xp)
                 VALUES ('w1-hello', '2026-01-01T10:00:00', 1, 1, 100);
            """
        )
        connection.commit()
        connection.close()

    def test_old_database_gains_new_columns(self):
        self._make_old_database()
        db = Database(self.path)
        try:
            attempt_columns = {row["name"] for row in
                               db.connection.execute("PRAGMA table_info(attempts)")}
            self.assertIn("failed_check", attempt_columns)
            self.assertIn("error_kind", attempt_columns)
            # Стара база не знала про «чистий прохід» — ним закриваються
            # помилки в журналі, і без міграції огляд рахував би їх вічно.
            self.assertIn("clean", attempt_columns)
            progress_columns = {row["name"] for row in
                                db.connection.execute("PRAGMA table_info(progress)")}
            self.assertIn("code", progress_columns)
            self.assertIn("bonus_xp", progress_columns)
        finally:
            db.close()

    def test_old_progress_survives_the_migration(self):
        self._make_old_database()
        db = Database(self.path)
        try:
            self.assertEqual(db.status("w1-hello"), "done")
            self.assertEqual(db.total_xp(), 100)
            self.assertEqual(db.mistake_history(), [])
            db.record_attempt("w1-vars", ok=False, with_checks=True,
                              error_kind="NameError")
            self.assertEqual(len(db.mistake_history()), 1)
        finally:
            db.close()


class ScoringIntegrationTests(unittest.TestCase):
    """Перевіряємо, що правила XP і база узгоджені між собою."""

    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_solution_used_leads_to_review(self):
        from curriculum import find_task

        task = find_task("w2-strings")
        self.db.reveal_hint(task.id, 2, is_solution=True)
        self.assertTrue(
            scoring.needs_review(
                solved=True,
                attempts=self.db.attempts_count(task.id) or 1,
                solution_used=self.db.solution_used(task.id),
            )
        )


class BackupTests(unittest.TestCase):
    """Копія бази: прогрес за місяці не має залежати від одного файлу."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.db = Database(self.folder / "pytrainer.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_backup_copies_the_progress(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.close()                       # копіюємо закриту базу

        copy = backup_database(self.folder / "pytrainer.db")
        self.assertIsNotNone(copy)
        self.assertTrue(copy.exists())

        restored = Database(copy)
        try:
            self.assertEqual(restored.status("w1-hello"), "done")
            self.assertEqual(restored.total_xp(), 100)
        finally:
            restored.close()

    def test_backup_keeps_only_the_last_copies(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.close()
        source = self.folder / "pytrainer.db"

        created = [backup_database(source, keep=2) for _ in range(4)]

        copies = sorted((self.folder / "backups").glob("pytrainer-*.db"))
        self.assertEqual(len(copies), 2)

        newest = created[-1]
        self.assertTrue(newest.exists(), "щойно створена копія не має зникати")
        restored = Database(newest)
        try:
            self.assertEqual(restored.status("w1-hello"), "done")
            self.assertEqual(restored.total_xp(), 100)
        finally:
            restored.close()

    def test_backup_names_sort_like_dates(self):
        """Ім'я копії можна сортувати як рядок — воно йде в хронологічному порядку."""
        self.db.mark_solved("w1-hello", 100)
        self.db.close()
        names = [backup_database(self.folder / "pytrainer.db").name for _ in range(3)]
        self.assertEqual(names, sorted(names))

    def test_no_backup_without_a_database(self):
        self.assertIsNone(backup_database(self.folder / "нема.db"))


if __name__ == "__main__":
    unittest.main()
