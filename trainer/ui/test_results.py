"""The "Тести" ("Tests") tab: check cards, verdict, explanation, jump button.

Extracted from `TaskPanel` (split slice 5, module 1). The controller holds a
pointer to the panel (`p`) and draws via its widgets — card state stays in
the panel.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .theme import Colors

if TYPE_CHECKING:
    from curriculum import Check, Task

    from ..core.runner import RunResult
    from .task_panel import TaskPanel


def _tr(text: str) -> str:
    return QCoreApplication.translate("TestResults", text)


class TestResults:
    """Check-tab renderer."""

    def __init__(self, panel: TaskPanel) -> None:
        self.p = panel

    def clear_checks(self) -> None:
        p = self.p
        while p.checks_box.count() > 1:
            item = p.checks_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                p._drop_widget(widget)
        p._check_cards.clear()

    def add_card(self, widget: QWidget, box: QVBoxLayout | None = None) -> None:
        target = box if box is not None else self.p.checks_box
        target.insertWidget(target.count() - 1, widget)

    def check_card(
        self,
        *,
        mark: str,
        name: str,
        detail: str = "",
        state: str = "pending",
        tooltip: str = "",
        extra: QWidget | None = None,
    ) -> QFrame:
        """One card: state icon, check name and explanation."""
        card = QFrame()
        card.setObjectName("CheckCard")
        colours = {
            "ok": (Colors.success, Colors.border),
            "fail": (Colors.error, Colors.error),
            "pending": (Colors.muted, Colors.border),
            "info": (Colors.warn, Colors.warn),
        }
        mark_colour, border = colours.get(state, colours["pending"])
        card.setStyleSheet(
            f"QFrame#CheckCard {{ background-color: {Colors.elevated};"
            f" border: 1px solid {border}; border-radius: 8px; }}"
        )

        row = QHBoxLayout(card)
        row.setContentsMargins(11, 9, 11, 9)
        row.setSpacing(9)

        mark_label = QLabel(mark)
        mark_label.setObjectName("CheckMark")
        mark_label.setStyleSheet(f"color: {mark_colour};")
        mark_label.setFixedWidth(16)
        mark_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        row.addWidget(mark_label)

        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(3)

        name_label = QLabel(name)
        name_label.setObjectName("CheckName")
        name_label.setWordWrap(True)
        column.addWidget(name_label)

        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName(
                "CheckError" if state == "fail" else "CheckDetail"
            )
            detail_label.setWordWrap(True)
            detail_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            column.addWidget(detail_label)

        if extra is not None:
            column.addWidget(extra)

        row.addLayout(column, 1)
        if tooltip:
            card.setToolTip(tooltip)
        return card

    @staticmethod
    def check_kind(check: Check) -> str:
        return _tr("перевірка виводу програми") if check.is_stdout else _tr("перевірка коду")

    def show_planned_checks(self, task: Task | None) -> None:
        """Shows the check list **before** the run: what exactly they will demand."""
        p = self.p
        self.clear_checks()

        if task is None or not task.checks:
            p.tests_summary.setObjectName("VerdictWarn")
            p.tests_summary.setText(_tr("Це пункт поза тренажером"))
            p.tests_detail.setText(
                _tr("Тут немає прихованих тестів — результат оцінюєш ти сам.")
            )
        else:
            total = len(task.checks)
            p.tests_summary.setObjectName("VerdictWarn")
            form = (_tr("перевірка") if total == 1 else
                    _tr("перевірки") if 2 <= total <= 4 else
                    _tr("перевірок"))
            p.tests_summary.setText(
                _tr("Буде {n} {form} — ще не запускались").format(n=total, form=form)
            )
            for check in task.checks:
                self.add_card(self.check_card(
                    mark="○",
                    name=check.name,
                    detail=self.check_kind(check),
                    state="pending",
                ))
            p.tests_detail.setText(
                _tr("Перевірки приховані: ти бачиш, що саме вони вимагають, але не "
                    "сам код тесту. Натисни «Перевірити» (F5), щоб прогнати їх.")
            )

        p._repolish(p.tests_summary)

    def reset_tests(self) -> None:
        self.show_planned_checks(self.p._task)

    def show_result(self, result: RunResult, with_checks: bool) -> None:
        from .task_panel import TAB_TESTS

        p = self.p
        self.clear_checks()

        if with_checks and result.checks:
            passed = result.passed_count
            total = len(result.checks)

            for check in result.checks:
                detail = ""
                if check.ok:
                    detail = _tr("пройдено")
                elif check.error:
                    detail = check.error
                if not check.ok and check.actual:
                    first_lines = "\n".join(check.actual.splitlines()[:4])
                    shown = _tr("Насправді вивела:\n{lines}").format(lines=first_lines)
                    detail = f"{detail}\n{shown}" if detail else shown
                self.add_card(self.check_card(
                    mark="✓" if check.ok else "✕",
                    name=check.name,
                    detail=detail.strip(),
                    state="ok" if check.ok else "fail",
                    tooltip=check.error,
                ))

            if result.all_passed:
                p.tests_summary.setObjectName("VerdictOk")
                p.tests_summary.setText(
                    _tr("Усі перевірки пройдено: {passed} із {total} ✓").format(
                        passed=passed, total=total)
                )
            else:
                p.tests_summary.setObjectName("VerdictBad")
                p.tests_summary.setText(
                    _tr("Пройдено {passed} із {total} — є що виправити").format(
                        passed=passed, total=total)
                )

            self.show_advice(result, passed, total)
        elif result.timed_out:
            p.tests_summary.setObjectName("VerdictWarn")
            p.tests_summary.setText(_tr("Код зупинено за таймаутом"))
            self.show_advice(result, 0, 0)
        elif result.stderr:
            p.tests_summary.setObjectName("VerdictBad")
            p.tests_summary.setText(_tr("Код впав з помилкою"))
            self.show_advice(result, 0, 0)
        else:
            p.tests_summary.setObjectName("VerdictOk")
            p.tests_summary.setText(_tr("Код виконано без помилок"))
            p.tests_detail.setText(
                _tr("Це був звичайний запуск. Натисни «Перевірити» (F5), щоб "
                    "прогнати приховані тести.")
            )

        p._repolish(p.tests_summary)
        p.tabs.setCurrentIndex(TAB_TESTS)

    def show_advice(self, result: RunResult, passed: int, total: int) -> None:
        """Explains the error in human language and hints the next step."""
        p = self.p
        advice = result.advice
        self.add_jump_button(result)
        if not advice:
            if result.all_passed:
                p.tests_detail.setText(
                    _tr("Так тримати! Наступна задача — у списку зліва (Ctrl+N).")
                )
            else:
                first_error = result.first_error
                p.tests_detail.setText(
                    _tr("Перша проблема: {err}").format(err=first_error) if first_error
                    else _tr("Подивись, яка саме перевірка впала, вище.")
                )
            return

        kind = advice.splitlines()[0]
        self.add_card(self.check_card(
            mark="?",
            name=_tr("Що це означає"),
            detail=advice,
            state="info",
            tooltip=kind,
        ))
        p.tests_detail.setText(
            _tr("Помилка — це підказка, а не вирок: Python каже, де саме код "
                "розійшовся з твоїм задумом.")
        )

    def add_jump_button(self, result: RunResult) -> None:
        """A "jump to line N" button — the fastest path from error to code.

        The error explainer already knows the line number; the human just
        needs a button instead of hunting it with their eyes in the editor.
        """
        p = self.p
        line = result.failed_line
        if not line:
            p._jump_line = 0
            return
        p._jump_line = line
        button = QPushButton(_tr("↪  Перейти до рядка {n}").format(n=line))
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
        self.add_card(holder)

    @property
    def jump_line(self) -> int:
        """Line jumpable to after the last run (0 — none)."""
        return getattr(self.p, "_jump_line", 0)


__all__ = ["TestResults"]
