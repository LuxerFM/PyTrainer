"""Тести редактора коду: відступи, розумний Enter і запуск із клавіатури.

Редактор — та частина інтерфейсу, з якою людина стикається щосекунди. Якщо
Tab раптом вставить 5 пробілів або Enter перестане зберігати відступ,
зламається саме те, заради чого тренажер існує. Тому тут перевіряються не
віджети, а поведінка: що саме опиниться в тексті після натискання клавіші.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEvent, Qt  # noqa: E402
from PySide6.QtGui import QFontMetricsF, QKeyEvent, QTextCursor  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from trainer.ui.editor import INDENT, CodeEditor  # noqa: E402
from trainer.ui.theme import Colors, apply_theme, scale, set_scale  # noqa: E402


class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)

    def setUp(self):
        self.editor = CodeEditor()
        self.addCleanup(self.editor.deleteLater)
        self.addCleanup(self._restore_theme)

    def _restore_theme(self) -> None:
        Colors.use("dark")
        set_scale(1.0)
        apply_theme(self.app)

    # ---------- допоміжне ----------

    def _press(self, key, modifiers=Qt.KeyboardModifier.NoModifier, text=""):
        event = QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)
        self.editor.keyPressEvent(event)

    def _select_all(self) -> None:
        self.editor.moveCursor(QTextCursor.MoveOperation.Start)
        self.editor.moveCursor(QTextCursor.MoveOperation.End,
                               QTextCursor.MoveMode.KeepAnchor)

    # ---------- Tab і Shift+Tab ----------

    def test_tab_inserts_four_spaces(self):
        self.editor.setPlainText("")
        self._press(Qt.Key.Key_Tab)
        self.assertEqual(self.editor.toPlainText(), INDENT)

    def test_tab_indents_every_selected_line(self):
        self.editor.setPlainText("a = 1\nb = 2")
        self._select_all()
        self._press(Qt.Key.Key_Tab)
        self.assertEqual(self.editor.toPlainText(), "    a = 1\n    b = 2")

    def test_tab_leaves_empty_lines_alone(self):
        self.editor.setPlainText("a = 1\n\nb = 2")
        self._select_all()
        self._press(Qt.Key.Key_Tab)
        self.assertEqual(self.editor.toPlainText(), "    a = 1\n\n    b = 2")

    def test_shift_tab_removes_the_indent(self):
        self.editor.setPlainText("    a = 1\n    b = 2")
        self._select_all()
        self._press(Qt.Key.Key_Backtab)
        self.assertEqual(self.editor.toPlainText(), "a = 1\nb = 2")

    def test_shift_tab_removes_a_shorter_indent_without_eating_code(self):
        """Якщо відступ менший за 4 пробіли — знімаємо рівно його."""
        self.editor.setPlainText("  a = 1")
        self._select_all()
        self._press(Qt.Key.Key_Backtab)
        self.assertEqual(self.editor.toPlainText(), "a = 1")

    def test_shift_tab_handles_tabs_and_untouched_lines(self):
        self.editor.setPlainText("\ta = 1\nb = 2")
        self._select_all()
        self._press(Qt.Key.Key_Backtab)
        self.assertEqual(self.editor.toPlainText(), "a = 1\nb = 2")

    # ---------- розумний Enter ----------

    def _end_of_line(self) -> None:
        self.editor.moveCursor(QTextCursor.MoveOperation.End)

    def test_enter_after_colon_adds_an_indent(self):
        self.editor.setPlainText("if x:")
        self._end_of_line()
        self._press(Qt.Key.Key_Return)
        self.assertEqual(self.editor.toPlainText(), "if x:\n    ")

    def test_enter_keeps_the_current_indent(self):
        self.editor.setPlainText("if x:\n    a = 1")
        self._end_of_line()
        self._press(Qt.Key.Key_Return)
        self.assertEqual(self.editor.toPlainText(), "if x:\n    a = 1\n    ")

    def test_enter_after_backslash_continues_the_line(self):
        self.editor.setPlainText("total = 1 + \\")
        self._end_of_line()
        self._press(Qt.Key.Key_Return)
        self.assertEqual(self.editor.toPlainText(), "total = 1 + \\\n    ")

    def test_enter_in_the_middle_of_a_line_splits_it(self):
        """Звичайний Enter посеред рядка не має нічого дописувати збоку."""
        self.editor.setPlainText("ab")
        self.editor.moveCursor(QTextCursor.MoveOperation.Start)
        self._press(Qt.Key.Key_Return)
        self.assertEqual(self.editor.toPlainText(), "\nab")

    # ---------- запуск із клавіатури ----------

    def test_ctrl_enter_asks_to_run(self):
        calls = []
        self.editor.run_requested.connect(lambda: calls.append(True))
        self._press(Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(calls, [True])

    def test_plain_enter_does_not_run(self):
        calls = []
        self.editor.run_requested.connect(lambda: calls.append(True))
        self.editor.setPlainText("a = 1")
        self._end_of_line()
        self._press(Qt.Key.Key_Return)
        self.assertEqual(calls, [])

    # ---------- смуга з номерами ----------

    def test_gutter_reserves_three_digits_even_for_a_tiny_file(self):
        """Ширина смуги не має сіпатись, поки в файлі менше тисячі рядків."""
        self.editor.setPlainText("a")
        narrow = self.editor.gutter_width()
        self.editor.setPlainText("\n".join(str(number) for number in range(150)))
        self.assertEqual(self.editor.gutter_width(), narrow)

    def test_gutter_grows_for_a_four_digit_file(self):
        self.editor.setPlainText("a")
        narrow = self.editor.gutter_width()
        self.editor.setPlainText("\n".join(str(number) for number in range(1200)))
        self.assertGreater(self.editor.gutter_width(), narrow)

    def test_gutter_paints_a_hundred_lines_without_crashing(self):
        """Смуга номерів малюється власним кодом — тому перевіряємо і його."""
        self.editor.setPlainText("\n".join(f"line {number}" for number in range(120)))
        self.editor.resize(600, 300)
        self.assertFalse(self.editor.grab().isNull())

    # ---------- тема й масштаб ----------

    def test_apply_theme_rebuilds_the_highlighter_and_font(self):
        before = self.editor._highlighter
        self.editor.apply_theme()
        self.assertIsNot(self.editor._highlighter, before)

        size = self.editor.font().pointSize()
        set_scale(1.5)
        self.editor.apply_theme()
        self.assertGreater(self.editor.font().pointSize(), size)

    def test_tab_stop_is_four_spaces(self):
        expected = QFontMetricsF(self.editor.font()).horizontalAdvance(" ") * 4
        self.assertAlmostEqual(self.editor.tabStopDistance(), expected, delta=0.5)


if __name__ == "__main__":
    unittest.main()
