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
import os as _os
import traceback as _traceback

_results = []


def _check(_name, _source):
    try:
        exec(compile(_source, "<тест>", "exec"), globals())
    except BaseException as _error:            # ловимо все, навіть assert
        _results.append({"name": _name, "ok": False,
                         "error": "%s: %s" % (type(_error).__name__, _error),
                         "line": _user_line(_error)})
    else:
        _results.append({"name": _name, "ok": True, "error": "", "line": 0})


_HARNESS_LINE = _check.__code__.co_firstlineno


def _user_line(_error):
    """Номер рядка у файлі користувача, де стався виняток (0 — невідомо).

    Твій код і службовий харнес лежать в одному файлі, тому кадри стека
    мають однакове ім'я. Розрізняємо їх двома ознаками: кадр мусить бути
    вище рядка, з якого починається харнес, і належати тому самому файлу
    (кадри перевірок живуть у файлі "<тест>" і не рахуються).
    """
    try:
        _frames = _traceback.extract_tb(_error.__traceback__)
    except Exception:
        return 0

    _own = globals().get("__file__", "")
    _own_name = _os.path.basename(_own) if _own else ""

    for _frame in reversed(_frames):
        if not _frame.line or _frame.lineno >= _HARNESS_LINE:
            continue
        if _own_name and _os.path.basename(_frame.filename) != _own_name:
            continue
        return _frame.lineno
    return 0
'''


@dataclass
class CheckResult:
    """Результат однієї прихованої перевірки."""

    name: str
    ok: bool
    error: str = ""
    actual: str = ""
    line: int = 0        # рядок у коді користувача, де стався виняток


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
    def first_failed_check(self) -> str:
        """Назва першої перевірки, яка не пройшла (порожньо, якщо все гаразд)."""
        for check in self.checks:
            if not check.ok:
                return check.name
        return ""

    @property
    def failed_line(self) -> int:
        """Рядок у коді користувача, який треба показати (0 — невідомо).

        Спершу дивимось, що нам сказала перевірка (вона бачила справжній
        стек), і лише потім — текст помилки всього запуску.
        """
        for check in self.checks:
            if not check.ok and check.line:
                return check.line
        from .errors import analyse

        found = analyse(self.stderr)
        if found is not None and found.line:
            return found.line
        return 0

    @property
    def failure_kind(self) -> str:
        """Тип помилки для журналу: NameError, AssertionError…

        Порожньо, якщо це просто неправильний вивід ("у виводі немає…") —
        тоді писати в журнал нема чого, бо це не помилка Python.
        """
        if self.all_passed:
            return ""
        if self.timed_out:
            return "TimeoutError"
        from .errors import analyse_short

        for text in (self.stderr, self.first_error):
            if not text.strip():
                continue
            found = analyse_short(text.splitlines()[-1])
            if found is not None:
                return found.kind
        return ""

    @property
    def crashed(self) -> bool:
        return self.exit_code != 0 and not self.timed_out

    @property
    def advice(self) -> str:
        """Людське пояснення помилки — те, що показуємо в панелі «Тести».

        Порожньо, якщо помилки не було або ми не змогли її розпізнати.
        """
        if self.all_passed:
            return ""
        if self.timed_out:
            return (
                "Код працював занадто довго і був зупинений. Найчастіша "
                "причина — цикл while, умова якого ніколи не стає хибною.\n"
                "Що робити: перевір, чи змінна в умові справді змінюється "
                "всередині циклу, і чи є вихід через break."
            )
        from .errors import analyse_short, explain

        if self.stderr.strip():
            text = explain(self.stderr)
            if text:
                return text

        # Виняток усередині прихованої перевірки не доходить до stderr: харнес
        # ловить його й зберігає одним рядком у результатах перевірок. Саме це й
        # найчастіший випадок у новачка, тому пояснюємо і його.
        short = analyse_short(self.first_error)
        return short.as_text() if short else ""


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
    # Windows переводить \n у \r\n, коли програма пише у файл (а ми саме так і
    # ловимо вивід). Без цього нормалізування перевірка «вивід рівно такий»
    # проходила б на Linux і падала б лише на Windows.
    out = out.replace("\r\n", "\n")
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
