"""Самоперевірка: `PyTrainer.exe --self-test` — чи справді працює перевірка коду.

Вікно малюється навіть тоді, коли виконання коду зламане. Саме так і сталося:
у зібраному `.exe` `sys.executable` вказує на сам тренажер, тому кожна
перевірка запускала друге вікно PyTrainer, вердикт не приходив ніколи, а
тимчасові файли ще й не прибирались. Жоден тест з коду такого не побачить —
проблема живе лише в зібраному `.exe`. Тому CI більше не «просто відкриває»
`.exe`, а просить його виконати код і показати вердикт.

Перевіряються три речі, кожна з яких ламалась би окремо:

1. правильний розв'язок проходить **усі** перевірки — і перевірки коду,
   і перевірки виводу (серед них «вивід рівно такий», яка на Windows
   залежить від переводу рядків);
2. зламаний розв'язок **не** проходить, і саме та перевірка, яка мусить;
3. `while True` зупиняється таймаутом, а не висить вічно.

Кроки не залежать від змісту навчальної програми: розв'язок узятий тут же,
щоб самоперевірка не падала через перейменовану задачу.
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

#: Код, у якому є і функція, і ввід, і вивід — тобто всі види перевірок.
SCRIPT = """\
name = input()


def add(a, b):
    return a + b


print("Привіт,", name)
print(add(2, 3))
"""

#: Той самий код із помилкою в одному рядку: `-` замість `+`.
BROKEN = SCRIPT.replace("return a + b", "return a - b")

#: Класика, від якої тренажер мусить захищатись.
HANG = "while True:\n    pass\n"

SUM_CHECK = "функція add рахує суму"
GREETING_CHECK = "вітається з тим, кого ввели"
OUTPUT_CHECK = "виводить рівно два рядки"


def checks():
    """Перевірки для самоперевірки — ті самі види, що й у справжніх задачах."""
    from curriculum.schema import code, stdout

    return [
        code(SUM_CHECK, "assert add(2, 3) == 5, add(2, 3)"),
        stdout(GREETING_CHECK, contains="Привіт, Світ", stdin=INPUT),
        stdout(OUTPUT_CHECK, equals="Привіт, Світ\n5", stdin=INPUT),
    ]


@dataclass
class SelfCheckStep:
    """Один крок самоперевірки — що перевіряли і чим це скінчилось."""

    name: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class SelfCheckReport:
    """Результат самоперевірки цілком."""

    frozen: bool = False
    steps: list[SelfCheckStep] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True, лише якщо кроки взагалі були і всі вони пройшли."""
        return bool(self.steps) and all(step.ok for step in self.steps)

    @property
    def mode(self) -> str:
        """Звідки запущено: зібраний `.exe` чи звичайний Python."""
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
    """Короткий опис вердикту — щоб у звіті було видно, що саме сталося."""
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
        and result.passed_count == 1          # зламався саме підрахунок
        and result.first_failed_check == SUM_CHECK
    )
    return ok, _describe(result)


def _hang(timeout: float) -> tuple[bool, str]:
    result = run_code(HANG, timeout=timeout)
    return result.timed_out, _describe(result)


def run_self_check(timeout: float = DEFAULT_TIMEOUT, hang_timeout: float = 1.0) -> SelfCheckReport:
    """Виконує всі кроки самоперевірки.

    `hang_timeout` менший за звичайний таймаут: ми навмисне запускаємо код,
    який не завершується, і чекати на нього повні 5 секунд немає сенсу.
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
            # Поломка самого тренажера — це теж невдалий крок, а не падіння
            # самоперевірки: інакше в CI не було б видно, що саме зламалось.
            ok, detail = False, f"{type(error).__name__}: {error}"
        report.steps.append(SelfCheckStep(name=name, ok=ok, detail=detail))
    return report


def report_path_from(argv: list[str], frozen: bool) -> Path | None:
    """Куди покласти звіт: явний шлях із команди, інакше — поруч із .exe.

    У зібраного `.exe` немає консолі, тож надрукувати звіт йому нікуди.
    Порожній виклик без шляху кладе його поруч із собою; запуск із коду
    нічого не створює, бо там є куди друкувати.
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
    """Друкує звіт, якщо є куди: у віконного .exe потоків може не бути."""
    stream = getattr(sys, "stdout", None) or getattr(sys, "stderr", None)
    if stream is not None:
        print(text, file=stream)


def main(argv: list[str] | None = None) -> int:
    """Запускає самоперевірку й повертає 0, лише якщо все справді працює."""
    argv = list(sys.argv if argv is None else argv)
    ensure_streams()
    report = run_self_check()
    target = report_path_from(argv, report.frozen)
    _write_report(report, target)
    _say(report.as_text() + (f"\nЗвіт: {target}" if target else ""))
    return 0 if report.ok else 1


__all__ = ["FLAG", "SelfCheckReport", "SelfCheckStep", "main", "run_self_check"]
