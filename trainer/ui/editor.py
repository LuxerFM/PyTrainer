"""Code editor.

Qt itself has no ready "code field", so we assemble one from QPlainTextEdit:
a line-number gutter, current-line highlight, auto-indent after `:`,
Tab = 4 spaces, Ctrl+Enter = run code.
"""

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetricsF, QPainter, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from .highlighter import PythonHighlighter
from .theme import MONO_FONTS, Colors, pick_font, ui_size

INDENT = " " * 4


class _LineNumberArea(QWidget):
    """Gutter left of the code, where line numbers are drawn."""

    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._editor.gutter_width(), 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._editor.paint_gutter(event)


class CodeEditor(QPlainTextEdit):
    """Code field with all the comforts."""

    run_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Editor")
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCursorWidth(2)

        font = pick_font(MONO_FONTS, ui_size(11))
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(" ") * 4)

        self._gutter = _LineNumberArea(self)
        self._highlighter = PythonHighlighter(self.document())

        self.blockCountChanged.connect(self._refresh_gutter_width)
        self.updateRequest.connect(self._refresh_gutter)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._refresh_gutter_width()
        self._highlight_current_line()

    def apply_theme(self) -> None:
        """Rereads the font and highlight colours.

        Needed after a theme or scale change: syntax colours are kept not by
        QSS but by the highlighter itself, so it must be recreated.
        """
        font = pick_font(MONO_FONTS, ui_size(11))
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(" ") * 4)

        self._highlighter.setDocument(None)      # unbind the old one
        self._highlighter = PythonHighlighter(self.document())
        self._highlighter.rehighlight()
        self._refresh_gutter_width()
        self._highlight_current_line()

    # ---------- number gutter ----------

    def gutter_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _refresh_gutter_width(self) -> None:
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _refresh_gutter(self, rect: QRect, dy: int) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._refresh_gutter_width()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        area = self.contentsRect()
        self._gutter.setGeometry(
            QRect(area.left(), area.top(), self.gutter_width(), area.height())
        )

    def paint_gutter(self, event) -> None:
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor(Colors.gutter_bg))

        current_line = self.textCursor().blockNumber()
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        offset = self.contentOffset()
        top = self.blockBoundingGeometry(block).translated(offset).top()
        bottom = top + self.blockBoundingRect(block).height()
        line_height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                colour = Colors.accent if number == current_line else Colors.muted
                painter.setPen(QColor(colour))
                painter.drawText(
                    0,
                    int(top),
                    self._gutter.width() - 10,
                    line_height,
                    Qt.AlignmentFlag.AlignRight,
                    str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            number += 1
        painter.end()

    # ---------- current-line highlight ----------

    def _highlight_current_line(self) -> None:
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(Colors.elevated))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    # ---------- keys ----------

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+Enter (on macOS — Cmd+Enter) = run
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and modifiers in (
            Qt.KeyboardModifier.ControlModifier,
            Qt.KeyboardModifier.MetaModifier,
        ):
            self.run_requested.emit()
            return

        if key == Qt.Key.Key_Tab and not modifiers:
            self._indent_selection()
            return
        if key == Qt.Key.Key_Backtab:  # Shift+Tab
            self._dedent_selection()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not modifiers:
            self._smart_newline()
            return
        super().keyPressEvent(event)

    # ---------- indents ----------

    def _selected_lines(self) -> tuple[int, int]:
        cursor = self.textCursor()
        start = self.document().findBlock(cursor.selectionStart()).blockNumber()
        if cursor.hasSelection():
            end = self.document().findBlock(cursor.selectionEnd()).blockNumber()
        else:
            end = start
        return start, end

    def _indent_selection(self) -> None:
        """Tab: adds indent (one line — just 4 spaces)."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.insertText(INDENT)
            return
        self._shift_lines(INDENT)

    def _dedent_selection(self) -> None:
        self._shift_lines(INDENT, remove=True)

    def _shift_lines(self, indent: str, remove: bool = False) -> None:
        start, end = self._selected_lines()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        for number in range(start, end + 1):
            block = self.document().findBlockByNumber(number)
            line = block.text()
            if remove:
                if line.startswith(indent):
                    cut = len(indent)
                elif line.startswith(" "):
                    cut = len(line) - len(line.lstrip(" "))
                    cut = min(cut, len(indent))
                elif line.startswith("\t"):
                    cut = 1
                else:
                    continue
                edit = self.textCursor()
                edit.setPosition(block.position())
                edit.movePosition(edit.MoveOperation.Right, edit.MoveMode.KeepAnchor, cut)
                edit.removeSelectedText()
            elif block.text().strip():  # leave empty lines alone
                edit = self.textCursor()
                edit.setPosition(block.position())
                edit.insertText(indent)
        cursor.endEditBlock()

    def _smart_newline(self) -> None:
        """Enter: keeps the indent and adds 4 spaces after `:` itself."""
        cursor = self.textCursor()
        line = cursor.block().text()[: cursor.positionInBlock()]
        indent = line[: len(line) - len(line.lstrip(" \t"))]
        if line.rstrip().endswith(":") or line.rstrip().endswith("\\"):
            indent += INDENT
        cursor.insertText("\n" + indent)
        self.ensureCursorVisible()
