"""Тести навчальної сесії — правил, які раніше жили в інтерфейсі."""

import unittest

from curriculum import find_task
from trainer.core.db import Database
from trainer.core.runner import CheckResult, RunResult, run_task
from trainer.core.session import StudySession


def passed(checks: int = 2) -> RunResult:
    return RunResult(
        ran_checks=True,
        checks=[CheckResult(name=f"перевірка {index}", ok=True) for index in range(checks)],
    )


def failed(checks: int = 2, passed_count: int = 1) -> RunResult:
    return RunResult(
        ran_checks=True,
        checks=[
            CheckResult(name=f"перевірка {index}", ok=index < passed_count,
                        error="" if index < passed_count else "AssertionError")
            for index in range(checks)
        ],
    )


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.session = StudySession(self.db)

    def tearDown(self):
        self.db.close()

    # ---------- базові переходи ----------

    def test_plain_run_does_not_touch_progress(self):
        task = find_task("w1-hello")
        update = self.session.record_result(task, RunResult(stdout="привіт"))
        self.assertIsNone(update)
        self.assertEqual(self.db.status(task.id), "todo")

    def test_first_clean_pass_is_mastered_right_away(self):
        task = find_task("w1-hello")
        update = self.session.record_result(task, passed())
        self.assertTrue(update.passed)
        self.assertTrue(update.first_try)
        self.assertEqual(update.xp, 100)
        self.assertTrue(update.mastered)
        self.assertIsNone(self.db.review(task.id))

    def test_failed_attempt_goes_to_review_queue(self):
        task = find_task("w1-hello")
        update = self.session.record_result(task, failed())
        self.assertFalse(update.passed)
        self.assertEqual(update.xp, 0)
        self.assertIsNotNone(self.db.review(task.id))
        self.assertFalse(update.mastered)

    def test_second_try_success_still_needs_review(self):
        task = find_task("w1-hello")
        self.session.record_result(task, failed())
        update = self.session.record_result(task, passed())
        self.assertTrue(update.passed)
        self.assertIsNotNone(self.db.review(task.id))
        self.assertFalse(update.mastered)

    def test_solution_used_lands_in_review_queue(self):
        task = find_task("w1-hello")
        self.session.use_solution(task)
        update = self.session.record_result(task, passed())
        self.assertEqual(update.xp, 55)
        self.assertIn("чергу повторень", " ".join(update.notes))

    # ---------- повторення й XP за них ----------

    def test_review_cycle_advances_and_masters(self):
        task = find_task("w1-hello")
        self.session.record_result(task, failed())
        self.session.record_result(task, passed())        # здав з другої спроби

        rewards = []
        for _ in range(4):
            update = self.session.record_result(task, passed(), review_mode=True)
            rewards.append(update.bonus_xp)
            if update.review_days is None:
                break

        self.assertTrue(all(reward > 0 for reward in rewards), rewards)
        self.assertEqual(rewards, sorted(rewards), "глибші повторення мають коштувати більше")
        self.assertTrue(self.session.is_mastered(task.id))
        self.assertIsNone(self.db.review(task.id))

    def test_review_xp_goes_to_total(self):
        task = find_task("w1-hello")
        self.session.record_result(task, failed())
        self.session.record_result(task, passed())
        before = self.db.total_xp()
        self.session.record_result(task, passed(), review_mode=True)
        self.assertGreater(self.db.total_xp(), before)

    def test_failed_review_resets_interval(self):
        task = find_task("w1-hello")
        self.session.record_result(task, failed())
        self.session.record_result(task, passed())
        self.session.record_result(task, passed(), review_mode=True)
        index_before = self.db.review(task.id)["interval_index"]

        self.session.record_result(task, failed(), review_mode=True)
        self.assertEqual(self.db.review(task.id)["interval_index"], 0)
        self.assertGreater(index_before, 0)

    # ---------- підказки й ручні пункти ----------

    def test_hint_lowers_preview(self):
        task = find_task("w1-hello")
        self.assertEqual(self.session.preview_xp(task), 100)
        self.assertEqual(self.session.record_hint(task, 1, False), 85)

    def test_manual_milestone_marks_done_without_xp(self):
        task = find_task("m2-git")
        self.assertTrue(task.stub)
        self.session.mark_manual_done(task)
        self.assertEqual(self.db.status(task.id), "done")
        self.assertEqual(self.db.total_xp(), 0)

    def test_summary_counts_mastered_separately(self):
        self.session.record_result(find_task("w1-hello"), passed())   # чисто → утримано
        self.session.record_result(find_task("w1-vars"), failed())    # у черзі повторень

        summary = self.session.summary()
        self.assertEqual(summary["done"], 1)
        self.assertEqual(summary["mastered"], 1)
        self.assertGreater(summary["total"], 10)

    def test_real_code_flows_through_session(self):
        """Перевірка «від краю до краю»: код → runner → сесія → база."""
        task = find_task("w1-hello")
        update = self.session.record_result(task, run_task(task, task.starter))
        self.assertFalse(update.passed)

        update = self.session.record_result(task, run_task(task, task.solution_hint.text))
        self.assertTrue(update.passed)
        self.assertEqual(self.db.status(task.id), "done")


if __name__ == "__main__":
    unittest.main()
