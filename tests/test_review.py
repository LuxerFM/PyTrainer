"""Тести холодного повторення: яку задачу дістаємо і скільки на неї часу.

Головне тут — не «щось вибралось», а правила: лише здані задачі, спершу
черга повторень, відкрита задача не випадає вдруге, а час обмежений з обох
боків. Саме ці правила відрізняють вправу від простого перегляду розв'язку.
"""

import random
import unittest
from types import SimpleNamespace

from curriculum import find_task, study_tasks
from trainer.core.db import Database
from trainer.core.review import (
    COLD_MINUTES,
    MIN_COLD_MINUTES,
    cold_seconds,
    due_tasks,
    pick_cold_task,
    solved_tasks,
)


class ColdReviewTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def _solve(self, task_id: str, *, due_in: int | None = None) -> None:
        """Здає задачу так, як це зробив би тренажер."""
        self.db.mark_solved(task_id, 100)
        if due_in is not None:
            self.db.schedule_review(task_id, due_in, 0)

    # ---------- кого можна діставати з пам'яті ----------

    def test_nothing_solved_means_no_cold_review(self):
        self.assertIsNone(pick_cold_task(self.db))

    def test_solved_task_is_offered_with_its_time_limit(self):
        self._solve("w1-hello")
        choice = pick_cold_task(self.db)
        self.assertEqual(choice.task.id, "w1-hello")
        self.assertFalse(choice.from_queue)
        self.assertEqual(choice.seconds, cold_seconds(find_task("w1-hello")))

    def test_stub_milestones_are_not_offered(self):
        """Пункт поза тренажером (venv, Git) згадувати нічим — там немає коду."""
        self.db.mark_solved("m2-git", 0)
        self.assertIsNone(pick_cold_task(self.db))

    def test_unsolved_task_is_not_offered(self):
        self._solve("w1-hello")
        self.db.record_attempt("w2-list", ok=False, with_checks=True)
        self.db.schedule_review("w2-list", 0, 0)      # у черзі, але не здана
        choice = pick_cold_task(self.db)
        self.assertEqual(choice.task.id, "w1-hello")

    def test_solved_tasks_lists_only_done_ones(self):
        self._solve("w1-hello")
        self.db.mark_in_progress("w2-list")
        self.assertEqual([task.id for task in solved_tasks(self.db)], ["w1-hello"])

    # ---------- черговість ----------

    def test_queue_comes_first(self):
        self._solve("w1-hello")
        self._solve("w1-vars", due_in=0)              # час повторювати вже сьогодні
        for seed in range(5):
            choice = pick_cold_task(self.db, rng=random.Random(seed))
            self.assertEqual(choice.task.id, "w1-vars")
            self.assertTrue(choice.from_queue)

    def test_future_review_does_not_jump_ahead(self):
        """Задача, яку час згадувати аж через тиждень, не має лізти першою."""
        self._solve("w1-hello")
        self._solve("w1-vars", due_in=7)
        self.assertEqual(due_tasks(self.db), [])
        choice = pick_cold_task(self.db, rng=random.Random(1))
        self.assertEqual(choice.task.id, "w1-hello")
        self.assertFalse(choice.from_queue)

    def test_due_tasks_skips_the_open_task(self):
        self._solve("w1-hello", due_in=0)
        self._solve("w1-vars", due_in=0)
        self.assertEqual(
            [task.id for task in due_tasks(self.db, exclude="w1-hello")],
            ["w1-vars"],
        )

    # ---------- випадковість і повторюваність ----------

    def test_open_task_is_never_offered(self):
        self._solve("w1-hello")
        self._solve("w1-vars")
        for seed in range(10):
            choice = pick_cold_task(
                self.db, exclude="w1-hello", rng=random.Random(seed)
            )
            self.assertEqual(choice.task.id, "w1-vars")

    def test_excluding_the_only_solved_task_leaves_nothing(self):
        self._solve("w1-hello")
        self.assertIsNone(pick_cold_task(self.db, exclude="w1-hello"))

    def test_same_seed_gives_the_same_task(self):
        for task_id in ("w1-hello", "w1-vars", "w1-input", "w1-if-even"):
            self._solve(task_id)
        first = pick_cold_task(self.db, rng=random.Random(3))
        second = pick_cold_task(self.db, rng=random.Random(3))
        self.assertEqual(first.task.id, second.task.id)

    def test_different_seeds_can_give_different_tasks(self):
        for task_id in ("w1-hello", "w1-vars", "w1-input", "w1-if-even"):
            self._solve(task_id)
        picked = {
            pick_cold_task(self.db, rng=random.Random(seed)).task.id
            for seed in range(30)
        }
        self.assertGreater(len(picked), 1, "вибір має бути випадковим")

    # ---------- час ----------

    def test_time_limit_is_capped_both_ways(self):
        self.assertEqual(cold_seconds(SimpleNamespace(minutes=90)),
                         COLD_MINUTES * 60)
        self.assertEqual(cold_seconds(SimpleNamespace(minutes=1)),
                         MIN_COLD_MINUTES * 60)

    def test_any_real_task_gets_a_sane_limit(self):
        for task in study_tasks():
            limit = cold_seconds(task)
            self.assertGreaterEqual(limit, MIN_COLD_MINUTES * 60, task.id)
            self.assertLessEqual(limit, COLD_MINUTES * 60, task.id)

    def test_minutes_match_the_seconds(self):
        """У підписі вікна показуються хвилини — вони мають бути тими ж."""
        self._solve("w1-hello")
        choice = pick_cold_task(self.db)
        self.assertEqual(choice.minutes, cold_seconds(choice.task) // 60)
        self.assertEqual(choice.minutes, choice.seconds // 60)


if __name__ == "__main__":
    unittest.main()
