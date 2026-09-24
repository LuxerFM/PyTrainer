@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Перший запуск: створюю віртуальне оточення і встановлюю PySide6...
    python -m venv .venv || goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

".venv\Scripts\python.exe" main.py
goto :eof

:error
echo.
echo Не вдалося підготувати оточення.
echo Перевір, чи встановлено Python 3.11 або новіший і чи є інтернет.
pause
