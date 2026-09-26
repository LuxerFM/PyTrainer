"""Тести режиму `--exec-runner`: .exe виконує код користувача сам, собою.

Це найтонше місце всієї програми і найгірше для тестів: поки застосунок
запускається з коду, цей режим узагалі не використовується. Тому перевіряємо
його як окремий процес — рівно так, як його запускає runner, а в зібраному
`.exe` — сам тренажер.

Запуск: .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from trainer import cli
from trainer.core import exec_runner, selfcheck
from trainer.core.runner import interpreter_command

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


class ScriptRunnerTests(unittest.TestCase):
    """Те, що бачить код користувача: аргументи, тека, вивід, код виходу."""

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory(prefix="pytrainer_exec_")
        self.addCleanup(self.folder.cleanup)
        self.workdir = Path(self.folder.name)

    def write(self, name: str, source: str) -> Path:
        target = self.workdir / name
        target.write_text(source, encoding="utf-8")
        return target

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess:
        """Запускає режим так, як його запускає runner (а .exe — сам себе)."""
        return subprocess.run(
            [sys.executable, str(MAIN), "--exec-runner", *arguments],
            cwd=self.workdir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            timeout=60,
        )

    def test_script_runs_and_prints(self) -> None:
        self.write("solution.py", 'print("Привіт, Світ")\n')
        done = self.run_script("solution.py")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("Привіт, Світ", done.stdout)

    def test_script_can_import_a_neighbour_file(self) -> None:
        """`import utils` працює як у справжньому проєкті — як і з коду."""
        self.write("utils.py", "def double(value):\n    return value * 2\n")
        self.write("solution.py", "import utils\n\nprint(utils.double(21))\n")
        done = self.run_script("solution.py")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("42", done.stdout)

    def test_script_runs_in_its_own_folder(self) -> None:
        """Робоча тека — тека файла, інакше відносні шляхи ламались би."""
        self.write("solution.py", "import os\n\nprint(os.path.basename(os.getcwd()))\n")
        done = self.run_script("solution.py")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(self.workdir.name, done.stdout)

    def test_exit_code_of_the_script_is_returned(self) -> None:
        self.write("solution.py", "raise SystemExit(3)\n")
        self.assertEqual(self.run_script("solution.py").returncode, 3)

    def test_quiet_exit_returns_zero(self) -> None:
        self.write("solution.py", "import sys\n\nsys.exit()\n")
        self.assertEqual(self.run_script("solution.py").returncode, 0)

    def test_exit_with_message_prints_it(self) -> None:
        """`sys.exit("текст")` — повідомлення в stderr і код 1, як у Python."""
        self.write("solution.py", 'raise SystemExit("немає файлу")\n')
        done = self.run_script("solution.py")
        self.assertEqual(done.returncode, 1)
        self.assertIn("немає файлу", done.stderr)

    def test_error_goes_to_stderr_with_traceback(self) -> None:
        """Помилку друкуємо самі: у віконному .exe вона інакше стала б діалогом."""
        self.write("solution.py", "raise ValueError('щось не так')\n")
        done = self.run_script("solution.py")
        self.assertEqual(done.returncode, 1)
        self.assertIn("ValueError", done.stderr)
        self.assertIn("Traceback", done.stderr)

    def test_missing_path_is_reported_as_usage_error(self) -> None:
        done = self.run_script()
        self.assertEqual(done.returncode, 2)
        self.assertIn(exec_runner.FLAG, done.stderr)


class InProcessTests(unittest.TestCase):
    """Той самий режим, але як звичайна функція — так його бачить .exe.

    У зібраному `.exe` `main.py` викликає саме `exec_runner.main()`, тому
    перевіряємо і цей вхід, а не лише окремий процес.
    """

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory(prefix="pytrainer_inproc_")
        self.addCleanup(self.folder.cleanup)
        self.workdir = Path(self.folder.name)
        self.addCleanup(os.chdir, os.getcwd())
        self.addCleanup(sys.path.__setitem__, slice(None), list(sys.path))
        self.addCleanup(setattr, sys, "argv", list(sys.argv))

    def test_prints_what_the_script_printed(self) -> None:
        script = self.workdir / "solution.py"
        script.write_text('print("привіт")\n', encoding="utf-8")
        printed = io.StringIO()
        with mock.patch.object(sys, "stdout", printed):
            code = exec_runner.main(["PyTrainer.exe", exec_runner.FLAG, str(script)])
        self.assertEqual(code, 0)
        self.assertIn("привіт", printed.getvalue())
        self.assertEqual(os.getcwd(), str(self.workdir))

    def test_exit_code_of_the_script_is_returned(self) -> None:
        script = self.workdir / "solution.py"
        script.write_text("raise SystemExit(4)\n", encoding="utf-8")
        self.assertEqual(
            exec_runner.main(["PyTrainer.exe", exec_runner.FLAG, str(script)]), 4
        )


class ArgumentTests(unittest.TestCase):
    def test_path_is_taken_after_the_flag(self) -> None:
        self.assertEqual(
            exec_runner.script_from(["PyTrainer.exe", "--exec-runner", "solution.py"]),
            "solution.py",
        )

    def test_leading_flags_are_skipped(self) -> None:
        """Файл — це перший аргумент, який не схожий на прапорець."""
        self.assertEqual(
            exec_runner.script_from(["x", "--exec-runner", "--noconsole", "solution.py"]),
            "solution.py",
        )

    def test_other_commands_know_nothing_about_the_runner(self) -> None:
        self.assertEqual(exec_runner.script_from(["PyTrainer.exe", "--demo"]), "")


class StreamTests(unittest.TestCase):
    """Кодування й наявність стандартних потоків у віконному .exe.

    Тут ламаються дві речі одразу: потоку може не бути взагалі, і він може
    мати кодування системи (cp1251), через яке весь український вивід стає
    «??????» — а runner читає його як UTF-8.
    """

    def test_missing_streams_are_attached_to_the_real_files(self) -> None:
        with mock.patch.object(sys, "stdout", None), mock.patch.object(sys, "stderr", None):
            exec_runner.ensure_streams()
            stdout, stderr = sys.stdout, sys.stderr
        self.assertIsNotNone(stdout)
        self.assertIsNotNone(stderr)
        # Закриваємо обгортки, щоб вони не «протекли» в інші тести; самі
        # дескриптори 1 і 2 лишаються відкритими (closefd=False).
        stdout.close()
        stderr.close()

    def test_missing_descriptor_falls_back_to_devnull(self) -> None:
        with mock.patch.object(sys, "stdout", None), \
                mock.patch.object(exec_runner.os, "fdopen", side_effect=OSError):
            exec_runner.ensure_streams()
            stream = sys.stdout
        self.assertIsNotNone(stream)
        stream.close()

    def test_existing_streams_are_kept(self) -> None:
        before = sys.stdout
        exec_runner.ensure_streams()
        self.assertIs(before, sys.stdout)

    def test_exe_switches_the_system_encoding_to_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            # Саме справжній TextIOWrapper: так само виглядають потоки, які
            # приєднує віконний .exe.
            with open(Path(folder) / "console.txt", "w+", encoding="cp1251") as handle:
                with mock.patch.object(sys, "frozen", True, create=True), \
                        mock.patch.object(sys, "stdin", handle), \
                        mock.patch.object(sys, "stdout", handle), \
                        mock.patch.object(sys, "stderr", handle):
                    exec_runner.ensure_streams()
                    self.assertIs(sys.stdout, handle)
                    self.assertEqual(sys.stdout.encoding.lower().replace("-", "_"), "utf_8")

    def test_run_from_code_keeps_the_console_encoding(self) -> None:
        """З коду кодування консолі правильне — переводити його не можна."""
        with tempfile.TemporaryDirectory() as folder:
            with open(Path(folder) / "console.txt", "w+", encoding="cp1251") as handle:
                with mock.patch.object(sys, "stdout", handle):
                    exec_runner.ensure_streams()
                    self.assertEqual(sys.stdout.encoding, "cp1251")

    def test_stream_without_encoding_is_left_alone(self) -> None:
        """Підмінені в тестах потоки (StringIO) переписувати нічим."""
        replaced = io.StringIO()
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "stdout", replaced):
            exec_runner.ensure_streams()
            self.assertIs(replaced, sys.stdout)


class InterpreterTests(unittest.TestCase):
    """Яким інтерпретатором запускається код користувача."""

    def test_normal_run_uses_python_with_its_flags(self) -> None:
        command = interpreter_command("solution.py")
        self.assertEqual(command[0], sys.executable)
        self.assertIn("-u", command)
        self.assertEqual(command[-1], "solution.py")

    def test_frozen_run_asks_the_exe_to_run_the_file(self) -> None:
        """Найважливіший рядок: у зібраному .exe `sys.executable` — це сам тренажер.

        Якщо тут знову опиниться `python -X utf8`, кожна перевірка
        запускатиме друге вікно PyTrainer, і код користувача не виконається
        ніколи. Саме так тренажер і поводився до цієї правки.
        """
        exe = ROOT / "dist" / "PyTrainer.exe"
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "executable", str(exe)):
            self.assertEqual(
                interpreter_command("solution.py"),
                [str(exe), exec_runner.FLAG, "solution.py"],
            )


class CliTests(unittest.TestCase):
    """Вибір режиму: прапорці не мають випадково відкривати вікно."""

    def test_exec_runner_flag_goes_to_the_runner(self) -> None:
        with mock.patch.object(exec_runner, "main", return_value=7) as called:
            code = cli.main(["PyTrainer.exe", exec_runner.FLAG, "solution.py"])
        self.assertEqual(code, 7)
        called.assert_called_once()

    def test_self_test_flag_goes_to_the_self_check(self) -> None:
        with mock.patch.object(selfcheck, "main", return_value=1) as called:
            self.assertEqual(cli.main(["main.py", selfcheck.FLAG]), 1)
        called.assert_called_once()

    def test_everything_else_opens_the_window(self) -> None:
        from trainer import app

        with mock.patch.object(app, "main", return_value=0) as called:
            self.assertEqual(cli.main(["main.py", "--demo"]), 0)
        called.assert_called_once()


if __name__ == "__main__":
    unittest.main()
