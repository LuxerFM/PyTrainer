"""Тести розбору коду: на кожне правило — приклад поганого й доброго коду.

Правило без тесту з двох боків — це думка, а не перевірка. Тому тут є і код,
який має спрацювати, і код, на якому правило мусить промовчати: інструмент, що
прискіпується до нормального коду, людина просто перестає читати.

Окремо перевіряється головне для живого застосунку: розбір **не падає** на
жодній задачі курсу — ні на заготовці, ні на розв'язку, — і не вигадує
зауважень, яких у коді немає.
"""

import unittest
from unittest import mock

from curriculum import all_tasks
from trainer.core import codereview
from trainer.core.codereview import (
    MAX_REMARKS,
    NO_REMARKS,
    RULES,
    issues_phrase,
    names_used_in,
    review_code,
)

CLEAN = '''\
def average_marks(marks):
    """Середній бал за списком оцінок."""
    if not marks:
        return None
    return sum(marks) / len(marks)


def report(marks):
    average = average_marks(marks)
    if average is None:
        print("Оцінок немає")
        return
    print(f"Середній бал: {average:.1f}")
'''


class ReviewTestCase(unittest.TestCase):
    def _issues(self, code: str) -> list[str]:
        return [remark.kind for remark in review_code(code).issues]

    def _one(self, code: str, kind: str):
        """Повертає зауваження цього типу — або падає зі списком того, що є."""
        matching = [r for r in review_code(code).issues if r.kind == kind]
        if not matching:
            self.fail(f"правило «{kind}» не спрацювало; зауваження: {self._issues(code)}")
        return matching[0]

    def _silent(self, code: str, kind: str) -> None:
        self.assertNotIn(kind, self._issues(code), "правило прискіпується дарма")


class CleanCodeTests(ReviewTestCase):
    def test_clean_code_has_no_issues(self):
        review = review_code(CLEAN)
        self.assertTrue(review.ok)
        self.assertEqual(review.summary, NO_REMARKS)
        self.assertEqual(review.issues, ())

    def test_docstring_is_praised(self):
        review = review_code(CLEAN)
        self.assertEqual([remark.kind for remark in review.praises], ["praise-docstring"])
        self.assertTrue(review.ok, "похвала — не зауваження")

    def test_empty_editor_is_not_a_crime(self):
        for code in ("", "   \n", "# лише коментар\n"):
            review = review_code(code)
            self.assertTrue(review.ok)
            self.assertIn("нема чого розбирати", review.summary)

    def test_syntax_error_comes_back_as_one_remark(self):
        review = review_code("def f(:\n    pass\n")
        self.assertFalse(review.ok)
        self.assertEqual(len(review.issues), 1)
        remark = review.issues[0]
        self.assertEqual(remark.kind, "syntax")
        self.assertEqual(remark.line, 1)
        self.assertIn("Тести", review.summary)

    def test_every_remark_has_title_and_advice(self):
        for task in all_tasks():
            for code in (task.starter, task.solution_hint.text if task.solution_hint else ""):
                for remark in review_code(code).remarks:
                    self.assertTrue(remark.title.strip(), task.id)
                    self.assertTrue(remark.advice.strip(), task.id)


