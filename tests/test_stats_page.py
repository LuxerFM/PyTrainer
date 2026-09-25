"""Тести намальованих віджетів статистики: календаря активності й графіка XP.

Ці два віджети малюються вручну (`paintEvent`), тому їх не перевірить жоден
пошук по віджетах: якщо в коді малювання станеться помилка, застосунок
упаде лише тоді, коли користувач загляне у «Прогрес». Тут ми змушуємо їх
намалюватись без екрана й перевіряємо те, що видно оком: колір клітинки
залежить від кількості спроб, а порожній графік не малює підпису.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from trainer.ui.stats_page import ActivityGrid, XpChart  # noqa: E402
from trainer.ui.theme import Colors, apply_theme, set_scale  # noqa: E402


class ActivityGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)

    def setUp(self):
        self.calendar = ActivityGrid()
        self.addCleanup(self.calendar.deleteLater)
        self.addCleanup(lambda: (Colors.use("dark"), set_scale(1.0), apply_theme(self.app)))

    def test_cell_colour_grows_with_activity(self):
        """Чотири щаблі: порожньо, трохи, нормально, багато.

        Саме чотири, а не п'ять: клітинка не мусить мати відтінок для
        кожної кількості спроб — важливо лише, щоб їх було видно оком.
        """
        colour = lambda count: self.calendar._cell_color(count).name().lower()
        self.assertEqual(colour(0), Colors.elevated.lower())
        self.assertEqual(colour(1), Colors.selection.lower())
        self.assertEqual(colour(3), "#3f74c9")
        self.assertEqual(colour(6), Colors.accent.lower())
        self.assertEqual(colour(12), Colors.accent.lower())
        self.assertEqual(
            len({colour(count) for count in (0, 1, 3, 6)}), 4,
            "щаблі діяльності мають відрізнятись",
        )

    def test_empty_day_is_painted_with_the_quiet_colour(self):
        self.assertEqual(
            self.calendar._cell_color(0).name().lower(), Colors.elevated.lower()
        )

    def test_calendar_paints_with_and_without_activity(self):
        self.calendar.resize(160, 90)
        self.assertFalse(self.calendar.grab().isNull())

        today = date.today()
        activity = {
            (today - timedelta(days=offset)).isoformat(): offset % 5
            for offset in range(40)
        }
        activity[today.isoformat()] = 9
        self.calendar.set_activity(activity)
        self.assertFalse(self.calendar.grab().isNull())


class XpChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)

    def setUp(self):
        self.chart = XpChart()
        self.addCleanup(self.chart.deleteLater)

    def test_days_cover_the_whole_window(self):
        days = self.chart._days()
        self.assertEqual(len(days), XpChart.DAYS)
        self.assertEqual(days[-1][0], date.today().isoformat())

    def test_empty_chart_paints_without_a_caption(self):
        self.chart.resize(200, 64)
        self.assertFalse(self.chart.grab().isNull())
        self.assertEqual(max(value for _, value in self.chart._days()), 0)

    def test_chart_paints_bars_for_a_quiet_and_a_busy_day(self):
        today = date.today()
        self.chart.set_data({
            today.isoformat(): 200,                                   # пік
            (today - timedelta(days=1)).isoformat(): 20,              # тихий день
            (today - timedelta(days=2)).isoformat(): 120,             # середній
        })
        self.chart.resize(220, 64)
        self.assertFalse(self.chart.grab().isNull())

        values = dict(self.chart._days())
        self.assertEqual(values[today.isoformat()], 200)
        self.assertEqual(values[(today - timedelta(days=1)).isoformat()], 20)


if __name__ == "__main__":
    unittest.main()
