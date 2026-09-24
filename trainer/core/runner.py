"""Запуск коду користувача в окремому процесі + перевірка прихованими тестами.

Три речі, які тут важливі:

1. **Окремий процес.** Якщо в коді буде `while True`, ми вб'ємо цей процес по
   таймауту, і застосунок продовжить працювати. Якби ми виконували код у себе,
   зависла б уся програма.

2. **Ліміт виводу.** `print` у циклі за 5 секунд друкує сотні мегабайт. Тому
   вивід пишеться у файл, а ми читаємо лише перші MAX_OUTPUT_BYTES — інакше
   витік пам'яті був би в нас, а не в коді користувача.

3. **Кілька файлів.** Задача може принести із собою допоміжні файли (наприклад
   `utils.py`, який треба імпортувати). Вони пишуться в ту саму тимчасову папку,
   тому `import utils` у розв'язку працює як у справжньому проєкті.

Перевірки бувають двох видів:
  * перевірка коду — assert-вираз, який виконується після коду користувача
    в тому ж середовищі (тому бачить його функції та змінні);
  * перевірка виводу — окремий запуск, де програмі подається ввід (ніби
    користувач щось надрукував) і порівнюється те, що вона вивела.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

from curriculum.schema import Check

MARKER = "__PYTRAINER_RESULTS__"
DEFAULT_TIMEOUT = 5.0
MAX_OUTPUT_BYTES = 64 * 1024
DEFAULT_ENTRYPOINT = "solution.py"

HARNESS = '''

# ---------- службовий код тренажера (не твій, не редагуй) ----------
import json as _json

_results = []


def _check(_name, _source):
    try:
        exec(compile(_source, "<тест>", "exec"), globals())
    except BaseException as _error:            # ловимо все, навіть assert
        _results.append({"name": _name, "ok": False,
                         "error": "%s: %s" % (type(_error).__name__, _error)})
    else:
        _results.append({"name": _name, "ok": True, "error": ""})
'''


@dataclass
class CheckResult:
    """Результат однієї прихованої перевірки."""

    name: str
    ok: bool
    error: str = ""
    actual: str = ""


@dataclass
class RunResult:
    """Усе, що ми дізналися після запуску коду."""

    stdout: str = ""
    stderr: str = ""
    checks: list[CheckResult] = field(default_factory=list)
    exit_code: int = 0
    timed_out: bool = False
    ran_checks: bool = False
    stdin: str = ""
    output_truncated: bool = False

    @property
    def all_passed(self) -> bool:
        return self.ran_checks and all(check.ok for check in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for check in self.checks if check.ok)

    @property
    def first_error(self) -> str:
        for check in self.checks:
            if not check.ok:
                return check.error
        return ""

    @property
    def crashed(self) -> bool:
        return self.exit_code != 0 and not self.timed_out


def _build_source(code: str, code_checks: list[Check]) -> str:
    parts = [code, HARNESS]
    for check in code_checks:
        parts.append(f"_check({check.name!r}, {check.code!r})")
    parts.append(f'print("{MARKER}" + _json.dumps(_results, ensure_ascii=False))')
    return "\n".join(parts) + "\n"


def _short(text: str, limit: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _read_capped(path: str) -> tuple[str, bool]:
    """Читає початок файлу з виводом, не затягуючи в пам'ять усе."""
    size = os.path.getsize(path)
    with open(path, "rb") as handle:
        data = handle.read(MAX_OUTPUT_BYTES)
    text = data.decode("utf-8", "replace")
    if size > MAX_OUTPUT_BYTES:
        text += f"\n…вивід обрізано ({size // 1024} КБ, показано початок)"
        return text, True
    return text, False


