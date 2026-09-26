"""Збирає PyTrainer.exe (Windows/Linux) і готує теку для роздачі.

    .venv\\Scripts\\python.exe tools\\build_exe.py

Що робить:
1. перевіряє, що PyInstaller стоїть (і підказує, як поставити);
2. малює іконки, якщо їх немає (assets/icon.png, assets/icon.ico);
3. збирає один файл `dist/PyTrainer.exe` за `pytrainer.spec`;
4. кладе поруч README, LICENSE і коротку інструкцію — щоб людині, яка
   завантажила архів, не треба було нічого добудовувати;
5. просить зібраний .exe виконати код і показати вердикт — якщо він цього не
   вміє, збірка вважається невдалою (`--no-check` вимикає цю перевірку).

З прапорцем `--install` той самий .exe копіюється ще й у корінь проєкту —
тобто туди, де вже лежить прогрес. Для себе самого це найзручніший варіант:
і запуск із коду, і запуск .exe бачать одну базу. Ярлик на це .exe робить
`tools/make_shortcut.py`.

Прогрес користувача застосунок створює сам — поруч із .exe
(див. trainer/paths.py).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXE_NAME = "PyTrainer.exe" if sys.platform == "win32" else "PyTrainer"

HOWTO = """PyTrainer — тренажер Python
================================

1. Запусти PyTrainer{ext} (подвійний клік).
2. Прогрес (pytrainer.db) лежить у службовій теці системи, а не в цій:
   Windows — %LOCALAPPDATA%\PyTrainer, інші системи —
   ~/.local/share/PyTrainer. Відкрити її можна з меню «Файл → Відкрити
   теку з даними», а поруч із .exe лишаються progress.json,
   Python-Roadmap.md і pytrainer.ini (налаштування).
3. Щоб перенести прогрес на інший комп'ютер, скопіюй теку даних цілком,
   скористайся «Файл → Експортувати прогрес» або запусти з прапорцем
   --data-dir ТЕКА — тоді все ляже в одну теку, яку можна носити з собою.

Інтернет не потрібен, права адміністратора — теж.
""".format(ext=".exe" if sys.platform == "win32" else "")


def ensure_icons() -> None:
    png = ROOT / "assets" / "icon.png"
    ico = ROOT / "assets" / "icon.ico"
    if png.exists() and ico.exists():
        return
    print("Іконок немає — малюю…")
    subprocess.run([sys.executable, str(ROOT / "tools" / "make_icon.py")], check=True)


def check_self_test(exe: Path) -> bool:
    """Просить .exe виконати код і показати вердикт — головна перевірка збірки.

    Вікно відкривається навіть тоді, коли запуск коду в зібраному .exe зламаний:
    саме так і сталося одного разу, коли `sys.executable` у `.exe` — це сам
    тренажер. Тому збірка сама себе перевіряє не «чи малюється вікно», а «чи
    приходить вердикт» (див. `trainer/core/selfcheck.py`).
    """
    report = exe.parent / "selftest.json"
    print()
    print("Перевіряю, що .exe виконує код і перевірки…")
    result = subprocess.run([str(exe), "--self-test", str(report)], check=False)

    text = ""
    try:
        text = report.read_text(encoding="utf-8")
        steps = json.loads(text).get("steps", [])
    except (OSError, ValueError):
        steps = []
    for step in steps:
        mark = "ок" if step.get("ok") else "ПОМИЛКА"
        print(f"  [{mark}] {step.get('name')} — {step.get('detail')}")
    # Порожній або нечитабельний звіт — це не «все гаразд», а «нічого не
    # перевірили»: саме тому тут потрібні і код виходу, і самі кроки.
    return result.returncode == 0 and bool(steps) and all(step.get("ok") for step in steps)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Зібрати PyTrainer.exe")
    parser.add_argument(
        "--install", action="store_true",
        help="покласти .exe поруч із проєктом (туди, де лежить прогрес)",
    )
    parser.add_argument(
        "--no-check", action="store_true",
        help="не перевіряти зібраний .exe самоперевіркою (вона запускає його 7 разів)",
    )
    args = parser.parse_args(argv)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "PyInstaller не встановлено.\n"
            "Постав його так:\n"
            f"    {sys.executable} -m pip install -r requirements-dev.txt"
        )
        return 1

    ensure_icons()

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(ROOT / "pytrainer.spec"),
        "--noconfirm",
        "--clean",
        "--workpath",
        str(ROOT / "build"),
        "--distpath",
        str(DIST),
    ]
    print("Збираю:", " ".join(command[2:]))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        return result.returncode

    built = DIST / EXE_NAME
    if not built.exists():
        print(f"Збірка завершилась, але {built} не знайдено")
        return 1

    for name in ("README.md", "LICENSE"):
        source = ROOT / name
        if source.exists():
            shutil.copy2(source, DIST / name)
    (DIST / ("ЯК_ЗАПУСКАТИ.txt" if sys.platform == "win32" else "HOW_TO_RUN.txt")).write_text(
        HOWTO, encoding="utf-8"
    )

    if not args.no_check and not check_self_test(built):
        print()
        print("Самоперевірка не пройшла: .exe зібрано, але код у ньому не виконується.")
        print("Вікно при цьому відкривається — тому й перевіряємо вердикт, а не вікно.")
        return 1

    print()
    print(f"Готово: {built} ({built.stat().st_size / 1_048_576:.1f} МБ)")
    print(f"Роздавати можна всю теку: {DIST}")

    if args.install:
        installed = ROOT / EXE_NAME
        shutil.copy2(built, installed)
        print()
        print(f"Встановлено поруч із проєктом: {installed}")
        print("База знайома та сама, що й у запуску з коду — прогрес не подвоюється.")
        sys.path.insert(0, str(ROOT))
        from trainer.paths import data_folder      # noqa: PLC0415

        print(f"Дані (база, копії, замок): {data_folder()}")
        print(f"Ярлик на робочий стіл: {sys.executable} tools/make_shortcut.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
