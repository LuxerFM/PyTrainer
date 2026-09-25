"""Створює ярлик PyTrainer на робочому столі (Windows).

    .venv\\Scripts\\python.exe tools/make_shortcut.py

Навіщо окремий скрипт: ярлик — це файл із зашитим шляхом. Якщо перенести теку
з застосунком, ярлик «зламається», і відновити його треба однією командою, а
не згадуванням, як це робилось.

Що робить скрипт:
1. знаходить зібраний `.exe` (спершу поруч із проєктом, потім у `dist/`);
2. створює `PyTrainer.lnk` на робочому столі з тією ж іконкою, що в застосунку;
3. друкує шлях до ярлика — щоб було видно, де він лежить.

Важлива дрібниця: тека запуску ярлика — це тека `.exe`, тому прогрес
(`pytrainer.db`, `progress.json`, `Python-Roadmap.md`) лежить саме там і
подорожує разом із нею.
"""

from __future__ import annotations

import argparse
import base64
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "PyTrainer"


def find_exe(explicit: str | None = None) -> Path:
    """Знаходить зібраний .exe: явний шлях → корінь проєкту → dist/."""
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise SystemExit(f"Немає такого файла: {path}")
        return path.resolve()

    candidates = [
        ROOT / "PyTrainer.exe",
        ROOT / "dist" / "PyTrainer.exe",
        ROOT / "PyTrainer",
        ROOT / "dist" / "PyTrainer",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise SystemExit(
        "Зібраного застосунку не знайдено. Спершу збери його:\n"
        f"    {sys.executable} tools/build_exe.py"
    )


def make_shortcut(exe: Path, name: str = DEFAULT_NAME) -> Path:
    """Створює ярлик на робочому столі й повертає його шлях.

    Через PowerShell, а не через pywin32: це не додає ще одну залежність до
    проєкту, а WScript.Shell є в будь-якій Windows.
    """
    icon = ROOT / "assets" / "icon.ico"
    script = f"""
$ErrorActionPreference = 'Stop'
$desktop = [Environment]::GetFolderPath('Desktop')
if (-not $desktop) {{ throw 'Не вдалося знайти робочий стіл' }}
$link = Join-Path $desktop '{name}.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($link)
$shortcut.TargetPath = '{exe}'
$shortcut.WorkingDirectory = '{exe.parent}'
$shortcut.Description = 'PyTrainer — тренажер Python'
"""
    if icon.exists():
        script += f"$shortcut.IconLocation = '{icon}'\n"
    script += "$shortcut.Save()\nWrite-Output $link\n"

    # -EncodedCommand тримає українські літери живими незалежно від кодової
    # сторінки консолі Windows.
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive",
         "-EncodedCommand", encoded],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit(
            "PowerShell не зміг створити ярлик:\n"
            f"{result.stdout.strip()}\n{result.stderr.strip()}"
        )
    created = Path(result.stdout.strip().splitlines()[-1])
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ярлик PyTrainer на робочому столі")
    parser.add_argument("--exe", help="шлях до зібраного .exe (типово: знайти сам)")
    parser.add_argument("--name", default=DEFAULT_NAME, help="назва ярлика")
    args = parser.parse_args(argv)

    if sys.platform != "win32":
        print("Ярлики .lnk — це формат Windows. На цій системі створи .desktop-файл "
              "або запусти застосунок із терміналу.")
        return 0

    exe = find_exe(args.exe)
    link = make_shortcut(exe, args.name)
    print(f"Ярлик: {link}")
    print(f"Указує на: {exe}")
    print(f"Прогрес лежить поруч: {exe.parent}")
    print("Порада: правий клік по ярлику → «Закріпити на панелі завдань».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
