"""Тема застосунку: палітри (темна й світла), шрифти і таблиця стилів (QSS).

Увесь інтерфейс звертається до кольорів через `Colors.accent`, `Colors.muted`
тощо. За цим ім'ям стоїть не клас, а «перемикач» активної палітри — тому
перемикання теми не вимагає жодних змін у віджетах: вони читають ті самі
атрибути й отримують уже нові кольори.

Тут же живе масштаб шрифту (`set_scale`): розміри в QSS задані в пікселях, і
під час збирання таблиці стилів ми множимо їх на поточний коефіцієнт.
"""

import re
import sys
from pathlib import Path
from string import Template

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication


class DarkPalette:
    """Темна тема (назви як у VS Code, кольори — власні)."""

    bg = "#101216"          # фон вікна
    panel = "#161922"       # панелі (сайдбар, панель задач)
    elevated = "#1e222c"    # елементи поверх панелей (кнопки, меню)
    border = "#272b36"      # лінії розділювачів
    text = "#dfe3ea"        # основний текст
    muted = "#8a92a3"       # другорядний текст
    strong = "#ffffff"      # текст, який має «виступати» (жирне в умові)
    accent = "#4c8dff"      # акцент (кнопки, прогрес)
    accent_hover = "#6ba1ff"
    accent_press = "#3d76d9"
    on_accent = "#0b1220"   # текст на акцентній кнопці
    selection = "#2b3a55"   # виділення
    editor_bg = "#0c0e13"   # фон редактора
    gutter_bg = "#0a0c10"   # фон смуги з номерами рядків
    scroll = "#2e3340"      # повзунок прокрутки
    scroll_hover = "#3b4152"
    success = "#3ecf8e"     # тест пройдено
    error = "#ff6b6b"       # помилка
    warn = "#ffb454"        # попередження

    # кольори підсвітки синтаксису Python
    syn_keyword = "#ff8ab5"
    syn_builtin = "#4fc1ff"
    syn_self = "#ffb454"
    syn_string = "#a5e075"
    syn_comment = "#6a7285"
    syn_number = "#c3a6ff"
    syn_func = "#ffd479"
    syn_decorator = "#7fd1c0"


class LightPalette:
    """Світла тема: та сама структура, інші кольори.

    Кольори підсвітки синтаксису тут темніші: на білому фоні світлі
    відтінки з темної теми просто не читаються.
    """

    bg = "#f3f5f9"
    panel = "#e9edf4"
    elevated = "#ffffff"
    border = "#d2d8e4"
    text = "#1d222c"
    muted = "#5c6574"
    strong = "#000000"
    accent = "#2f6fe4"
    accent_hover = "#2a63cd"
    accent_press = "#2456b3"
    on_accent = "#ffffff"
    selection = "#cfe0ff"
    editor_bg = "#ffffff"
    gutter_bg = "#f5f6fa"
    scroll = "#c4cbd9"
    scroll_hover = "#a9b2c4"
    success = "#187f52"
    error = "#c23333"
    warn = "#9a6208"

    syn_keyword = "#c2185b"
    syn_builtin = "#0b62a4"
    syn_self = "#9a6208"
    syn_string = "#2f7d32"
    syn_comment = "#78818f"
    syn_number = "#6b3fc4"
    syn_func = "#7a5c00"
    syn_decorator = "#0f7f74"


PALETTES = {"dark": DarkPalette, "light": LightPalette}


class _ActivePalette:
    """Об'єкт, читання атрибутів якого йде до активної палітри.

    Саме тому в усьому коді можна писати `Colors.accent`, не думаючи про тему.
    """

    def __init__(self) -> None:
        self._palette = DarkPalette

    def use(self, name: str) -> None:
        self._palette = PALETTES.get(name, DarkPalette)

    @property
    def name(self) -> str:
        """Назва активної теми: "dark" або "light"."""
        return "light" if self._palette is LightPalette else "dark"

    def __getattr__(self, item: str) -> str:
        return getattr(self._palette, item)


Colors = _ActivePalette()


def palette_vars() -> dict[str, str]:
    """Кольори активної палітри — для підстановки в QSS."""
    return {
        key: value
        for key, value in vars(Colors._palette).items()  # noqa: SLF001 — навмисно
        if not key.startswith("_") and isinstance(value, str)
    }


