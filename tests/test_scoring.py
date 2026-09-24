"""Тести правил навчання: XP, інтервали повторень, серія днів."""

import unittest
from datetime import date, timedelta

from curriculum import find_task
from trainer.core import scoring


class XpTests(unittest.TestCase):
    def test_base_xp_without_hints(self):
        task = find_task("w1-hello")            # Легко = 100 XP
        self.assertEqual(scoring.xp_for(task, hints_used=0), 100)

    def test_each_hint_costs_xp(self):
        task = find_task("w1-hello")
        self.assertEqual(scoring.xp_for(task, hints_used=1), 85)
        self.assertEqual(scoring.xp_for(task, hints_used=2), 70)

    def test_xp_never_falls_below_floor(self):
        task = find_task("w1-hello")
        self.assertGreaterEqual(scoring.xp_for(task, hints_used=10), 40)

    def test_project_task_is_worth_more(self):
        project = find_task("w1-calc")          # Проєкт = 250 XP
        self.assertEqual(scoring.xp_for(project, hints_used=0), 250)

    def test_repeat_pass_gives_less(self):
        task = find_task("w1-hello")
        self.assertEqual(scoring.xp_for(task, hints_used=0, first_time=False), 30)

    def test_solution_used_counts_as_full_penalty(self):
        task = find_task("w1-hello")
        # навіть якщо підказки не розкривали — вставлений розв'язок знижує XP
        self.assertEqual(scoring.xp_for(task, solution_used=True),
                         scoring.xp_for(task, hints_used=scoring.SOLUTION_HINT_LEVELS))
        self.assertLess(scoring.xp_for(task, solution_used=True),
                        scoring.xp_for(task, hints_used=1))


class IntervalTests(unittest.TestCase):
    def test_intervals_grow(self):
        self.assertEqual(scoring.next_interval(-1, True), (0, 1))
        self.assertEqual(scoring.next_interval(0, True), (1, 3))
        self.assertEqual(scoring.next_interval(1, True), (2, 7))
        self.assertEqual(scoring.next_interval(2, True), (3, 30))

    def test_after_last_interval_task_is_mastered(self):
        self.assertEqual(scoring.next_interval(3, True), (4, None))

    def test_failure_resets_to_first_interval(self):
        self.assertEqual(scoring.next_interval(3, False), (0, 1))


class ReviewTriggerTests(unittest.TestCase):
    def test_failed_task_needs_review(self):
        self.assertTrue(scoring.needs_review(solved=False, attempts=1))

    def test_second_attempt_needs_review(self):
        self.assertTrue(scoring.needs_review(solved=True, attempts=2))

    def test_clean_first_pass_is_done(self):
        self.assertFalse(scoring.needs_review(solved=True, attempts=1))

    def test_solution_used_needs_review(self):
        self.assertTrue(
            scoring.needs_review(solved=True, attempts=1, solution_used=True)
        )


class StreakTests(unittest.TestCase):
    def test_empty_history(self):
        self.assertEqual(scoring.streak_from_days([]), 0)

    def test_streak_counting_today(self):
        today = date(2026, 9, 24)
        days = [today.isoformat(),
                (today - timedelta(days=1)).isoformat(),
                (today - timedelta(days=2)).isoformat()]
        self.assertEqual(scoring.streak_from_days(days, today=today), 3)

    def test_streak_keeps_yesterday_before_evening(self):
        today = date(2026, 9, 24)
        days = [(today - timedelta(days=1)).isoformat(),
                (today - timedelta(days=2)).isoformat()]
        self.assertEqual(scoring.streak_from_days(days, today=today), 2)

    def test_gap_breaks_streak(self):
        today = date(2026, 9, 24)
        days = [(today - timedelta(days=2)).isoformat()]
        self.assertEqual(scoring.streak_from_days(days, today=today), 0)


if __name__ == "__main__":
    unittest.main()
