"""Тести плану на сьогодні.

План — це те, що людина бачить першим, коли сідає працювати. Тому перевіряємо
не «щось повернулось», а сам порядок: спершу повторення, потім слабке місце,
потім нове — і все це мусить уміщатися в один вечір.
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from curriculum import find_task, study_tasks, topic_of
from trainer.core.db import Database
from trainer.core.plan import DEFAULT_BUDGET, PlanStep, daily_plan


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "plan.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _first_unfinished(self):
        for task in study_tasks():
            if self.db.status(task.id) != "done":
                return task
        raise AssertionError("усі задачі здані — тест зламався б")

    # ---------- базове ----------

    def test_empty_progress_still_gives_a_plan(self):
        plan = daily_plan(self.db)
        self.assertFalse(plan.empty)
        self.assertEqual(plan.steps[0].kind, "new")
        self.assertEqual(plan.steps[0].task_id, self._first_unfinished().id)

    def test_plan_fits_the_budget(self):
        plan = daily_plan(self.db, budget=60)
        self.assertLessEqual(plan.minutes, 60 + 25)   # +останній крок завжди влазить

    def test_default_budget_is_a_normal_evening(self):
        self.assertEqual(DEFAULT_BUDGET, 100)

    def test_steps_have_reasons_and_topics(self):
        for step in daily_plan(self.db).steps:
            with self.subTest(step=step.title):
                self.assertTrue(step.reason.strip(), "крок без пояснення «чому»")
                self.assertGreater(step.minutes, 0)

    def test_no_duplicate_tasks_in_the_plan(self):
        ids = [step.task_id for step in daily_plan(self.db).steps]
        self.assertEqual(len(ids), len(set(ids)))

    def test_skips_already_solved_tasks(self):
        for task in study_tasks()[:5]:
            self.db.mark_solved(task.id, 100)
        plan = daily_plan(self.db)
        solved = {task.id for task in study_tasks()[:5]}
        for step in plan.steps:
            self.assertNotIn(step.task_id, solved)

    # ---------- повторення ----------

    def test_reviews_come_first(self):
        task = self._first_unfinished()
        self.db.schedule_review(task.id, 0, 0)          # час повторювати вже сьогодні
        plan = daily_plan(self.db)
        self.assertEqual(plan.steps[0].kind, "review")
        self.assertEqual(plan.steps[0].task_id, task.id)

    def test_overdue_review_is_marked_as_such(self):
        task = self._first_unfinished()
        self.db.schedule_review(task.id, 0, 0)
        self.db.connection.execute(
            "UPDATE reviews SET due_date = DATE('now', '-3 day') WHERE task_id = ?",
            (task.id,),
        )
        self.db.connection.commit()
        plan = daily_plan(self.db)
        self.assertIn("прострочено", plan.steps[0].reason)

    def test_future_reviews_are_not_in_todays_plan(self):
        task = self._first_unfinished()
        self.db.schedule_review(task.id, 30, 3)
        kinds = [step.kind for step in daily_plan(self.db).steps]
        self.assertNotIn("review", kinds)

    # ---------- слабкі теми ----------

    def test_weak_topic_becomes_a_step(self):
        """Три провали в темі — і план має запропонувати її добити."""
        task = self._first_unfinished()
        topic = topic_of(task.id)
        siblings = [item for item in study_tasks() if topic_of(item.id) == topic]
        for item in siblings[:2]:
            for _ in range(3):
                self.db.record_attempt(item.id, ok=False, with_checks=True,
                                       error_kind="AssertionError")
        plan = daily_plan(self.db)
        weak_steps = [step for step in plan.steps if step.kind == "weak"]
        self.assertTrue(weak_steps, f"тема «{topic}» не потрапила в план")
        self.assertEqual(weak_steps[0].topic, topic)

    def test_weak_step_needs_an_unfinished_task(self):
        """Якщо в слабкій темі все здано — кроку бути не повинно."""
        task = self._first_unfinished()
        topic = topic_of(task.id)
        for item in [t for t in study_tasks() if topic_of(t.id) == topic]:
            self.db.mark_solved(item.id, 100)
            for _ in range(3):
                self.db.record_attempt(item.id, ok=False, with_checks=True,
                                       error_kind="AssertionError")
        plan = daily_plan(self.db)
        self.assertFalse([s for s in plan.steps if s.kind == "weak"])

    # ---------- межі ----------

    def test_plan_is_empty_when_everything_is_done(self):
        for task in study_tasks():
            self.db.mark_solved(task.id, 100)
        plan = daily_plan(self.db)
        self.assertTrue(plan.empty)
        self.assertEqual(plan.minutes, 0)
        self.assertEqual(plan.as_lines(), [])

    def test_as_lines_is_human_readable(self):
        lines = daily_plan(self.db).as_lines()
        self.assertTrue(lines)
        self.assertIn("~", lines[0])
        for index, line in enumerate(lines, start=1):
            self.assertTrue(line.startswith(f"{index}."))

    def test_stub_tasks_never_reach_the_plan(self):
        for task in study_tasks():
            self.db.mark_solved(task.id, 100)
        self.db.schedule_review("m5-deploy", 0, 0)   # заглушка в черзі
        plan = daily_plan(self.db)
        self.assertEqual([step.task_id for step in plan.steps], [])

    def test_plan_step_defaults(self):
        step = PlanStep(kind="new", title="щось", reason="тому що")
        self.assertEqual(step.minutes, 10)
        self.assertIsNone(step.task_id)
        self.assertFalse(step.done)


if __name__ == "__main__":
    unittest.main()