# Шрифти пробуємо по порядку — беремо перший, який є в системі.
MONO_FONTS = ("Cascadia Mono", "JetBrains Mono", "Consolas", "Menlo",
              "DejaVu Sans Mono", "Courier New")
UI_FONTS = ("Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans",
            "Helvetica Neue", "DejaVu Sans")

# Текст умов задач і підказок читають довше, ніж підписи в інтерфейсі, тому
# для нього окремий, трохи «спокійніший» список: довгі засічки тут заважають.
PROSE_FONTS = ("Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans",
               "Noto Sans Display", "Helvetica Neue", "DejaVu Sans")

_FAMILY_CACHE: dict[tuple[str, ...], str] = {}

_BUNDLED_FILES = ("Inter-Regular.otf", "Inter-Bold.otf",
                  "JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf")
_BUNDLED_LOADED = False


def _fonts_dir() -> Path:
    """Bundled-fonts folder — works from code and from the built .exe."""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parents[2]
    return root / "assets" / "fonts"


def load_bundled_fonts() -> list[str]:
    """Registers bundled Inter + JetBrains Mono and prefers them.

    Why bundled: system fonts vary per machine (and CI/offscreen images may
    lack Cyrillic glyphs entirely — hence tofu screenshots). Bundled fonts
    render the same everywhere, in both Ukrainian and English. Safe to call
    any number of times; before a QApplication exists it does nothing and
    the system-font fallback applies.
    """
    global _BUNDLED_LOADED, MONO_FONTS, UI_FONTS, PROSE_FONTS
    if _BUNDLED_LOADED:
        return []
    if QApplication.instance() is None:
        return []
    folder = _fonts_dir()
    families: list[str] = []
    if folder.is_dir():
        for name in _BUNDLED_FILES:
            fid = QFontDatabase.addApplicationFont(str(folder / name))
            if fid != -1:
                families.extend(QFontDatabase.applicationFontFamilies(fid))
    for family in families:
        if "Mono" in family:
            if family not in MONO_FONTS:
                MONO_FONTS = (family,) + MONO_FONTS
        elif family not in UI_FONTS:
            UI_FONTS = (family,) + UI_FONTS
            PROSE_FONTS = (family,) + PROSE_FONTS
    _BUNDLED_LOADED = True
    _FAMILY_CACHE.clear()
    return families


def pick_font(candidates: tuple[str, ...], size: int) -> QFont:
    """Повертає перший доступний шрифт зі списку."""
    load_bundled_fonts()
    available = set(QFontDatabase.families())
    for name in candidates:
        if name in available:
            return QFont(name, size)
    return QFont(candidates[-1], size)


def family_name(candidates: tuple[str, ...]) -> str:
    """Назва першого доступного шрифта — щоб вставити в HTML/CSS.

    Потрібно для `QTextBrowser`: там стилі задаються текстом, а не QFont.
    Результат кешуємо: QFontDatabase.families() — не найдешевша операція.
    """
    load_bundled_fonts()
    cached = _FAMILY_CACHE.get(candidates)
    if cached is not None:
        return cached

    available = set(QFontDatabase.families())
    for name in candidates:
        if name in available:
            _FAMILY_CACHE[candidates] = name
            return name
    _FAMILY_CACHE[candidates] = candidates[-1]
    return candidates[-1]


def prose_family() -> str:
    """Сімейство шрифта для умов, підказок і шпаргалок."""
    return family_name(PROSE_FONTS)


def mono_family() -> str:
    """Сімейство моноширинного шрифта для коду в текстах."""
    return family_name(MONO_FONTS)


# --------------------------------------------------------------------------
# масштаб шрифту
# --------------------------------------------------------------------------

_SCALE = 1.0
MIN_SCALE, MAX_SCALE = 0.85, 1.6


def set_scale(value: float) -> float:
    """Задає масштаб шрифту (з обмеженням) і повертає те, що вийшло."""
    global _SCALE
    _SCALE = max(MIN_SCALE, min(MAX_SCALE, round(value, 2)))
    return _SCALE


def scale() -> float:
    return _SCALE


def ui_size(base: int) -> int:
    """Розмір шрифту з урахуванням масштабу — для QFont і HTML."""
    return max(8, round(base * _SCALE))