class RuleTests(ReviewTestCase):
    def test_unused_name_is_reported_and_is_not_a_crime_when_used(self):
        remark = self._one("def total(items):\n    result = 0\n    return sum(items)\n",
                           "unused-name")
        self.assertIn("result", remark.title)
        self.assertEqual(remark.line, 2)
        self._silent("def total(items):\n    result = sum(items)\n    return result\n",
                     "unused-name")

    def test_private_and_throwaway_names_are_left_alone(self):
        self._silent("def f(items):\n    _unused = 5\n    return items\n", "unused-name")

    def test_assignments_inside_a_loop_are_still_checked(self):
        """Змінна всередині циклу — така сама змінна, як і будь-де."""
        self.assertIn(
            "unused-name",
            self._issues("for item in [1, 2, 3]:\n    changed = 1\n    print(item)\n"),
        )
        self.assertNotIn(
            "unused-name",
            self._issues("for item in [1, 2, 3]:\n    print('раз')\n"),
        )

    def test_unused_import_is_reported(self):
        remark = self._one("import math\nimport random\n\nprint(math.pi)\n",
                           "unused-import")
        self.assertIn("random", remark.title)
        self.assertEqual(remark.line, 2)
        self._silent("import math\n\nprint(math.sqrt(4))\n", "unused-import")
        self._silent("from math import sqrt\n\nprint(sqrt(4))\n", "unused-import")
        self._silent("from math import *\n\nprint(sqrt(4))\n", "unused-import")

    def test_index_loop_from_another_start_is_left_alone(self):
        """`range(start, len(items))` — це робота з індексами, а не обхід списку."""
        self._silent("def move(numbers, write):\n"
                     "    for index in range(write, len(numbers)):\n"
                     "        numbers[index] = 0\n", "range-len")
        self._silent("for index in range(1, len(items)):\n    print(items[index])\n",
                     "range-len")

    def test_range_len_is_reported(self):
        remark = self._one("def total(items):\n"
                           "    result = 0\n"
                           "    for i in range(len(items)):\n"
                           "        result = result + items[i]\n"
                           "    return result\n", "range-len")
        self.assertEqual(remark.line, 3)
        self.assertIn("enumerate", remark.advice)
        self._silent("def total(items):\n    return sum(item for item in items)\n", "range-len")
        self._silent("for index, item in enumerate(items):\n    print(index, item)\n",
                     "range-len")

    def test_comparison_with_true_and_none_is_reported(self):
        true_remark = self._one("flag = True\nif flag == True:\n    print('так')\n",
                                "compare-to-literal")
        self.assertIn("True", true_remark.title)
        none_remark = self._one("value = None\nif value != None:\n    print(value)\n",
                                "compare-to-literal")
        self.assertIn("is not None", none_remark.advice)
        self._silent("value = None\nif value is not None:\n    print(value)\n",
                     "compare-to-literal")
        self._silent("if 0:\n    print('нуль — теж хибне')\n", "compare-to-literal")

    def test_bare_except_is_reported(self):
        remark = self._one("try:\n    number = int('x')\nexcept:\n    number = 0\n",
                           "bare-except")
        self.assertIn("except ValueError", remark.advice)
        self._silent("try:\n    number = int('1')\nexcept ValueError:\n    number = 0\n",
                     "bare-except")

    def test_swallowed_error_is_reported(self):
        remark = self._one("try:\n    number = int('x')\n"
                           "except ValueError:\n    pass\n", "silent-except")
        self.assertIn("print", remark.advice)
        self._silent("try:\n    number = int('1')\nexcept ValueError:\n"
                     "    print('не число')\n", "silent-except")

    def test_open_without_with_is_reported(self):
        remark = self._one("f = open('notes.txt', encoding='utf-8')\n"
                           "print(f.read())\nf.close()\n", "open-without-with")
        self.assertIn("with open", remark.advice)
        self._silent("with open('notes.txt', encoding='utf-8') as f:\n"
                     "    print(f.read())\n", "open-without-with")

    def test_elif_chain_is_one_level_not_many(self):
        """`if/elif/elif` — це один поверх: інакше калькулятор був би лабіринтом."""
        chain = "".join(f"elif value == {index + 20}:\n    print({index})\n"
                        for index in range(5))
        self._silent(f"value = 30\nif value == 19:\n    print('x')\n{chain}",
                     "deep-nesting")

    def test_deep_nesting_is_reported_once(self):
        code = ("def check(a, b):\n"
                "    if a:\n"
                "        if b:\n"
                "            for item in [1, 2]:\n"
                "                if item:\n"
                "                    print(item)\n")
        issues = review_code(code).issues
        self.assertEqual([r.kind for r in issues].count("deep-nesting"), 1)
        self._silent("def check(a):\n"
                     "    if a:\n"
                     "        for item in [1, 2]:\n"
                     "            print(item)\n", "deep-nesting")

    def test_round_numbers_of_the_base_ten_are_left_alone(self):
        """`// 100` і `% 10` — розряди числа, а не магія."""
        self._silent("hundreds = number // 100\n"
                     "tens = (number // 10) % 10\n"
                     "units = number % 10\n"
                     "total = hundreds + tens + units\n", "repeated-literal")

    def test_repeated_string_is_reported(self):
        remark = self._one('print("готово")\nprint("готово")\nprint("готово")\n',
                           "repeated-literal")
        self.assertIn("готово", remark.title)

    def test_repeated_literal_is_reported(self):
        remark = self._one("print(4.5)\nprint(4.5)\nprint(4.5)\n", "repeated-literal")
        self.assertIn("4.5", remark.title)
        self.assertIn("3", remark.title)
        self._silent("print(4.5)\nprint(4.4)\nprint(4.5)\n", "repeated-literal")
        self._silent("for step in range(3):\n    print(step + 1)\n", "repeated-literal")

    def test_boolean_returns_are_reported(self):
        remark = self._one("def passed(marks):\n"
                           "    if marks:\n"
                           "        return True\n"
                           "    else:\n"
                           "        return False\n", "boolean-return")
        self.assertIn("return умова", remark.advice)
        self._silent("def passed(marks):\n"
                     "    if marks:\n"
                     "        return True\n"
                     "    return False\n", "boolean-return")
        self._silent("def rank(marks):\n"
                     "    if marks:\n"
                     "        return 5\n"
                     "    else:\n"
                     "        return 2\n", "boolean-return")

    def test_long_function_is_reported(self):
        body = "".join(f"    step_{index} = {index + 10}\n" for index in range(26))
        remark = self._one(f"def big():\n{body}    return step_0\n", "long-function")
        self.assertIn("big", remark.title)
        self._silent("def small():\n    return 42\n", "long-function")

    def test_camel_case_is_reported(self):
        remark = self._one("totalSum = 3\nprint(totalSum)\n", "naming")
        self.assertIn("total_sum", remark.advice)
        self._silent("MAX_SIZE = 3\nprint(MAX_SIZE)\n", "naming")
        self._silent("total_sum = 3\nprint(total_sum)\n", "naming")

    def test_function_with_a_letter_name_is_reported(self):
        remark = self._one("def f(marks):\n    return sum(marks)\n", "short-function-name")
        self.assertIn("average_marks", remark.advice)
        self._silent("def average_marks(marks):\n    return sum(marks)\n",
                     "short-function-name")


