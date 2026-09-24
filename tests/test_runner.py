"""Тести ядра перевірки: запуск коду, фікстури вводу, вердикти.

Запуск: .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import unittest

from curriculum import find_task
from curriculum.schema import code, stdout
from trainer.core.runner import run_code, run_task


class RunCodeTests(unittest.TestCase):
    def test_prints_stdout(self):
        result = run_code('print("привіт")')
        self.assertEqual(result.stdout, "привіт")
        self.assertEqual(result.exit_code, 0)

    def test_ukrainian_text_survives(self):
        result = run_code('print("Ґудзик, їжак, Євген")')
        self.assertIn("Ґудзик, їжак, Євген", result.stdout)

    def test_code_check_passes(self):
        result = run_code(
            "def add(a, b):\n    return a + b\n",
            [code("додає", "assert add(2, 3) == 5")],
        )
        self.assertTrue(result.all_passed)
        self.assertEqual(result.passed_count, 1)

    def test_code_check_fails_with_reason(self):
        result = run_code(
            "def add(a, b):\n    return a - b\n",
            [code("додає", "assert add(2, 3) == 5")],
        )
        self.assertFalse(result.all_passed)
        self.assertIn("AssertionError", result.first_error)

    def test_stdout_check_with_input_fixture(self):
        source = 'name = input("Ім\'я: ")\nprint(f"Привіт, {name}!")\n'
        result = run_code(
            source, [stdout("вітається", contains="Привіт, Аня", stdin="Аня\n")]
        )
        self.assertTrue(result.all_passed)
        self.assertEqual(result.checks[0].actual.strip(), "Ім'я: Привіт, Аня!")

    def test_stdout_not_contains_catches_wrong_branch(self):
        source = 'print("непарне")'
        result = run_code(
            source,
            [stdout("має бути парне", contains="парне", not_contains="непарне",
                    stdin="8\n")],
        )
        self.assertFalse(result.all_passed)
        self.assertIn("зайве", result.first_error)

    def test_stdout_lines_check(self):
        result = run_code('print("a")', [stdout("два рядки", lines=2)])
        self.assertFalse(result.all_passed)
        self.assertIn("щонайменше 2 рядків", result.first_error)

    def test_order_of_checks_is_kept(self):
        result = run_code(
            "def ok():\n    return True\n",
            [
                code("перша", "assert ok()"),
                stdout("друга", contains="x", stdin=""),
                code("третя", "assert ok()"),
            ],
        )
        self.assertEqual([check.name for check in result.checks],
                         ["перша", "друга", "третя"])

    def test_timeout_stops_infinite_loop(self):
        result = run_code("while True:\n    pass\n", timeout=1.0)
        self.assertTrue(result.timed_out)

    def test_timeout_marks_checks_as_failed(self):
        result = run_code("while True:\n    pass\n", [code("щось", "assert True")],
                          timeout=1.0)
        self.assertFalse(result.all_passed)
        self.assertIn("не завершився", result.first_error)

    def test_syntax_error_reported(self):
        result = run_code("def broken(:\n    pass\n")
        self.assertIn("SyntaxError", result.stderr)
        self.assertFalse(result.all_passed)

    def test_crash_reason_for_checks(self):
        result = run_code("raise ValueError('немає даних')", [code("перевірка", "assert True")])
        self.assertIn("ValueError", result.first_error)

    def test_input_without_fixture_does_not_hang(self):
        result = run_code("name = input()\nprint(name)")
        self.assertIn("EOFError", result.stderr)

    def test_marker_line_is_hidden_from_stdout(self):
        result = run_code('print("готово")', [code("перевірка", "assert True")])
        self.assertEqual(result.stdout, "готово")

    # ---------- файли проєкту ----------

    def test_extra_files_are_importable(self):
        source = "import utils\nprint(utils.double(21))\n"
        result = run_code(
            source,
            files={"utils.py": "def double(value):\n    return value * 2\n"},
        )
        self.assertEqual(result.stdout, "42")

    def test_extra_files_work_with_code_checks(self):
        source = "import utils\n\ndef answer():\n    return utils.double(21)\n"
        result = run_code(
            source,
            [code("використовує модуль", "assert answer() == 42")],
            files={"utils.py": "def double(value):\n    return value * 2\n"},
        )
        self.assertTrue(result.all_passed)

    def test_missing_file_is_reported(self):
        result = run_code("import utils\n", [code("перевірка", "assert True")])
        self.assertIn("ModuleNotFoundError", result.first_error)

    def test_custom_entrypoint(self):
        result = run_code(
            'print("з main")\n',
            entrypoint="main.py",
            files={"helper.py": "VALUE = 1\n"},
        )
        self.assertEqual(result.stdout, "з main")

    # ---------- захист від великого виводу ----------

    def test_huge_output_is_truncated(self):
        result = run_code(
            "for index in range(200000):\n    print('x' * 40)\n", timeout=10
        )
        self.assertLess(len(result.stdout), 130_000)
        self.assertIn("вивід обрізано", result.stdout)
        self.assertTrue(result.output_truncated)

    # ---------- запуск у контексті задачі ----------

    def test_run_task_uses_task_files(self):
        task = find_task("m2-module")
        self.assertTrue(task.has_files)
        result = run_task(task, task.solution_hint.text)
        self.assertTrue(result.all_passed)


if __name__ == "__main__":
    unittest.main()
