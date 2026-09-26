"""Вкладка «Рев'ю»: картки розбору коду з кнопками переходу до рядка.

Витягнуто з `TaskPanel` (зріз 5 розпилу, модуль 2). Контролер тримає
вказівник на панель (`p`) — стан карток лишається у панелі.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ..core.codereview import NOT_REVIEWED

if TYPE_CHECKING:
    from PySide6.QtWidgets import QFrame

    from ..core.codereview import CodeReview, Remark
    from .task_panel import TaskPanel


class ReviewView:
    """Рендер вкладки розбору коду."""

    def __init__(self, panel: TaskPanel) -> None:
        self.p = panel

    def show_review(self, review: CodeReview) -> None:
        """Показує розбір коду: зауваження з номерами рядків і одну похвалу."""
        from .task_panel import TAB_REVIEW

        p = self.p
        self.clear_review()
        p.review_summary.setText(review.summary)
        p.review_summary.setObjectName("VerdictOk" if review.ok else "VerdictWarn")
        p._repolish(p.review_summary)

        for remark in review.remarks:
            p._add_card(self.review_card(remark), p.review_box)

        issues = len(review.issues)
        p.tabs.setTabText(TAB_REVIEW, f"Рев'ю · {issues}" if issues else "Рев'ю")
        p.review_button.setText("Розібрати ще раз")

    def reset_review(self) -> None:
        """Забуває попередній розбір: для нової задачі він був би брехнею."""
        from .task_panel import TAB_REVIEW

        p = self.p
        self.clear_review()
        p.review_summary.setText(NOT_REVIEWED)
        p.review_summary.setObjectName("Subtle")
        p._repolish(p.review_summary)
        p.review_button.setText("Розібрати код")
        p.tabs.setTabText(TAB_REVIEW, "Рев'ю")

    @property
    def review_cards(self) -> list[QFrame]:
        """Картки розбору — щоб тести могли їх порахувати."""
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
            tooltip=f"Рядок {remark.line}" if remark.line else "",
            extra=self.line_button(remark.line),
        )

    def line_button(self, line: int) -> QWidget | None:
        """Кнопка «перейти до рядка» — з зауваження одразу в код."""
        if not line:
            return None
        p = self.p
        button = QPushButton(f"↪  Рядок {line}")
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
