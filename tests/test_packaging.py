"""Тести збірки й шляхів: те, що ламається лише в .exe і лише в CI.

Тут перевіряються три речі, які очима не побачиш:

1. `trainer/paths.py` справді перемикається на теку .exe, коли програму
   зібрано — інакше прогрес зникав би після кожного закриття вікна;
2. `pytrainer.spec` викидає зайві модулі Qt (і не викидає потрібні) —
   помилка тут не ламає тести, а ламає готовий .exe;
3. картинки, на які посилається README, існують, а всі знімки, які вміє
   робити `tools/make_screenshots.py`, у README показані.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from curriculum import all_tasks, study_tasks  # noqa: E402
from trainer import paths  # noqa: E402


def load_spec() -> dict:
    """Виконує pytrainer.spec із заглушками PyInstaller — як це робить сам PyInstaller.

    Сама збірка тут не потрібна: перевіряємо логіку фільтра, а не компіляцію.
    """
    seen: dict = {}

    def analysis(scripts, **kwargs):
        seen["scripts"] = scripts
        seen["kwargs"] = kwargs
        # Кілька реальних імен, які PyInstaller знаходить у збірці PySide6.
        return mock.Mock(
            pure=[],
            scripts=scripts,
            datas=[("assets/icon.png", "x", "DATA")],
            binaries=[
                ("PySide6/Qt6Core.dll", "x", "BINARY"),
                ("PySide6/Qt6Gui.dll", "x", "BINARY"),
                ("PySide6/Qt6Widgets.dll", "x", "BINARY"),
                ("PySide6/Qt6Network.dll", "x", "BINARY"),
                ("PySide6/Qt6WebEngineCore.dll", "x", "BINARY"),
                ("PySide6/Qt6Sql.dll", "x", "BINARY"),
                ("PySide6/QtWebEngineWidgets.pyd", "x", "EXTENSION"),
                ("PySide6/translations/qtbase_uk.qm", "y", "DATA"),
                ("PySide6/translations/qtbase_en.qm", "y", "DATA"),
            ],
        )

    namespace = {
        "SPECPATH": str(ROOT),
        "Analysis": analysis,
        "PYZ": lambda *args, **kwargs: None,
        "EXE": lambda *args, **kwargs: None,
    }
    source = (ROOT / "pytrainer.spec").read_text(encoding="utf-8")
    exec(compile(source, "pytrainer.spec", "exec"), namespace)
    namespace["_seen"] = seen
    return namespace


class PathsTest(unittest.TestCase):
    def test_normal_run_uses_project_root(self) -> None:
        self.assertFalse(paths.is_frozen())
        self.assertEqual(paths.app_folder(), ROOT)
        self.assertEqual(paths.resource("assets", "icon.png"), ROOT / "assets" / "icon.png")

    def test_frozen_run_uses_folder_with_exe(self) -> None:
        exe = ROOT / "dist" / "PyTrainer.exe"
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "executable", str(exe)):
            self.assertTrue(paths.is_frozen())
            # Найважливіше в усьому файлі: НЕ тека розпакування, а тека .exe.
            self.assertEqual(paths.app_folder(), exe.parent)

    def test_frozen_resources_come_from_unpack_folder(self) -> None:
        unpack = ROOT / "build" / "_meipass"
        with mock.patch.object(sys, "_MEIPASS", str(unpack), create=True):
            self.assertEqual(paths.resource("assets", "icon.png"), unpack / "assets" / "icon.png")


def imported_modules(sources: list[str]) -> set[str]:
    """Верхні імена модулів, які імпортує код (sqlite3.dbapi2 → sqlite3)."""
    found: set[str] = set()
    for source in sources:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue      # заготовка може бути неповною — це не привід падати
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def task_sources() -> list[str]:
    """Увесь код, який виконується в .exe: заготовки, перевірки, розв'язки, файли."""
    sources: list[str] = []
    for item in all_tasks():
        sources.append(item.starter)
        sources.extend(check.code for check in item.checks if check.code)
        if item.solution_hint is not None:
            sources.append(item.solution_hint.text)
        sources.extend(item.files.values())
    return sources


def trainer_sources() -> list[str]:
    """Код тренажера — саме його читає PyInstaller, коли вирішує, що брати."""
    files = [*ROOT.glob("trainer/**/*.py"), ROOT / "main.py"]
    return [path.read_text(encoding="utf-8") for path in files if path.is_file()]


class BundledModulesTest(unittest.TestCase):
    """Імпорти коду задач мусять існувати всередині зібраного .exe.

    PyInstaller кладе в архів лише те, що знайшов у коді тренажера. Тому
    `import csv` у розв'язку працює із коду й падає **тільки** в .exe — а
    .exe це саме те, чим користується той, кому тренажер дали. Тут ми беремо
    імпорти справжніх задач і звіряємо їх зі списком `USER_MODULES` у
    специфікації: додав задачу з новим модулем — тест скаже, що дописати.
    """

    def setUp(self) -> None:
        self.namespace = load_spec()

    def test_every_import_of_every_task_is_bundled(self) -> None:
        bundled = imported_modules(trainer_sources())
        bundled.update(name.split(".")[0] for name in self.namespace["USER_MODULES"])
        # Файли, які задача приносить із собою (utils.py, fake_api.py), лягають
        # у тимчасову папку поруч із розв'язком — у збірку їх брати не треба.
        bundled.update(Path(name).stem for item in all_tasks() for name in item.files)
        missing = imported_modules(task_sources()) - bundled
        self.assertEqual(
            sorted(missing), [],
            "ці модулі потрібні коду задач, а в .exe їх не буде: "
            "додай їх до USER_MODULES у pytrainer.spec",
        )