def _run_process(
    source: str,
    stdin: str,
    timeout: float,
    files: dict[str, str] | None = None,
    entrypoint: str = DEFAULT_ENTRYPOINT,
) -> tuple[str, str, int, bool, bool]:
    """Виконує код у тимчасовій папці.

    Повертає (stdout, stderr, код виходу, чи був таймаут, чи обрізано вивід).
    """
    with tempfile.TemporaryDirectory(prefix="pytrainer_") as workdir:
        for name, content in (files or {}).items():
            target = os.path.join(workdir, name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(content)

        with open(os.path.join(workdir, entrypoint), "w", encoding="utf-8") as handle:
            handle.write(source)

        out_path = os.path.join(workdir, "__stdout.txt")
        err_path = os.path.join(workdir, "__stderr.txt")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

        with open(out_path, "wb") as out, open(err_path, "wb") as err:
            process = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-u", entrypoint],
                stdin=subprocess.PIPE,
                stdout=out,
                stderr=err,
                cwd=workdir,          # тому sys.path[0] = тимчасова папка → import своїх файлів працює
                env=env,
            )
            try:
                process.communicate(input=stdin.encode("utf-8"), timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                timed_out = True

        stdout, out_truncated = _read_capped(out_path)
        stderr, err_truncated = _read_capped(err_path)

    if timed_out:
        stderr += f"Код працював довше ніж {timeout:g} с і був зупинений.\n"
    return stdout, stderr, (-1 if timed_out else process.returncode), timed_out, (
        out_truncated or err_truncated
    )


def _evaluate_stdout(check: Check, out: str) -> CheckResult:
    """Перевіряє вивід програми за правилами перевірки."""
    problems = []

    if check.stdout_equals is not None:
        if out.strip() != check.stdout_equals.strip():
            problems.append(
                f"Очікував «{_short(check.stdout_equals)}», а програма вивела "
                f"«{_short(out)}»"
            )

    if check.stdout_contains is not None and check.stdout_contains not in out:
        problems.append(f"У виводі немає «{_short(check.stdout_contains, 40)}»")

    if check.stdout_not_contains is not None and check.stdout_not_contains in out:
        problems.append(f"У виводі зайве «{_short(check.stdout_not_contains, 40)}»")

    if check.stdout_lines is not None:
        lines = [line for line in out.splitlines() if line.strip()]
        if len(lines) < check.stdout_lines:
            problems.append(
                f"Очікував щонайменше {check.stdout_lines} рядків, "
                f"а надруковано {len(lines)}"
            )

    return CheckResult(
        name=check.name,
        ok=not problems,
        error="; ".join(problems),
        actual=out.rstrip(),
    )


def run_code(
    code: str,
    checks: list[Check] | None = None,
    stdin: str = "",
    timeout: float = DEFAULT_TIMEOUT,
    files: dict[str, str] | None = None,
    entrypoint: str = DEFAULT_ENTRYPOINT,
) -> RunResult:
    """Виконує код користувача. Якщо передані checks — проганяє й перевірки."""
    checks = list(checks or [])
    code_checks = [check for check in checks if check.code]
    stdout_checks = [check for check in checks if check.is_stdout]
    result = RunResult(ran_checks=bool(checks), stdin=stdin)

    # --- перевірки коду: один запуск, бо їм потрібен спільний стан функцій ---
    if code_checks:
        stdout, stderr, exit_code, timed_out, truncated = _run_process(
            _build_source(code, code_checks), stdin, timeout, files, entrypoint
        )
        result.timed_out = timed_out
        result.exit_code = exit_code
        result.stderr = stderr
        result.output_truncated = truncated

        parsed: list[CheckResult] = []
        clean_lines = []
        for line in stdout.splitlines():
            if line.startswith(MARKER):
                for item in json.loads(line[len(MARKER):]):
                    parsed.append(CheckResult(**item))
            else:
                clean_lines.append(line)
        result.stdout = "\n".join(clean_lines).rstrip()

        if timed_out or not parsed:
            # код не дійшов до перевірок: синтаксична помилка, виняток або цикл
            reason = (
                f"Код не завершився за {timeout:g} с"
                if timed_out
                else _crash_reason(stderr)
            )
            result.checks = [
                CheckResult(name=check.name, ok=False, error=reason)
                for check in code_checks
            ]
        else:
            result.checks = parsed
    else:
        # звичайний запуск (без перевірок) — просто показуємо вивід
        stdout, stderr, exit_code, timed_out, truncated = _run_process(
            code, stdin, timeout, files, entrypoint
        )
        result.stdout = stdout.rstrip()
        result.stderr = stderr
        result.exit_code = exit_code
        result.timed_out = timed_out
        result.output_truncated = truncated

    # --- перевірки виводу: кожна окремим запуском зі своїм вводом ---
    for check in stdout_checks:
        feed = check.stdin if check.stdin is not None else stdin
        out, err, exit_code, timed_out, truncated = _run_process(
            code, feed, timeout, files, entrypoint
        )
        result.output_truncated = result.output_truncated or truncated
        if timed_out:
            result.checks.append(
                CheckResult(name=check.name, ok=False,
                            error=f"Код не завершився за {timeout:g} с")
            )
            result.timed_out = True
            continue
        if exit_code != 0 and not out.strip():
            result.checks.append(
                CheckResult(name=check.name, ok=False,
                            error=_crash_reason(err), actual=out.rstrip())
            )
            continue
        result.checks.append(_evaluate_stdout(check, out))

    if code_checks and result.checks:
        # зберігаємо порядок перевірок таким, як він заданий у задачі
        order = {check.name: index for index, check in enumerate(checks)}
        result.checks.sort(key=lambda item: order.get(item.name, 99))

    return result


def run_task(
    task,
    code: str,
    checks: list[Check] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> RunResult:
    """Запускає код у контексті задачі: з її вводом, файлами й точкою входу.

    Саме цим має користуватись і застосунок, і тести: тоді неможливо забути
    передати допоміжні файли задачі (а це ламало б задачі з модулями).
    """
    return run_code(
        code,
        list(task.checks) if checks is None else checks,
        stdin=task.stdin,
        timeout=timeout,
        files=task.files,
        entrypoint=task.entrypoint,
    )


def _crash_reason(stderr: str) -> str:
    """Витягує з traceback останній рядок — саме він пояснює помилку."""
    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    if not lines:
        return "Код впав з помилкою"
    last = lines[-1]
    if lines[-1].startswith("File ") and len(lines) > 1:
        last = lines[-2]
    return f"Код впав з помилкою: {_short(last, 120)}"
