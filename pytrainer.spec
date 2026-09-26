# -*- mode: python ; coding: utf-8 -*-
"""Специфікація PyInstaller: один файл PyTrainer.exe.

Збирати не напряму, а через скрипт, який ще й кладе поруч README та ярлики:

    .venv\\Scripts\\python.exe tools\\build_exe.py

Результат — `dist/PyTrainer.exe`. База з прогресом і копії лежать у службовій
теці системи (`%LOCALAPPDATA%\PyTrainer`), а `progress.json`, `Python-Roadmap.md`
і `pytrainer.ini` — поруч із .exe: `--onefile` розпаковує код у тимчасову теку,
яку прибирає після виходу, а SQLite у синхронізованій теці (OneDrive) псується
(див. `trainer/paths.py`).
"""

from pathlib import Path

ROOT = Path(SPECPATH).resolve()  # SPECPATH задає сам PyInstaller
ICON = ROOT / "assets" / "icon.ico"
ICON_PNG = ROOT / "assets" / "icon.png"

# Qt тягне за собою майже весь свій стек — і збірка «просто так» важить
# під сотню мегабайт. Тренажеру потрібні лише QtCore, QtGui та QtWidgets,
# тому зайві модулі викидаємо явно (перелік у README, у розділі про збірку).
QT_UNUSED = (
    "Qt3D",
    "QtBluetooth",
    "QtCharts",
    "QtDataVisualization",
    "QtDesigner",
    "QtHelp",
    "QtMultimedia",
    "QtNetworkAuth",
    "QtNfc",
    "QtOpenGL",
    "QtPdf",
    "QtPositioning",
    "QtQml",
    "QtQuick",
    "QtRemoteObjects",
    "QtScxml",
    "QtSensors",
    "QtSerialPort",
    "QtSql",
    "QtStateMachine",
    "QtTest",
    "QtTextToSpeech",
    "QtWebChannel",
    "QtWebEngine",
    "QtWebSockets",
    "QtXml",
)


# Модулі, які потрібні коду задач, але сам тренажер їх не імпортує.
# PyInstaller збирає лише те, що знайшов у коді тренажера, тому без цього
# списку `import csv` у розв'язку падав би в зібраному .exe — а .exe
# це саме те, чим користується той, кому тренажер дали.
USER_MODULES = [
    "asyncio",
    "collections",
    "csv",
    "datetime",
    "functools",
    "http",
    "inspect",
    "io",
    "itertools",
    "json",
    "math",
    "operator",
    "random",
    "re",
    "sqlite3",
    "sqlite3.dbapi2",
    "ssl",
    "statistics",
    "string",
    "textwrap",
    "threading",
    "time",
    "traceback",
    "typing",
    "urllib",
    "urllib.request",
    "uuid",
]


def keep(name: str) -> bool:
    """False для бібліотек і даних, які нашій програмі не потрібні."""
    # У PySide6 бібліотеки звуться Qt6Core.dll, Qt6WebEngineCore.dll — тобто
    # зайва шістка розриває порівняння зі списком вище. Тому спершу
    # позбуваємось «6» після «qt», і тільки потім шукаємо входження.
    lowered = name.replace("\\", "/").lower().replace("qt6", "qt")
    if any(part.lower() in lowered for part in QT_UNUSED):
        return False
    # Переклади Qt: застосунок повністю український, англійські .qm не потрібні.
    if "/translations/" in lowered and "qtbase_uk" not in lowered:
        return False
    return True


a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ICON_PNG), "assets")],
    hiddenimports=USER_MODULES,
    hookspath=[],
    runtime_hooks=[],
    # У зібраному .exe нічого з цього не використовується, а важить чимало.
    excludes=["tkinter", "unittest", "doctest", "pydoc", "setuptools", "pip", "lib2to3"],
    noarchive=False,
)
# PyInstaller 6 зберігає ці списки як звичайні list — фільтруємо напряму.
a.binaries = [entry for entry in a.binaries if keep(entry[0])]
a.datas = [entry for entry in a.datas if keep(entry[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PyTrainer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # це віконний застосунок, консоль не потрібна
    disable_windowed_traceback=False,
    icon=str(ICON) if ICON.exists() else None,
)
