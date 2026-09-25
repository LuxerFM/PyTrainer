"""Тести теми: обидві палітри, масштаб шрифту і таблиця стилів.

Найважливіше тут — test_palettes_have_the_same_keys: якщо додати колір лише
в темну палітру, світла тема впаде з AttributeError у випадковому місці
інтерфейсу. Цей тест ловить таку помилку одразу.
"""

import unittest

from trainer.ui import theme


class PaletteTests(unittest.TestCase):
    def test_palettes_have_the_same_keys(self):
        dark = {key for key in vars(theme.DarkPalette) if not key.startswith("_")}
        light = {key for key in vars(theme.LightPalette) if not key.startswith("_")}
        self.assertEqual(dark - light, set(), "ці кольори є лише в темній темі")
        self.assertEqual(light - dark, set(), "ці кольори є лише в світлій темі")

    def test_every_colour_is_a_hex_value(self):
        for palette in (theme.DarkPalette, theme.LightPalette):
            for key, value in vars(palette).items():
                if key.startswith("_"):
                    continue
                with self.subTest(palette=palette.__name__, key=key):
                    self.assertRegex(value, r"^#[0-9a-f]{6}$")

    def test_palette_vars_follows_the_active_theme(self):
        try:
            theme.Colors.use("light")
            self.assertEqual(theme.Colors.name, "light")
            self.assertEqual(theme.palette_vars()["bg"], theme.LightPalette.bg)
            theme.Colors.use("dark")
            self.assertEqual(theme.Colors.name, "dark")
            self.assertEqual(theme.palette_vars()["bg"], theme.DarkPalette.bg)
        finally:
            theme.Colors.use("dark")

    def test_unknown_theme_falls_back_to_dark(self):
        try:
            theme.Colors.use("рожева")
            self.assertEqual(theme.Colors.name, "dark")
        finally:
            theme.Colors.use("dark")


class ScaleTests(unittest.TestCase):
    def tearDown(self):
        theme.set_scale(1.0)

    def test_scale_is_limited_from_both_sides(self):
        self.assertEqual(theme.set_scale(9.0), theme.MAX_SCALE)
        self.assertEqual(theme.set_scale(0.1), theme.MIN_SCALE)

    def test_ui_size_follows_the_scale(self):
        theme.set_scale(1.0)
        self.assertEqual(theme.ui_size(14), 14)
        theme.set_scale(1.5)
        self.assertEqual(theme.ui_size(14), 21)

    def test_ui_size_never_goes_below_readable(self):
        theme.set_scale(theme.MIN_SCALE)
        self.assertGreaterEqual(theme.ui_size(9), 8)

    def test_scaled_qss_multiplies_font_sizes(self):
        theme.set_scale(1.0)
        plain = theme.scaled_qss("QLabel { font-size: 12px; padding: 4px; }")
        self.assertIn("font-size: 12px", plain)

        theme.set_scale(1.5)
        bigger = theme.scaled_qss("QLabel { font-size: 12px; padding: 4px; }")
        self.assertIn("font-size: 18px", bigger)
        self.assertIn("padding: 4px", bigger, "відступи не мають масштабуватись")


class QssTests(unittest.TestCase):
    def test_template_has_no_unsubstituted_placeholders(self):
        text = theme.QSS.substitute(theme.palette_vars())
        self.assertNotIn("$", text, "у QSS лишився невідомий підстановлювач")
        self.assertIn("QToolButton#Primary", text)

    def test_both_palettes_substitute_without_missing_keys(self):
        for name in ("dark", "light"):
            try:
                theme.Colors.use(name)
                with self.subTest(theme=name):
                    self.assertIn("background-color", theme.QSS.substitute(theme.palette_vars()))
            finally:
                theme.Colors.use("dark")


if __name__ == "__main__":
    unittest.main()