class ReviewShapeTests(ReviewTestCase):
    def test_issues_are_sorted_by_line(self):
        code = ("import random\n"
                "import math\n"
                "value = 3\n"
                "print(math.pi)\n"
                "if value == True:\n"
                "    print('так')\n")
        lines = [r.line for r in review_code(code).issues]
        self.assertEqual(lines, sorted(lines))
        self.assertTrue(all(lines), "у кожного зауваження має бути рядок")

    def test_limit_keeps_the_review_readable(self):
        code = "".join(f"unused_{index} = {index + 10}\n" for index in range(12))
        review = review_code(code)
        self.assertEqual(len(review.issues), MAX_REMARKS)
        self.assertIn("12", review.summary)
        self.assertIn("Розібрати ще раз", review.summary)

    def test_praise_about_names_does_not_praise_bad_names(self):
        review = review_code("def AvgOfMarks(marks):\n    return sum(marks)\n")
        self.assertEqual([r.kind for r in review.praises], [])
        self.assertIn("naming", [r.kind for r in review.issues])

    def test_praise_never_hides_issues(self):
        review = review_code('"""Опис."""\nimport random\nprint(1)\n')
        self.assertEqual([r.kind for r in review.issues], ["unused-import"])
        self.assertFalse(review.ok)

    def test_line_numbers_fit_the_file(self):
        for task in all_tasks():
            for code in (task.starter, task.solution_hint.text if task.solution_hint else ""):
                total = code.count("\n") + 1
                for remark in review_code(code, limit=99).remarks:
                    self.assertLessEqual(remark.line, total, task.id)
                    self.assertGreaterEqual(remark.line, 0, task.id)

    def test_issues_phrase_speaks_ukrainian(self):
        self.assertEqual(issues_phrase(1), "1 зауваження")
        self.assertEqual(issues_phrase(3), "3 зауваження")
        self.assertEqual(issues_phrase(7), "7 зауважень")
        self.assertEqual(issues_phrase(21), "21 зауваження")
        self.assertEqual(issues_phrase(111), "111 зауважень")

    def test_every_rule_explains_itself(self):
        """Правило без пояснення в коді — це зауваження, яке нікому не зрозуміле."""
        for rule in RULES:
            self.assertTrue(rule.__doc__, rule.__name__)
            review = review_code("value = 1\nprint(value)\n")
            self.assertNotIn(rule.__name__, [r.kind for r in review.issues])

    def test_rules_survive_strange_but_valid_code(self):
        samples = [
            "",
            "x = 1; y = 2\n",
            "class A:\n    def f(self):\n        ...\n",
            "async def f(items):\n    async for item in items:\n        print(item)\n",
            "match value:\n    case 1:\n        print('один')\n    case _:\n        print('інше')\n",
            "values = [item for item in range(3) if item]\n",
            "if (n := 10) > 5:\n    print(n)\n",
            "def f(*args, **kwargs):\n    return len(args) + len(kwargs)\n",
            "global_value: int = 0\n",
            "counter: int\n",
            "def f(badName):\n    return badName\n",
            "def f(items=[]):\n    items.append(1)\n    return items\n",
            "with open('a.txt', encoding='utf-8') as first, open('b.txt') as second:\n"
            "    print(first.read(), second.read())\n",
            "def outer():\n    def inner():\n        return 1\n    return inner\n",
            "try:\n    pass\nfinally:\n    print('готово')\n",
        ]
        for sample in samples:
            review = review_code(sample)
            self.assertIsInstance(review.remarks, tuple, sample)
            self.assertTrue(review.summary, sample)

    def test_a_broken_rule_does_not_break_the_whole_review(self):
        """Код користувача буває який завгодно — розбір не має падати."""
        def boom(tree, keep):
            raise ValueError("правило зламалось")

        with mock.patch.object(codereview, "RULES",
                               (boom, codereview._unused_imports)):
            review = review_code("import random\nprint('готово')\n")

        self.assertEqual([r.kind for r in review.issues], ["unused-import"])

    def test_deep_nesting_is_found_inside_every_branch(self):
        """Лабіринт — він і в `elif`, і в `except`, і в `finally`, і в `match`."""
        samples = {
            "elif": (
                "value = 1\n"
                "if value == 10:\n"
                "    print('x')\n"
                "elif value:\n"
                "    if value:\n"
                "        for item in [1, 2]:\n"
                "            if item:\n"
                "                print(item)\n"
            ),
            "except": (
                "value = 1\n"
                "try:\n"
                "    print(value)\n"
                "except ValueError:\n"
                "    if value:\n"
                "        for item in [1, 2]:\n"
                "            if item:\n"
                "                print(item)\n"
            ),
            "finally": (
                "value = 1\n"
                "try:\n"
                "    print(value)\n"
                "finally:\n"
                "    if value:\n"
                "        for item in [1, 2]:\n"
                "            if item:\n"
                "                print(item)\n"
            ),
            "match": (
                "value = 1\n"
                "match value:\n"
                "    case 1:\n"
                "        if value:\n"
                "            for item in [1, 2]:\n"
                "                if item:\n"
                "                    print(item)\n"
            ),
        }
        for name, code in samples.items():
            self.assertIn("deep-nesting", self._issues(code), name)

    def test_deeply_nested_code_does_not_break_the_review(self):
        code = "value = 10\n"
        for depth in range(80):
            code += "    " * depth + f"if value == {depth + 20}:\n"
        code += "    " * 80 + "print(value)\n"
        self.assertIn("deep-nesting", self._issues(code))


