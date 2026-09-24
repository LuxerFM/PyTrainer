"""Підсвітка синтаксису Python.

Ідея проста: описуємо список правил «регулярний вираз → колір» і на кожному
рядку фарбуємо все, що підходить. Правила застосовуються по порядку, тому
код, рядки і коментарі стоять у списку останніми — вони перемагають.
"""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from .theme import Colors

KEYWORDS = (
    "if elif else for while break continue pass return def class import from as "
    "try except finally raise with lambda global nonlocal del not and or in is "
    "assert yield async await match case"
).split()

BUILTINS = (
    "print len range input int str float bool list dict set tuple sum min max abs "
    "round sorted reversed enumerate zip open type isinstance len range divmod "
    "ValueError TypeError KeyError IndexError ZeroDivisionError Exception FileNotFoundError"
).split()


def _format(colour: str, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(colour))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt


def build_rules() -> list[tuple[QRegularExpression, QTextCharFormat]]:
    """Повертає правила підсвітки у порядку застосування."""
    keyword = _format(Colors.syn_keyword, bold=True)
    builtin = _format(Colors.syn_builtin)
    self_kw = _format(Colors.syn_self, italic=True)
    number = _format(Colors.syn_number)
    func = _format(Colors.syn_func)
    decorator = _format(Colors.syn_decorator)
    string = _format(Colors.syn_string)
    comment = _format(Colors.syn_comment, italic=True)

    rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
        (QRegularExpression(r"\b(?:%s)\b" % "|".join(KEYWORDS)), keyword),
        (QRegularExpression(r"\b(?:%s)\b" % "|".join(BUILTINS)), builtin),
        (QRegularExpression(r"\bself\b"), self_kw),
        (QRegularExpression(r"\b\d+(?:\.\d+)?\b"), number),
        (QRegularExpression(r"@\w[\w.]*"), decorator),
        (QRegularExpression(r"(?<=\bdef\s)\w+"), func),
        (QRegularExpression(r"(?<=\bclass\s)\w+"), func),
        (QRegularExpression(r"[\+\-\*/%=<>!&|^~]+"), _format(Colors.text)),
        # останні три перекривають усе інше — так і треба
        (QRegularExpression(r'"""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\''), string),
        (QRegularExpression(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''), string),
        (QRegularExpression(r"#[^\n]*"), comment),
    ]
    return rules


class PythonHighlighter(QSyntaxHighlighter):
    """Фарбує код Python у QPlainTextEdit."""

    def __init__(self, document) -> None:
        super().__init__(document)
        self._rules = build_rules()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (назва з Qt)
        for pattern, fmt in self._rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