def scaled_qss(text: str) -> str:
    """Множить усі `font-size: Npx` у таблиці стилів на поточний масштаб."""
    if _SCALE == 1.0:
        return text
    return re.sub(
        r"font-size:\s*(\d+)px",
        lambda match: f"font-size: {ui_size(int(match.group(1)))}px",
        text,
    )


def truncate(text: str, length: int = 58) -> str:
    """Короткий підпис для дерева/списків."""
    text = " ".join(text.split())
    return text if len(text) <= length else text[: length - 1] + "…"


QSS = Template(
    """
QWidget {
    background-color: $bg;
    color: $text;
}
QToolTip {
    background-color: $elevated;
    color: $text;
    border: 1px solid $border;
    padding: 4px 8px;
}

/* ---------- меню ---------- */
QMenuBar {
    background-color: $panel;
    border-bottom: 1px solid $border;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
}
QMenuBar::item:selected { background-color: $elevated; }
QMenu {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 26px 6px 12px;
    border-radius: 6px;
}
QMenu::item:selected { background-color: $selection; }
QMenu::separator { height: 1px; background: $border; margin: 6px 8px; }

/* ---------- верхня панель ---------- */
QToolBar {
    background-color: $panel;
    border-bottom: 1px solid $border;
    padding: 8px 10px;
    spacing: 6px;
}
QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 7px 13px;
    color: $text;
    font-weight: 600;
}
QToolBar QToolButton:hover { background-color: $elevated; border-color: $border; }
QToolBar QToolButton:pressed { background-color: $border; }
QToolBar QToolButton:disabled { color: $muted; }

QToolButton#Primary {
    background-color: $accent;
    color: $on_accent;
    border: none;
    font-weight: 700;
}
QToolButton#Primary:hover { background-color: $accent_hover; }
QToolButton#Primary:pressed { background-color: $accent_press; }
QToolButton#Primary:disabled { background-color: $elevated; color: $muted; }

/* ---------- панелі та картки ---------- */
QWidget#Panel { background-color: $panel; }
QWidget#Header { background-color: $panel; border-bottom: 1px solid $border; }
QLabel#Brand { font-size: 16px; font-weight: 700; }
QLabel#BrandAccent { color: $accent; font-size: 16px; font-weight: 700; }
QLabel#Subtle { color: $muted; font-size: 12px; }
QLabel#Meta { color: $muted; font-size: 12px; }
QLabel#Source { color: $muted; font-size: 11px; }
QLabel#SectionTitle {
    color: $muted;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 8px 4px 4px 4px;
}
QLabel#Badge {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: 11px;
    padding: 4px 11px;
    color: $muted;
    font-weight: 600;
}
QLabel#BadgeAccent { color: $accent; background-color: $elevated;
    border: 1px solid $border; border-radius: 11px; padding: 4px 11px;
    font-weight: 700; }
QLabel#TaskTitle { font-size: 15px; font-weight: 700; }

/* ---------- картки перевірок («Тести») ---------- */
QLabel#CheckName { font-weight: 600; font-size: 13px; }
QLabel#CheckMark { font-size: 14px; font-weight: 700; }
QLabel#CheckDetail { color: $muted; font-size: 12px; }
QLabel#CheckError { color: $error; font-size: 12px; }
QLabel#CheckOk { color: $success; font-size: 12px; }
QLabel#VerdictOk {
    color: $success; font-weight: 700; font-size: 13px;
    background-color: $elevated; border: 1px solid $border;
    border-left: 3px solid $success; border-radius: 8px; padding: 9px 12px;
}
QLabel#VerdictBad {
    color: $error; font-weight: 700; font-size: 13px;
    background-color: $elevated; border: 1px solid $border;
    border-left: 3px solid $error; border-radius: 8px; padding: 9px 12px;
}
QLabel#VerdictWarn {
    color: $warn; font-weight: 700; font-size: 13px;
    background-color: $elevated; border: 1px solid $border;
    border-left: 3px solid $warn; border-radius: 8px; padding: 9px 12px;
}
QLabel#Advice {
    color: $text; font-size: 12px;
    background-color: $editor_bg; border: 1px solid $border;
    border-left: 3px solid $warn; border-radius: 8px; padding: 10px 12px;
}
QLabel#HintTitle { font-weight: 600; font-size: 13px; }

/* ---------- дерево роадмапу ---------- */
QTreeWidget {
    background-color: $panel;
    border: none;
    show-decoration-selected: 1;
    outline: none;
}
QTreeWidget::item {
    padding: 6px 4px;
    border-radius: 7px;
    margin: 1px 6px 1px 0;
}
QTreeWidget::item:hover { background-color: $elevated; }
QTreeWidget::item:selected { background-color: $selection; color: $text; }

/* ---------- редактор і консоль ---------- */
QPlainTextEdit#Editor {
    background-color: $editor_bg;
    border: none;
    selection-background-color: $selection;
    color: $text;
}
QTextEdit#Console {
    background-color: $editor_bg;
    border: none;
    color: $text;
}
QTextBrowser { background: transparent; border: none; }
QTextBrowser#Statement {
    background-color: $panel;
    selection-background-color: $selection;
}
QTextBrowser#CheatSheet { background-color: $panel; }
QScrollArea#ChecksPage { background: transparent; border: none; }

/* ---------- вкладки ---------- */
QTabWidget::pane { border: none; top: -1px; }
QTabBar::tab {
    background: transparent;
    color: $muted;
    padding: 9px 11px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}
QTabBar::tab:hover { color: $text; }
QTabBar::tab:selected { color: $text; border-bottom: 2px solid $accent; }

/* ---------- випадний список (довідка) ---------- */
QComboBox {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px 10px;
    color: $text;
    font-weight: 600;
}
QComboBox:hover { border-color: $accent; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: $elevated;
    border: 1px solid $border;
    selection-background-color: $selection;
    selection-color: $text;
    color: $text;
    outline: none;
    padding: 4px;
}

/* ---------- списки та прокрутка ---------- */
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { padding: 7px 6px; border-radius: 7px; }
QListWidget::item:hover { background-color: $elevated; }

QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 11px; margin: 3px; }
QScrollBar:horizontal { background: transparent; height: 11px; margin: 3px; }
QScrollBar::handle { background-color: $scroll; border-radius: 4px; }
QScrollBar::handle:hover { background-color: $scroll_hover; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---------- інше ---------- */
QSplitter::handle { background-color: $border; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

QProgressBar {
    background-color: $elevated;
    border: none;
    border-radius: 4px;
    height: 8px;
    color: transparent;
}
QProgressBar::chunk { background-color: $accent; border-radius: 4px; }

QStatusBar { background-color: $panel; border-top: 1px solid $border; color: $muted; }
QStatusBar::item { border: none; }
QLineEdit {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px 10px;
    color: $text;
    selection-background-color: $selection;
}
QLineEdit:focus { border-color: $accent; }

QToolButton#NavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 7px;
    color: $muted;
    font-weight: 600;
}
QToolButton#NavButton:hover { background-color: $elevated; color: $text; }
QToolButton#NavButton:checked { background-color: $selection; color: $text; }

QFrame#Card {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: 10px;
}
QLabel#StatValue { font-size: 19px; font-weight: 700; }
QLabel#StatCaption { color: $muted; font-size: 11px; }
QLabel#Good { color: $success; font-weight: 600; }
QLabel#Warn { color: $warn; font-weight: 600; }
QLabel#Bad { color: $error; font-weight: 600; }

QPushButton#Ghost {
    background-color: transparent;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 7px 14px;
    color: $text;
    font-weight: 600;
}
QPushButton#Ghost:hover { background-color: $elevated; }
QPushButton#Ghost:disabled { color: $muted; }
"""
)


def apply_theme(app: QApplication, theme: str | None = None) -> None:
    """Застосовує тему й масштаб шрифту до всього застосунку.

    theme="dark" / "light" перемикає палітру; None — лишає поточну.
    """
    if theme:
        Colors.use(theme)

    # Fusion поводиться однаково на Windows/Linux/macOS — потрібно для стабільності.
    app.setStyle("Fusion")
    app.setFont(pick_font(UI_FONTS, ui_size(10)))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.bg))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.editor_bg))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.selection))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.elevated))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.elevated))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(Colors.muted))
    app.setPalette(palette)

    app.setStyleSheet(scaled_qss(QSS.substitute(palette_vars())))
