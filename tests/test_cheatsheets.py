"""Тести міні-довідки (шпаргалок).

Перевіряємо дві речі: що самі шпаргалки заповнені, і що для кожної задачі
тренажера знаходиться бодай якась — бо порожня вкладка «Довідка» під час
роботи гірша за відсутню.
"""

import os
import unittest

from curriculum import cheatsheets, study_tasks
from curriculum.schema import task as make_task


class CheatSheetDataTests(unittest.TestCase):
    def test_sheets_are_complete(self):
        for sheet in cheatsheets.all_sheets():
            with self.subTest(sheet=sheet.key):
                self.assertTrue(sheet.title.strip())
                self.assertTrue(sheet.body.strip())
                self.assertTrue(sheet.keywords, "без ключових слів підбір не працює")

    def test_keys_are_unique(self):
        keys = [sheet.key for sheet in cheatsheets.all_sheets()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_get_returns_sheet_by_key(self):
        self.assertEqual(cheatsheets.get("dicts").key, "dicts")
        self.assertIsNotNone(cheatsheets.get("algorithms"))
        self.assertIsNone(cheatsheets.get("такого-немає"))

    def test_get_by_unknown_key(self):
        self.assertIsNone(cheatsheets.get(""))


class PickTests(unittest.TestCase):
    def test_every_task_gets_a_sheet(self):
        for problem in study_tasks():
            with self.subTest(task=problem.id):
                sheet = cheatsheets.pick(problem)
                self.assertIsNotNone(sheet)
                self.assertTrue(sheet.title)

    def test_explicit_key_wins(self):
        problem = make_task(
            id="тест-явний", title="Щось зовсім не про словники",
            cheatsheet="algorithms",
        )
        self.assertEqual(cheatsheets.pick(problem).key, "algorithms")

    def test_topic_keywords_are_used(self):
        """Задача про словники мусить отримати шпаргалку про словники."""
        by_id = {problem.id: problem for problem in study_tasks()}
        self.assertEqual(cheatsheets.pick(by_id["m3-lc-two-sum"]).key, "dicts")
        self.assertEqual(
            cheatsheets.pick(by_id["m3-algo-binary-search"]).key, "algorithms"
        )

    def test_pick_text_for_manual_milestones(self):
        """Пункти поза тренажером теж мають отримувати доречну довідку."""
        self.assertEqual(
            cheatsheets.pick_text("Git: перший коміт у своєму проєкті").key, "venv"
        )
        self.assertEqual(cheatsheets.pick_text("невідомо про що").key, "basics")


class PlainToHtmlTests(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from trainer.ui.task_panel import plain_to_html  # noqa: E402

        self.plain_to_html = plain_to_html

    def test_prose_becomes_paragraphs(self):
        html_text = self.plain_to_html("Перше речення.\nДруге речення.")
        self.assertIn("<p>Перше речення.</p>", html_text)
        self.assertIn("<p>Друге речення.</p>", html_text)

    def test_code_lines_are_grouped_into_pre(self):
        html_text = self.plain_to_html(
            "Спробуй так:\nprint(1)\nprint(2)\n\nІ пояснення далі."
        )
        self.assertIn("<pre>print(1)\nprint(2)</pre>", html_text)
        self.assertIn("<p>Спробуй так:</p>", html_text)
        self.assertIn("<p>І пояснення далі.</p>", html_text)

    def test_html_is_escaped(self):
        html_text = self.plain_to_html("порівняй a < b\nprint(a < b)")
        self.assertIn("&lt;", html_text)
        self.assertNotIn("a < b", html_text)

    def test_empty_text_does_not_break(self):
        self.assertEqual(self.plain_to_html(""), "<p></p>")

    def test_assignment_is_detected_as_code(self):
        html_text = self.plain_to_html("total = 0")
        self.assertIn("<pre>total = 0</pre>", html_text)


if __name__ == "__main__":
    unittest.main()
