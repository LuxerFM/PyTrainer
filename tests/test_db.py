"""Тести бази даних тренажера."""

import unittest
from datetime import date, timedelta

from trainer.core import scoring
from trainer.core.db import Database


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
        today = date(2026, 9, 24)
        self.db.schedule_review("w1-hello", 1, 0)
        self.db.schedule_review("w2-for", 3, 1)

        due = self.db.due_reviews(on=today + timedelta(days=1))
        self.assertEqual([row["task_id"] for row in due], ["w1-hello"])

        upcoming = self.db.upcoming_reviews(on=today)
        self.assertEqual({row["task_id"] for row in upcoming}, {"w1-hello", "w2-for"})

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

    def test_reset_task_clears_everything(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.db.schedule_review("w1-hello", 1, 0)
        self.db.reset_task("w1-hello")
        self.assertEqual(self.db.status("w1-hello"), "todo")
        self.assertEqual(self.db.total_xp(), 0)
        self.assertEqual(self.db.attempts_count("w1-hello"), 0)
        self.assertIsNone(self.db.review("w1-hello"))


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


if __name__ == "__main__":
    unittest.main()
