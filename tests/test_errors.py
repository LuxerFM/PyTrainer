"""Тести пояснювача помилок.

Головне тут — що реальні traceback-и Python розпізнаються, і що на невідомій
помилці ми не вигадуємо дурниць, а кажемо чесно: «глянь консоль».
"""

import unittest

from trainer.core.errors import analyse, analyse_short, explain, kind_of
from trainer.core.runner import CheckResult, RunResult

NAME_ERROR = '''Traceback (most recent call last):
  File "solution.py", line 3, in <module>
    print(total)
NameError: name 'total' is not defined
'''

SYNTAX_ERROR = '''  File "solution.py", line 2
    print("привіт"
         ^
SyntaxError: '(' was never closed
'''

INDENT_ERROR = '''  File "solution.py", line 4
    print("другий")
    ^
IndentationError: unexpected indent
'''

KEY_ERROR = '''Traceback (most recent call last):
  File "solution.py", line 2, in <module>
    print(prices["ківі"])
KeyError: 'ківі'
'''

ASSERT_ERROR = '''Traceback (most recent call last):
  File "solution.py", line 1, in <module>
    assert average([1, 2]) == 2, "середнє порахувалось не так"
AssertionError: середнє порахувалось не так
'''

UNKNOWN_ERROR = '''Traceback (most recent call last):
  File "solution.py", line 1, in <module>
    raise NotImplementedError("ще не зроблено")
NotImplementedError: ще не зроблено
'''


class AnalyseTests(unittest.TestCase):
    def test_name_error(self):
        found = analyse(NAME_ERROR)
        self.assertIsNotNone(found)
        self.assertEqual(found.kind, "NameError")
        self.assertEqual(found.line, 3)
        self.assertEqual(found.source, "print(total)")
        self.assertIn("ім", found.meaning)          # «ім'я не знайдене»
        self.assertIn("лапки", found.advice)

    def test_syntax_error_points_to_the_line(self):
        found = analyse(SYNTAX_ERROR)
        self.assertEqual(found.kind, "SyntaxError")
        self.assertEqual(found.line, 2)
        self.assertIn("print", found.source)
        self.assertIn("дужку", found.advice)

    def test_indentation_error(self):
        found = analyse(INDENT_ERROR)
        self.assertEqual(found.kind, "IndentationError")
        self.assertIn("4", found.advice)            # скільки пробілів

    def test_key_error_suggests_get(self):
        found = analyse(KEY_ERROR)
        self.assertEqual(found.kind, "KeyError")
        self.assertIn("get", found.advice)

    def test_assertion_error_message_without_quotes(self):
        found = analyse(ASSERT_ERROR)
        self.assertEqual(found.kind, "AssertionError")
        self.assertEqual(found.message, "середнє порахувалось не так")

    def test_unknown_exception_still_gets_generic_help(self):
        found = analyse(UNKNOWN_ERROR)
        self.assertEqual(found.kind, "NotImplementedError")
        self.assertTrue(found.advice)

    def test_every_known_error_has_explanation(self):
        from trainer.core.errors import EXPLANATIONS

        for kind, (meaning, advice) in EXPLANATIONS.items():
            with self.subTest(kind=kind):
                self.assertTrue(meaning.strip(), f"{kind}: немає пояснення")
                self.assertTrue(advice.strip(), f"{kind}: немає поради")

    def test_empty_stderr_gives_nothing(self):
        self.assertIsNone(analyse(""))
        self.assertIsNone(analyse("   \n"))
        self.assertEqual(explain(""), "")

    def test_unrecognised_noise_does_not_crash(self):
        found = analyse("щось зовсім не схоже на traceback")
        self.assertIsNotNone(found)
        self.assertTrue(found.meaning)

    def test_ignores_foreign_files_in_traceback(self):
        """Рядок із чужого файлу не має видаватись за код користувача."""
        stderr = (
            'Traceback (most recent call last):\n'
            '  File "C:\\Python\\lib\\json\\decoder.py", line 355, in raw_decode\n'
            '  File "solution.py", line 7, in <module>\n'
            '    json.loads(text)\n'
            'JSONDecodeError: Expecting value: line 1 column 1 (char 0)\n'
        )
        found = analyse(stderr)
        self.assertEqual(found.line, 7)
        self.assertEqual(found.source, "json.loads(text)")


class ShortFormTests(unittest.TestCase):
    """Пояснення для одного рядка — так харнес віддає помилки з перевірок."""

    def test_parses_check_exception(self):
        found = analyse_short("NameError: name 'number' is not defined")
        self.assertIsNotNone(found)
        self.assertEqual(found.kind, "NameError")
        self.assertIn("Що робити", found.as_text())

    def test_parses_assertion_message(self):
        found = analyse_short("AssertionError: середнє порахувалось не так")
        self.assertEqual(found.kind, "AssertionError")
        self.assertEqual(found.message, "середнє порахувалось не так")

    def test_plain_phrase_is_not_treated_as_exception(self):
        """«У виводі немає «Привіт»» — не помилка з назвою типу."""
        self.assertIsNone(analyse_short("У виводі немає «Привіт»"))
        self.assertIsNone(analyse_short(""))


class RunResultAdviceTests(unittest.TestCase):
    def test_no_advice_when_everything_passed(self):
        result = RunResult(
            ran_checks=True,
            checks=[CheckResult(name="тест", ok=True)],
        )
        self.assertEqual(result.advice, "")

    def test_timeout_advice_talks_about_the_loop(self):
        result = RunResult(timed_out=True, exit_code=-1)
        self.assertIn("цикл", result.advice.lower())

    def test_crash_advice_uses_the_explainer(self):
        result = RunResult(stderr=NAME_ERROR, exit_code=1)
        self.assertIn("NameError", result.advice)
        self.assertIn("Що робити", result.advice)

    def test_clean_run_has_no_advice(self):
        result = RunResult(stdout="привіт", exit_code=0)
        self.assertEqual(result.advice, "")

    def test_advice_from_a_failed_check_without_stderr(self):
        """Найчастіший випадок: перевірка впала винятком, stderr порожній."""
        result = RunResult(
            ran_checks=True,
            checks=[CheckResult(name="простий випадок", ok=False,
                                error="NameError: name 'number' is not defined")],
        )
        self.assertEqual(result.stderr, "")
        self.assertIn("NameError", result.advice)
        self.assertIn("Що робити", result.advice)

    def test_advice_is_empty_for_a_plain_wrong_output(self):
        """「вивід не той» — не помилка Python, вигадувати пояснення не треба."""
        result = RunResult(
            ran_checks=True,
            checks=[CheckResult(name="виводить привітання", ok=False,
                                error="У виводі немає «Привіт»")],
        )
        self.assertEqual(result.advice, "")

    def test_kind_of(self):
        self.assertEqual(kind_of(NAME_ERROR), "NameError")
        self.assertEqual(kind_of(""), "")


if __name__ == "__main__":
    unittest.main()
