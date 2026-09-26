"""Self-test: `PyTrainer.exe --self-test` — does code checking really work.

The window draws even when code execution is broken. That is exactly what
happened: in the built `.exe` `sys.executable` points at the trainer itself,
so every check launched a second PyTrainer window, the verdict never arrived,
and temp files never got cleaned up. No test run from code can see that — the
problem lives only in the built `.exe`. So CI no longer "just opens" the
`.exe` but asks it to run code and show a verdict.

Three things are checked, each of which would break on its own:

1. the correct solution passes **all** checks — both code checks and output
   checks (including "output exactly this", which on Windows depends on line
   endings);
2. the broken solution does **not** pass, and exactly the check that must;
3. `while True` is stopped by the timeout instead of hanging forever.

The steps do not depend on curriculum content: the solution lives right here
so the self-test never falls over a renamed task.
"""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..paths import app_folder, is_frozen
from .exec_runner import ensure_streams
from .runner import DEFAULT_TIMEOUT, RunResult, run_code

FLAG = "--self-test"
DEFAULT_REPORT = "selftest.json"

INPUT = "Світ\n"

#: Code with a function, input and output — i.e. all check kinds.
SCRIPT = """\
name = input()


def add(a, b):
    return a + b


print("Привіт,", name)
print(add(2, 3))
"""

#: The same code with a one-line bug: `-` instead of `+`.
BROKEN = SCRIPT.replace("return a + b", "return a - b")

#: The classic the trainer must defend against.
HANG = "while True:\n    pass\n"

SUM_CHECK = "функція add рахує суму"
GREETING_CHECK = "вітається з тим, кого ввели"
OUTPUT_CHECK = "виводить рівно два рядки"


def checks():
    """Self-test checks — the same kinds as in real tasks."""
    from curriculum.schema import code, stdout

    return [
        code(SUM_CHECK, "assert add(2, 3) == 5, add(2, 3)"),
        stdout(GREETING_CHECK, contains="Привіт, Світ", stdin=INPUT),
        stdout(OUTPUT_CHECK, equals="Привіт, Світ\n5", stdin=INPUT),
    ]


@dataclass
class SelfCheckStep:
    """One self-test step — what was checked and how it ended."""

    name: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class SelfCheckReport:
    """The whole self-test result."""

    frozen: bool = False
    steps: list[SelfCheckStep] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True only if there were steps at all and all of them passed."""
        return bool(self.steps) and all(step.ok for step in self.steps)

    @property
    def mode(self) -> str:
        """Where it runs from: the built `.exe` or plain Python."""
        return "exe" if self.frozen else "python"

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "python": platform.python_version(),
            "steps": [step.as_dict() for step in self.steps],
        }

    def as_text(self) -> str:
        where = "зібраний .exe" if self.frozen else "Python із коду"
        lines = [f"Самоперевірка PyTrainer ({where}, Python {platform.python_version()}):"]
        for step in self.steps:
            lines.append(f"  [{'ок' if step.ok else 'ПОМИЛКА'}] {step.name} — {step.detail}")
        lines.append("Підсумок: усе гаразд" if self.ok else "Підсумок: перевірка коду НЕ працює")
        return "\n".join(lines)


def _one_line(text: str, limit: int = 120) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _describe(result: RunResult) -> str:
    """Short verdict description — so the report shows what exactly happened."""
    parts = [f"перевірок пройдено {result.passed_count} з {len(result.checks)}"]
    if result.timed_out:
        parts.append("код не встиг завершитись")
    if result.advice:
        parts.append(_one_line(result.advice))
    elif result.stdout:
        parts.append("вивід: " + _one_line(result.stdout, 80))
    return "; ".join(parts)


def _correct(timeout: float) -> tuple[bool, str]:
    result = run_code(SCRIPT, checks(), stdin=INPUT, timeout=timeout)
    return result.all_passed, _describe(result)


def _broken(timeout: float) -> tuple[bool, str]:
    result = run_code(BROKEN, checks(), stdin=INPUT, timeout=timeout)
    ok = (
        not result.all_passed
        and result.passed_count == 1          # exactly the counting broke
        and result.first_failed_check == SUM_CHECK
    )
    return ok, _describe(result)


def _hang(timeout: float) -> tuple[bool, str]:
    result = run_code(HANG, timeout=timeout)
    return result.timed_out, _describe(result)


def run_self_check(timeout: float = DEFAULT_TIMEOUT, hang_timeout: float = 1.0) -> SelfCheckReport:
    """Runs all self-test steps.

    `hang_timeout` is smaller than the plain timeout: we deliberately run
    never-ending code, and waiting the full 5 seconds on it makes no sense.
    """
    report = SelfCheckReport(frozen=is_frozen())
    probes = (
        ("правильний розв'язок проходить перевірки", lambda: _correct(timeout)),
        ("зламаний розв'язок не проходить", lambda: _broken(timeout)),
        ("нескінченний цикл зупиняється таймаутом", lambda: _hang(hang_timeout)),
    )
    for name, probe in probes:
        try:
            ok, detail = probe()
        except BaseException as error:
            # A broken trainer itself is also a failed step, not a self-test
            # crash: otherwise CI would never show what exactly broke.
            ok, detail = False, f"{type(error).__name__}: {error}"
        report.steps.append(SelfCheckStep(name=name, ok=ok, detail=detail))
    return report


def report_path_from(argv: list[str], frozen: bool) -> Path | None:
    """Where to put the report: explicit command path, else — next to the .exe.

    The built `.exe` has no console, so nowhere to print the report.
    A bare call with no path puts it next to itself; a run from code creates
    nothing, since there is somewhere to print.
    """
    if FLAG not in argv:
        return None
    for item in argv[argv.index(FLAG) + 1:]:
        if not item.startswith("-"):
            return Path(item)
    return app_folder() / DEFAULT_REPORT if frozen else None


def _write_report(report: SelfCheckReport, target: Path | None) -> None:
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(report.as_dict(), handle, ensure_ascii=False, indent=2)


def _say(text: str) -> None:
    """Prints the report if there is anywhere: a windowed .exe may have no streams."""
    stream = getattr(sys, "stdout", None) or getattr(sys, "stderr", None)
    if stream is not None:
        print(text, file=stream)


def main(argv: list[str] | None = None) -> int:
    """Runs the self-test and returns 0 only if everything really works."""
    argv = list(sys.argv if argv is None else argv)
    ensure_streams()
    report = run_self_check()
    target = report_path_from(argv, report.frozen)
    _write_report(report, target)
    _say(report.as_text() + (f"\nЗвіт: {target}" if target else ""))
    return 0 if report.ok else 1


__all__ = ["FLAG", "SelfCheckReport", "SelfCheckStep", "main", "run_self_check"]
