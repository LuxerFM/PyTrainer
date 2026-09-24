"""Темна тема застосунку: палітра, шрифти і таблиця стилів (QSS).

Всі кольори зібрані в одному класі `Colors`. Якщо захочеться світлу тему —
достатньо зробити другий такий клас і викликати apply_theme(app, інша_палітра).
"""

from string import Template

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication


class Colors:
    """Палітра темної теми (назви як у VS Code, кольори — власні)."""

    bg = "#101216"          # фон вікна
    panel = "#161922"       # панелі (сайдбар, панель задач)
    elevated = "#1e222c"    # елементи поверх панелей (кнопки, меню)
    border = "#272b36"      # лінії розділювачів
    text = "#dfe3ea"        # основний текст
    muted = "#8a92a3"       # другорядний текст
    accent = "#4c8dff"      # акцент (кнопки, прогрес)
    accent_hover = "#6ba1ff"
    accent_press = "#3d76d9"
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


# Шрифти пробуємо по порядку — беремо перший, який є в системі.
MONO_FONTS = ("Cascadia Mono", "JetBrains Mono", "Consolas", "Menlo",
              "DejaVu Sans Mono", "Courier New")
UI_FONTS = ("Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans",
            "Helvetica Neue", "DejaVu Sans")


def pick_font(candidates: tuple[str, ...], size: int) -> QFont:
    """Повертає перший доступний шрифт зі списку."""
    available = set(QFontDatabase.families())
    for name in candidates:
        if name in available:
            return QFont(name, size)
    return QFont(candidates[-1], size)


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
    color: #0b1220;
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

/* ---------- вкладки ---------- */
QTabWidget::pane { border: none; top: -1px; }
QTabBar::tab {
    background: transparent;
    color: $muted;
    padding: 9px 14px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}
QTabBar::tab:hover { color: $text; }
QTabBar::tab:selected { color: $text; border-bottom: 2px solid $accent; }

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
QToolButton#NavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 10px;
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


def apply_theme(app: QApplication) -> None:
    """Застосовує темну тему до всього застосунку."""
    # Fusion поводиться однаково на Windows/Linux/macOS — потрібно для стабільності.
    app.setStyle("Fusion")
    app.setFont(pick_font(UI_FONTS, 10))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.bg))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.editor_bg))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.selection))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.text))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.elevated))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.text))
    app.setPalette(palette)

    app.setStyleSheet(QSS.substitute(vars(Colors)))
