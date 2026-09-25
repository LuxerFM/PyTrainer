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

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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


class DocsTest(unittest.TestCase):
    def test_readme_states_the_real_test_count(self) -> None:
        """README обіцяє число тестів — воно не має розходитись із правдою.

        Інакше через місяць у README стоїть «219 тестів», а в проєкті
        давно двісті тридцять: дрібниця, але саме з таких дрібниць README
        і перестає бути правдою.
        """
        total = unittest.defaultTestLoader.discover(str(ROOT / "tests")).countTestCases()
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            f"{total} тестів", readme,
            f"у README немає згадки «{total} тестів» — онови цифри",
        )

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