class HiddenCheckTests(ReviewTestCase):
    """Перевірки виконуються в тому ж файлі — і розбір має про це знати.

    Інакше він радить видалити `from fake_api import BASE_URL`, без якого
    задача перестає здаватись: найгірше, що може зробити порадник.
    """

    def test_names_of_hidden_checks_are_collected(self):
        names = names_used_in([
            'assert isinstance(fetch_json(BASE_URL + "/rates"), dict)',
            "import inspect\nassert inspect.isfunction(fetch_text)",
        ])
        self.assertIn("BASE_URL", names)
        self.assertIn("fetch_json", names)
        self.assertIn("inspect", names)

    def test_broken_snippet_is_skipped_not_swallowed(self):
        self.assertEqual(names_used_in(["def broken(:"]), set())

    def test_kept_names_are_not_reported_as_unused(self):
        code = "from fake_api import BASE_URL\n\nvalue = 1\nprint(value)\n"
        self.assertIn("unused-import", self._issues(code))
        self.assertNotIn("unused-import",
                         [r.kind for r in review_code(code, keep={"BASE_URL"}).issues])
        self.assertNotIn("unused-name", [r.kind for r in review_code(
            "hidden = 5\nprint('готово')\n", keep={"hidden"}
        ).issues])


class CurriculumReviewTests(ReviewTestCase):
    def test_review_survives_every_task_in_the_curriculum(self):
        """Розбір — це UI: він не має права впасти на коді жодної задачі."""
        checked = 0
        for task in all_tasks():
            codes = [task.starter]
            if task.solution_hint:
                codes.append(task.solution_hint.text)
            for code in codes:
                review = review_code(code, keep=names_used_in(
                    check.code for check in task.checks if check.code
                ))
                self.assertTrue(review.summary, task.id)
                for remark in review.remarks:
                    self.assertIsInstance(remark.line, int, task.id)
                    self.assertTrue(remark.kind.strip(), task.id)
                    self.assertNotIn(" ", remark.kind, task.id)
                checked += 1
        self.assertGreater(checked, 150)


if __name__ == "__main__":
    unittest.main()