class SpecTest(unittest.TestCase):
    def setUp(self) -> None:
        self.namespace = load_spec()
        self.keep = self.namespace["keep"]

    def test_keeps_qt_modules_the_app_uses(self) -> None:
        for name in ("PySide6/Qt6Core.dll", "PySide6/Qt6Gui.dll",
                     "PySide6/Qt6Widgets.dll", "PySide6/Qt6Network.dll"):
            self.assertTrue(self.keep(name), f"{name} потрібен застосунку")

    def test_drops_unused_qt_modules(self) -> None:
        # Саме через «6» у назві цей фільтр колись не працював.
        for name in ("PySide6/Qt6WebEngineCore.dll", "PySide6/Qt6Sql.dll",
                     "PySide6/Qt3DCore.dll", "PySide6/QtWebEngineWidgets.pyd",
                     "PySide6/Qt6Multimedia.dll"):
            self.assertFalse(self.keep(name), f"{name} не потрібен застосунку")

    def test_drops_non_ukrainian_translations(self) -> None:
        self.assertTrue(self.keep("PySide6/translations/qtbase_uk.qm"))
        self.assertFalse(self.keep("PySide6/translations/qtbase_en.qm"))

    def test_keeps_own_files(self) -> None:
        self.assertTrue(self.keep("assets/icon.png"))
        self.assertTrue(self.keep("curriculum/month1.py"))

    def test_excludes_heavy_stdlib_packages(self) -> None:
        self.assertIn("tkinter", self.namespace["_seen"]["kwargs"]["excludes"])


def load_build_script():
    """Завантажує `tools/build_exe.py` як модуль, не запускаючи його."""
    spec = importlib.util.spec_from_file_location("build_exe", ROOT / "tools" / "build_exe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildScriptTest(unittest.TestCase):
    """Збірка сама себе перевіряє: .exe мусить уміти виконати код.

    Це єдина перевірка, яка справді ловить зламане виконання коду в `.exe`:
    вікно відкривається і тоді, коли розв'язок не запускається.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.build = load_build_script()

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory(prefix="pytrainer_build_")
        self.addCleanup(self.folder.cleanup)
        self.exe = Path(self.folder.name) / "PyTrainer.exe"
        self.report = self.exe.parent / "selftest.json"

    def run_exe_with(self, returncode: int):
        return mock.patch.object(
            self.build.subprocess, "run", return_value=mock.Mock(returncode=returncode)
        )

    def test_passing_report_means_a_good_build(self) -> None:
        self.report.write_text(
            json.dumps({"ok": True, "steps": [{"name": "крок", "ok": True, "detail": ""}]}),
            encoding="utf-8",
        )
        with self.run_exe_with(0):
            self.assertTrue(self.build.check_self_test(self.exe))

    def test_non_zero_exit_code_fails_the_build(self) -> None:
        with self.run_exe_with(1):
            self.assertFalse(self.build.check_self_test(self.exe))

    def test_unreadable_report_is_not_a_pass(self) -> None:
        """Немає звіту — немає й доказу, що код виконується."""
        with self.run_exe_with(0):
            self.assertFalse(self.build.check_self_test(self.exe))
        self.report.write_text("не json", encoding="utf-8")
        with self.run_exe_with(0):
            self.assertFalse(self.build.check_self_test(self.exe))

    def test_failed_step_fails_the_build_even_with_code_zero(self) -> None:
        self.report.write_text(
            json.dumps({"ok": False, "steps": [
                {"name": "крок", "ok": False, "detail": "не так"},
            ]}),
            encoding="utf-8",
        )
        with self.run_exe_with(0):
            self.assertFalse(self.build.check_self_test(self.exe))


class DocsTest(unittest.TestCase):
    def test_readme_states_the_real_test_count(self) -> None:
        """README обіцяє число тестів — воно не має розходитись із правдою.

        Інакше через місяць у README стоїть «219 тестів», а в проєкті
        давно двісті тридцять: дрібниця, але саме з таких дрібниць README
        і перестає бути правдою.
        """
        total = unittest.defaultTestLoader.discover(str(ROOT / "tests")).countTestCases()
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        form = "test" if total == 1 else "tests"
        self.assertIn(
            f"{total} {form}", readme,
            f"README has no mention of '{total} {form}' — update the numbers",
        )

    def test_readme_states_the_real_task_count(self) -> None:
        """Task count in README is a promise too — it must stay true."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        total, ready = len(all_tasks()), len(study_tasks())
        self.assertIn(f"{total} tasks", readme,
                      f"README has no mention of '{total} tasks' — update the numbers")
        self.assertIn(f"{ready} ready to solve", readme,
                      f"README has no mention of '{ready} ready to solve'")

    def test_readme_images_exist(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        references = set(re.findall(r"docs/images/[\w.-]+\.png", readme))
        self.assertTrue(references, "README не показує жодного знімка")
        for reference in sorted(references):
            self.assertTrue((ROOT / reference).exists(), f"немає файла {reference}")

    def test_every_screenshot_is_shown_in_readme(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        script = (ROOT / "tools" / "make_screenshots.py").read_text(encoding="utf-8")
        shots = set(re.findall(r'^\s{8}"(\d\d-[\w-]+)"', script, flags=re.MULTILINE))
        self.assertTrue(shots, "не знайдено жодного знімка у tools/make_screenshots.py")
        for shot in sorted(shots):
            self.assertIn(
                f"docs/images/{shot}.png", readme,
                f"знімок {shot}.png робиться, але в README його не видно",
            )


if __name__ == "__main__":
    unittest.main()
