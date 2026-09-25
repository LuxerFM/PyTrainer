"""Тести навчального плану.

Найважливіший тест тут — test_solutions_pass_their_checks: кожен розв'язок
із підказки реально запускається проти власних перевірок. Якщо хтось (я)
змінить перевірку й забуде розв'язок — впаде цей тест, а не користувач.
"""

import unittest

from curriculum import CURRICULUM, all_tasks, study_tasks, topic_of
from curriculum import roadmap_md
from curriculum.schema import Check
from trainer.core.runner import run_code, run_task


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

    def test_month_two_has_enough_tasks(self):
        ready = [task for task in study_tasks() if task.id.startswith("m2-")]
        self.assertGreaterEqual(len(ready), 10, "у місяці 2 має бути щонайменше 10 задач")
        topics = {topic.title for topic in CURRICULUM[1].topics}
        self.assertIn("Тиждень 8 · Дані: JSON, CSV, SQL", topics)

    def test_every_month_one_week_has_drills(self):
        """Після кожного тижня теорії — тема з дрилами.

        Це не прикраса, а вимога до змісту: 18 задач на місяць проходили за
        кілька вечорів, і місця для повторів на різних даних не лишалось.
        """
        topics = CURRICULUM[0].topics
        for week in range(1, 5):
            drills = [item for item in topics
                      if item.title.startswith(f"Тренування тижня {week}")]
            with self.subTest(week=week):
                self.assertTrue(drills, f"немає теми «Тренування тижня {week}»")
                ready = [task for task in drills[0].tasks if not task.stub]
                self.assertGreaterEqual(len(ready), 5, "у тренуванні мало дрилів")

    def test_drills_go_right_after_their_week(self):
        """Дрили стоять одразу після свого тижня, а не зібрані в кінці.

        Інакше план на день пропонував би повторювати те, що вчив тиждень
        тому, замість того, що вчив сьогодні.
        """
        titles = [item.title for item in CURRICULUM[0].topics]
        for week in range(1, 5):
            with self.subTest(week=week):
                start = next(
                    index for index, title in enumerate(titles)
                    if title.startswith(f"Тиждень {week} ·")
                )
                self.assertTrue(
                    titles[start + 1].startswith(f"Тренування тижня {week}"),
                    f"після «{titles[start]}» іде «{titles[start + 1]}»",
                )

    def test_drills_stay_short(self):
        """Дрил — це 5–12 хвилин: довгу вправу просто не почнуть."""
        for task in study_tasks():
            if task.id.startswith("d"):
                with self.subTest(task=task.id):
                    self.assertLessEqual(task.minutes, 12, "дрил задовгий")
                    self.assertGreaterEqual(task.minutes, 5, "дрил закороткий")

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
                result = run_task(task, task.solution_hint.text)
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
                result = run_task(task, task.starter)
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
        self.assertIn("Git: перший коміт у своєму проєкті", text)


if __name__ == "__main__":
    unittest.main()
