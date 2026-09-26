"""The "Рев'ю" ("Review") tab: code-review cards with line-jump buttons.

Extracted from `TaskPanel` (split slice 5, module 2). The controller holds a
pointer to the panel (`p`) — card state stays in the panel.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ..core.codereview import NOT_REVIEWED

if TYPE_CHECKING:
    from PySide6.QtWidgets import QFrame

    from ..core.codereview import CodeReview, Remark
    from .task_panel import TaskPanel


def _tr(text: str) -> str:
    return QCoreApplication.translate("ReviewView", text)


class ReviewView:
    """Code-review tab renderer."""

    def __init__(self, panel: TaskPanel) -> None:
        self.p = panel

    def show_review(self, review: CodeReview) -> None:
        """Shows the code review: remarks with line numbers and one praise."""
        from .task_panel import TAB_REVIEW

        p = self.p
        self.clear_review()
        p.review_summary.setText(review.summary)
        p.review_summary.setObjectName("VerdictOk" if review.ok else "VerdictWarn")
        p._repolish(p.review_summary)

        for remark in review.remarks:
            p._add_card(self.review_card(remark), p.review_box)

        issues = len(review.issues)
        tab = _tr("Рев'ю · {n}").format(n=issues) if issues else _tr("Рев'ю")
        p.tabs.setTabText(TAB_REVIEW, tab)
        p.review_button.setText(_tr("Розібрати ще раз"))

    def reset_review(self) -> None:
        """Forgets the previous review: for a new task it would be a lie."""
        from .task_panel import TAB_REVIEW

        p = self.p
        self.clear_review()
        p.review_summary.setText(NOT_REVIEWED)
        p.review_summary.setObjectName("Subtle")
        p._repolish(p.review_summary)
        p.review_button.setText(_tr("Розібрати код"))
        p.tabs.setTabText(TAB_REVIEW, _tr("Рев'ю"))

    @property
    def review_cards(self) -> list[QFrame]:
        """Review cards — so tests can count them."""
        p = self.p
        return [
            widget
            for index in range(p.review_box.count())
            if (widget := p.review_box.itemAt(index).widget()) is not None
        ]

    def clear_review(self) -> None:
        p = self.p
        while p.review_box.count() > 1:
            item = p.review_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                p._drop_widget(widget)

    def review_card(self, remark: Remark) -> QFrame:
        return self.p._check_card(
            mark="✎" if remark.is_praise else "!",
            name=remark.title,
            detail=remark.advice,
            state="ok" if remark.is_praise else "info",
            tooltip=_tr("Рядок {n}").format(n=remark.line) if remark.line else "",
            extra=self.line_button(remark.line),
        )

    def line_button(self, line: int) -> QWidget | None:
        """A "jump to line" button — from the remark straight into code."""
        if not line:
            return None
        p = self.p
        button = QPushButton(_tr("↪  Рядок {n}").format(n=line))
        button.setObjectName("Ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda _=False, number=line: p.jump_to_line_requested.emit(number)
        )
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(button)
        row.addStretch(1)
        return holder


__all__ = ["ReviewView"]
