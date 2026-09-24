"""Запуск коду користувача в окремому процесі + перевірка прихованими тестами.

Чому окремий процес: якщо в коді буде `while True`, ми вб'ємо цей процес по
таймауту, і застосунок продовжить працювати. Якби ми виконували код у себе,
зависла б уся програма.

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


def _run_process(source: str, stdin: str, timeout: float) -> tuple[str, str, int, bool]:
    """Виконує код у тимчасовому файлі. Повертає (stdout, stderr, код, таймаут)."""
    with tempfile.TemporaryDirectory(prefix="pytrainer_") as workdir:
        path = os.path.join(workdir, "solution.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(source)

        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        try:
            process = subprocess.run(
                [sys.executable, "-X", "utf8", "-u", path],
                input=stdin,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=workdir,
                env=env,
            )
            return process.stdout, process.stderr, process.returncode, False
        except subprocess.TimeoutExpired as expired:
            stdout = expired.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", "replace")
            stderr = f"Код працював довше ніж {timeout:g} с і був зупинений.\n"
            return stdout, stderr, -1, True


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
) -> RunResult:
    """Виконує код користувача. Якщо передані checks — проганяє й перевірки."""
    checks = list(checks or [])
    code_checks = [check for check in checks if check.code]
    stdout_checks = [check for check in checks if check.is_stdout]
    result = RunResult(ran_checks=bool(checks), stdin=stdin)

    # --- перевірки коду: один запуск, бо їм потрібен спільний стан функцій ---
    if code_checks:
        stdout, stderr, exit_code, timed_out = _run_process(
            _build_source(code, code_checks), stdin, timeout
        )
        result.timed_out = timed_out
        result.exit_code = exit_code
        result.stderr = stderr
        result.stdout = stdout

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
        stdout, stderr, exit_code, timed_out = _run_process(code, stdin, timeout)
        result.stdout = stdout.rstrip()
        result.stderr = stderr
        result.exit_code = exit_code
        result.timed_out = timed_out

    # --- перевірки виводу: кожна окремим запуском зі своїм вводом ---
    for check in stdout_checks:
        feed = check.stdin if check.stdin is not None else stdin
        out, err, exit_code, timed_out = _run_process(code, feed, timeout)
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


def _crash_reason(stderr: str) -> str:
    """Витягує з traceback останній рядок — саме він пояснює помилку."""
    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    if not lines:
        return "Код впав з помилкою"
    last = lines[-1]
    if lines[-1].startswith("File ") and len(lines) > 1:
        last = lines[-2]
    return f"Код впав з помилкою: {_short(last, 120)}"
