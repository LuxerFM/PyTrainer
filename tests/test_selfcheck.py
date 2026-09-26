"""Тести самоперевірки (`--self-test`): чи справді код виконується й перевіряється.

Самоперевірка існує заради зібраного `.exe`, але її кроки — це звичайні
запуски коду, тому вона рівно так само корисна з коду: вона перевіряє не
«чи намалювалось вікно», а «чи прийшов вердикт».

Запуск: .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from trainer.core import selfcheck
from trainer.core.selfcheck import SelfCheckReport, SelfCheckStep, run_self_check

MODE = ("python", "exe")


class SelfCheckTests(unittest.TestCase):
    """Одна справжня самоперевірка на весь клас: кроки запускають процеси."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = run_self_check()

    def test_all_steps_pass(self) -> None:
        for step in self.report.steps:
            self.assertTrue(step.ok, f"{step.name}: {step.detail}")
        self.assertTrue(self.report.ok)

    def test_every_kind_of_check_is_covered(self) -> None:
        """Кроки мають покривати те, що ламалось: перевірки, вивід і таймаут."""
        names = [step.name for step in self.report.steps]
        self.assertEqual(len(names), 3)
        self.assertIn("правильний розв'язок проходить перевірки", names)
        self.assertIn("зламаний розв'язок не проходить", names)
        self.assertIn("нескінченний цикл зупиняється таймаутом", names)

    def test_report_knows_where_it_was_run(self) -> None:
        self.assertIn(self.report.mode, MODE)

    def test_text_shows_every_step_and_the_verdict(self) -> None:
        text = self.report.as_text()
        for step in self.report.steps:
            self.assertIn(step.name, text)
        self.assertIn("усе гаразд", text)

    def test_dictionary_survives_json(self) -> None:
        data = json.loads(json.dumps(self.report.as_dict()))
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["steps"]), 3)
        self.assertTrue(data["python"])

    def test_broken_step_is_a_broken_report(self) -> None:
        report = SelfCheckReport(frozen=False, steps=[SelfCheckStep("крок", False, "не так")])
        self.assertFalse(report.ok)
        self.assertIn("НЕ працює", report.as_text())

    def test_report_without_steps_is_not_a_success(self) -> None:
        """Порожній звіт — це «нічого не перевірили», а не «все гаразд»."""
        self.assertFalse(SelfCheckReport(frozen=True).ok)

    def test_crash_of_the_trainer_is_a_failed_step_not_a_crash(self) -> None:
        """Так виглядав справжній баг: WinError 32 посеред перевірки."""
        with mock.patch.object(selfcheck, "run_code", side_effect=PermissionError("WinError 32")):
            report = run_self_check()
        self.assertFalse(report.ok)
        self.assertTrue(all(not step.ok for step in report.steps))
        self.assertIn("PermissionError", report.steps[0].detail)


class ReportPathTests(unittest.TestCase):
    def test_explicit_path_wins(self) -> None:
        self.assertEqual(
            selfcheck.report_path_from(["PyTrainer.exe", "--self-test", "звіт.json"], True),
            Path("звіт.json"),
        )

    def test_exe_writes_the_report_next_to_itself(self) -> None:
        """У віконного .exe немає консолі — друкувати йому нікуди."""
        from trainer.paths import app_folder

        self.assertEqual(
            selfcheck.report_path_from(["PyTrainer.exe", "--self-test"], True),
            app_folder() / selfcheck.DEFAULT_REPORT,
        )

    def test_run_from_code_does_not_create_files(self) -> None:
        self.assertIsNone(selfcheck.report_path_from(["main.py", "--self-test"], False))

    def test_other_commands_have_no_report(self) -> None:
        self.assertIsNone(selfcheck.report_path_from(["main.py", "--demo"], True))


class SelfCheckCommandTests(unittest.TestCase):
    """Сам `--self-test`: код виходу, файл звіту, вивід на екран."""

    def setUp(self) -> None:
        self.report = SelfCheckReport(
            frozen=False, steps=[SelfCheckStep("крок", True, "усе гаразд")]
        )

    def run_command(self, *arguments: str) -> int:
        with mock.patch.object(selfcheck, "run_self_check", return_value=self.report):
            return selfcheck.main(["main.py", selfcheck.FLAG, *arguments])

    def test_success_returns_zero_and_writes_the_report(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "selftest.json"
            self.assertEqual(self.run_command(str(target)), 0)
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"])
            self.assertEqual(data["steps"][0]["name"], "крок")

    def test_failure_returns_one(self) -> None:
        self.report.steps = [SelfCheckStep("крок", False, "не так")]
        self.assertEqual(self.run_command(), 1)

    def test_prints_the_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "selftest.json"
            printed = io.StringIO()
            with mock.patch.object(sys, "stdout", printed):
                self.run_command(str(target))
            self.assertIn("усе гаразд", printed.getvalue())
            self.assertIn("Звіт", printed.getvalue())

    def test_says_nothing_when_there_is_nowhere_to_print(self) -> None:
        with mock.patch.object(sys, "stdout", None), mock.patch.object(sys, "stderr", None):
            self.assertIsNone(selfcheck._say("текст"))


if __name__ == "__main__":
    unittest.main()
