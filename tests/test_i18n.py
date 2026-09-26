"""English localization: .qm translates, helpers persist, .ts is complete."""

import os
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QSettings
from PySide6.QtWidgets import QApplication

from trainer.ui.locale import current_language, install_language, set_language

ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "i18n" / "pytrainer_en.ts"


class I18nTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        install_language(self.app, "uk")  # other suites expect Ukrainian

    def test_qm_translates_known_strings(self):
        self.assertIsNotNone(install_language(self.app, "en"))
        self.assertEqual(QCoreApplication.translate("MainWindow", "Запустити"), "Run")
        self.assertEqual(QCoreApplication.translate("TaskPanel", "Довідка"), "Reference")
        self.assertEqual(QCoreApplication.translate("ReviewPage", "СЬОГОДНІ"), "TODAY")

    def test_uk_removes_translator(self):
        install_language(self.app, "en")
        self.assertIsNone(install_language(self.app, "uk"))
        self.assertEqual(QCoreApplication.translate("MainWindow", "Запустити"), "Запустити")

    def test_language_round_trips_through_settings(self):
        self.assertEqual(current_language(None), "uk")
        with tempfile.TemporaryDirectory() as folder:
            settings = QSettings(str(Path(folder) / "t.ini"), QSettings.Format.IniFormat)
            self.assertEqual(current_language(settings), "uk")
            set_language(settings, "en")
            self.assertEqual(current_language(settings), "en")
            settings.setValue("view/language", "garbage")
            self.assertEqual(current_language(settings), "uk")

    def test_ts_has_no_unfinished(self):
        doc = xml.dom.minidom.parse(str(TS_PATH))
        left = [m for m in doc.getElementsByTagName("message")
                if m.getElementsByTagName("translation")[0].getAttribute("type")]
        self.assertEqual(left, [])


if __name__ == "__main__":
    unittest.main()
