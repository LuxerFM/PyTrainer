"""Тести навчального плану.

Найважливіший тест тут — test_solutions_pass_their_checks: кожен розв'язок
із підказки реально запускається проти власних перевірок. Якщо хтось (я)
змінить перевірку й забуде розв'язок — впаде цей тест, а не користувач.
"""

import unittest

from curriculum import CURRICULUM, all_tasks, study_tasks, topic_of
from curriculum import roadmap_md
from curriculum.schema import Check
from trainer.core.runner import run_code


class CurriculumStructureTests(unittest.TestCase):
    def test_ids_are_unique(self):
        ids = [task.id for task in all_tasks()]
        duplicates = {value for value in ids if ids.count(value) > 1}
        self.assertEqual(duplicates, set(), f"дублікати id: {duplicates}")

    def test_plan_covers_all_months(self):
        self.assertGreaterEqual(len(CURRICULUM), 5)
        self.assertTrue(all(month.topics for month in CURRICULUM))

    def test_month_one_has_enough_tasks(self):
        ready = [task for task in study_tasks() if task.id.startswith("w")]
        self.assertGreaterEqual(len(ready), 15, "у місяці 1 має бути щонайменше 15 задач")

    def test_every_ready_task_is_complete(self):
        for task in study_tasks():
            with self.subTest(task=task.id):
                self.assertTrue(task.statement.strip(), "немає умови")
                self.assertTrue(task.starter.strip(), "немає заготовки коду")
                self.assertGreaterEqual(len(task.checks), 2, "мало перевірок")
                self.assertGreaterEqual(len(task.hints), 2, "мало підказок")
                self.assertIsNotNone(task.solution_hint, "немає розв'язку")
                self.assertTrue(topic_of(task.id), "задача поза темою")

    def test_checks_are_executable(self):
        for task in study_tasks():
            for check in task.checks:
                with self.subTest(task=task.id, check=check.name):
                    self.assertTrue(check.code or check.is_stdout)

    def test_solutions_pass_their_checks(self):
        for task in study_tasks():
            with self.subTest(task=task.id):
                result = run_code(
                    task.solution_hint.text, list(task.checks), stdin=task.stdin
                )
                message = (
                    f'{task.id}: розв\'язок не проходить перевірки — '
                    + "; ".join(
                        f'{check.name}: {check.error}'
                        for check in result.checks
                        if not check.ok
                    )
                )
                self.assertTrue(result.all_passed, message)

    def test_starters_do_not_pass(self):
        for task in study_tasks():
            with self.subTest(task=task.id):
                result = run_code(task.starter, list(task.checks), stdin=task.stdin)
                self.assertFalse(
                    result.all_passed,
                    f"{task.id}: заготовка вже проходить усі перевірки",
                )

    def test_check_result_shape(self):
        check = Check(name="тест", code="assert True")
        self.assertFalse(check.is_stdout)


class RoadmapFileTests(unittest.TestCase):
    def test_render_contains_months_and_checkboxes(self):
        text = roadmap_md.render({"w1-hello": "done"}, {"xp": 100, "streak": 2})
        self.assertIn("МІСЯЦЬ 1", text)
        self.assertIn("- [x] Перший вивід: print()", text)
        self.assertIn("- [ ] Функція greet(name)", text)
        self.assertIn("XP: **100**", text)

    def test_render_marks_stubs(self):
        text = roadmap_md.render({}, {})
        self.assertIn("_заплановано_", text)
        self.assertIn("Git: init, add, commit", text)


if __name__ == "__main__":
    unittest.main()
