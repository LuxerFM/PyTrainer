"""Ліва панель: дерево шляху, черга повторень і статистика.

Три режими в одній колонці — щоб не плодити вікна. Перемикач зверху
перемикає QStackedWidget зі сторінками.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QStackedWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .plan_page import PlanPage
from .review_page import ReviewPage
from .stats_page import StatsPage
from .theme import Colors, truncate

GLYPH = {"done": "✓", "current": "▶", "todo": "○", "stub": "◌"}
COLOUR = {
    "done": Colors.success,
    "current": Colors.accent,
    "todo": Colors.muted,
    "stub": Colors.scroll,
}


class RoadmapTree(QTreeWidget):
    """Дерево «місяць → тема → задача» з позначками стану."""

    task_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(14)
        self.setAnimated(True)
        self.setUniformRowHeights(True)
        self._items: dict[str, QTreeWidgetItem] = {}
        self._stubs: set[str] = set()
        self.itemClicked.connect(self._on_clicked)

    def load(self, months, statuses: dict[str, str]) -> None:
        self.clear()
        self._items.clear()
        self._stubs.clear()

        for month in months:
            month_item = QTreeWidgetItem([month.title])
            month_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            month_item.setForeground(0, QBrush(QColor(Colors.text)))
            font = month_item.font(0)
            font.setBold(True)
            month_item.setFont(0, font)
            self.addTopLevelItem(month_item)

            for topic in month.topics:
                topic_item = QTreeWidgetItem([topic.title])
                topic_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                topic_item.setForeground(0, QBrush(QColor(Colors.muted)))
                month_item.addChild(topic_item)

                for task in topic.tasks:
                    state = "stub" if task.stub else statuses.get(task.id, "todo")
                    item = QTreeWidgetItem([f'{GLYPH[state]}  {truncate(task.title, 38)}'])
                    item.setData(0, Qt.ItemDataRole.UserRole, task.id)
                    item.setForeground(0, QBrush(QColor(COLOUR[state])))
                    if task.stub:
                        self._stubs.add(task.id)
                    item.setToolTip(
                        0,
                        f"{task.title}\n{task.level} · {task.base_xp} XP"
                        if not task.stub
                        else f"{task.title}\nзаплановано",
                    )
                    topic_item.addChild(item)
                    self._items[task.id] = item

        self.expandToDepth(1)

    def _state_of(self, task_id: str, statuses: dict[str, str]) -> str:
        """Пункт плану може бути позначкою-заглушкою або реальною задачею."""
        status = statuses.get(task_id, "todo")
        if task_id in self._stubs:
            return "done" if status == "done" else "stub"
        return status

    def _paint(self, item: QTreeWidgetItem, state: str) -> None:
        title = item.text(0)[3:]
        item.setText(0, f"{GLYPH[state]}  {title}")
        item.setForeground(0, QBrush(QColor(COLOUR[state])))

    def mark(self, task_id: str, status: str) -> None:
        item = self._items.get(task_id)
        if item is not None:
            self._paint(item, status)

    def apply_statuses(self, statuses: dict[str, str]) -> None:
        """Оновлює лише позначки — без перебудови дерева.

        Перебудова скидала б розкриті теми, позицію скролу й поточний пошук,
        а це саме те, що дратує під час роботи над задачею.
        """
        for task_id, item in self._items.items():
            self._paint(item, self._state_of(task_id, statuses))

    def select(self, task_id: str) -> None:
        item = self._items.get(task_id)
        if item is not None:
            self.setCurrentItem(item)
            self.scrollToItem(item)

    # ---------- пошук ----------

    def filter(self, query: str) -> int:
        """Ховає все, що не підходить під пошук. Повертає кількість задач."""
        query = query.strip().lower()
        found = 0

        for item in self._items.values():
            haystack = f"{item.text(0)} {item.toolTip(0)}".lower()
            match = not query or query in haystack
            item.setHidden(not match)
            if match:
                found += 1

        for month_index in range(self.topLevelItemCount()):
            month_item = self.topLevelItem(month_index)
            month_visible = False
            for topic_index in range(month_item.childCount()):
                topic_item = month_item.child(topic_index)
                topic_visible = any(
                    not topic_item.child(index).isHidden()
                    for index in range(topic_item.childCount())
                )
                topic_item.setHidden(not topic_visible)
                topic_item.setExpanded(topic_visible)
                month_visible = month_visible or topic_visible
            month_item.setHidden(not month_visible)
            month_item.setExpanded(month_visible)

        if not query:                      # повертаємо звичайний вигляд
            self.collapseAll()
            self.expandToDepth(1)

        return found

    def _on_clicked(self, item: QTreeWidgetItem) -> None:
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_selected.emit(task_id)


class SideNav(QWidget):
    """Колонка зліва: шапка з прогресом, перемикач режимів і сторінки."""

    task_selected = Signal(str)
    cold_review_requested = Signal()
    digest_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setMinimumWidth(260)
        self._plan_key: tuple[str, ...] | None = None

        self.tree = RoadmapTree()
        self.reviews = ReviewPage()
        self.stats = StatsPage()
        self.plan = PlanPage()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_switch())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_roadmap_page())
        self.stack.addWidget(self.reviews)
        self.stack.addWidget(self.stats)
        self.stack.addWidget(self.plan)
        layout.addWidget(self.stack, 1)

        self.tree.task_selected.connect(self.task_selected.emit)
        self.reviews.task_selected.connect(self.task_selected.emit)
        self.plan.task_selected.connect(self.task_selected.emit)
        self.reviews.cold_review_requested.connect(self.cold_review_requested.emit)
        self.stats.digest_requested.connect(self.digest_requested.emit)

    # ---------- шапка ----------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        box = QVBoxLayout(header)
        box.setContentsMargins(16, 14, 16, 12)
        box.setSpacing(4)

        brand = QHBoxLayout()
        brand.setSpacing(0)
        for text, name in (("Py", "BrandAccent"), ("Trainer", "Brand")):
            label = QLabel(text)
            label.setObjectName(name)
            brand.addWidget(label)
        brand.addStretch(1)
        box.addLayout(brand)

        caption = QLabel("Шлях: від нуля до перших грошей")
        caption.setObjectName("Subtle")
        box.addWidget(caption)
        box.addSpacing(6)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(8)
        box.addWidget(self.progress)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.progress_label = QLabel("0 із 0 пройдено")
        self.progress_label.setObjectName("Subtle")
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("Subtle")
        row.addWidget(self.progress_label)
        row.addStretch(1)
        row.addWidget(self.percent_label)
        box.addLayout(row)
        return header

    def _build_roadmap_page(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(10, 10, 10, 6)
        box.setSpacing(6)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук задачі…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._on_search)
        box.addWidget(self.search)

        self.search_note = QLabel("")
        self.search_note.setObjectName("Subtle")
        self.search_note.setVisible(False)
        box.addWidget(self.search_note)

        box.addWidget(self.tree, 1)
        return page

    def _on_search(self, text: str) -> None:
        found = self.tree.filter(text)
        if not text.strip():
            self.search_note.setVisible(False)
            return
        self.search_note.setText(f"Знайдено задач: {found}")
        self.search_note.setVisible(True)

    def _build_switch(self) -> QWidget:
        holder = QWidget()
        holder.setObjectName("Header")
        row = QHBoxLayout(holder)
        row.setContentsMargins(10, 6, 10, 8)
        row.setSpacing(4)

        # Підписи короткі навмисно: чотири кнопки у вузькому сайдбарі — і
        # довгі слова Qt обрізає многоточієм («Повторення» → «Повто...»).
        # Повну назву видно в підказці при наведенні.
        modes = (
            ("Шлях", "План від нуля до перших грошей"),
            ("Повтор", "Черга повторень: що час згадати"),
            ("Прогрес", "Скільки здано, XP, серія днів, слабкі місця"),
            ("План", "Що робити сьогодні — готовий план на вечір"),
        )
        self.nav_buttons: list[QToolButton] = []
        for index, (title, tip) in enumerate(modes):
            button = QToolButton()
            button.setObjectName("NavButton")
            button.setText(title)
            button.setToolTip(tip)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setChecked(index == 0)
            button.clicked.connect(lambda _=False, i=index: self.set_mode(i))
            row.addWidget(button)
            self.nav_buttons.append(button)
        return holder

    # ---------- API ----------

    def set_mode(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for position, button in enumerate(self.nav_buttons):
            button.setChecked(position == index)

    def load_curriculum(self, months, statuses: dict[str, str]) -> None:
        """Перше завантаження малює дерево, подальші — лише оновлюють позначки."""
        plan_key = tuple(
            task.id for month in months for topic in month.topics for task in topic.tasks
        )
        if plan_key == self._plan_key:
            self.tree.apply_statuses(statuses)
        else:
            self.tree.load(months, statuses)
            self._plan_key = plan_key
        self._apply_search()

    def _apply_search(self) -> None:
        """Після оновлення дерева пошук має лишитись застосованим."""
        query = self.search.text()
        if query.strip():
            self._on_search(query)

    def mark(self, task_id: str, status: str) -> None:
        self.tree.mark(task_id, status)

    def select(self, task_id: str) -> None:
        self.set_mode(0)
        self.tree.select(task_id)

    def set_progress(self, done: int, total: int) -> None:
        percent = round(done * 100 / total) if total else 0
        self.progress.setValue(percent)
        self.progress_label.setText(f"{done} із {total} пройдено")
        self.percent_label.setText(f"{percent}%")

    def set_reviews(self, due_rows: list[dict], later_rows: list[dict]) -> None:
        self.reviews.set_rows(due_rows, later_rows)
        total = len(due_rows)
        self.nav_buttons[1].setText(f"Повторення{' · ' + str(total) if total else ''}")
        self.nav_buttons[1].setToolTip(
            f"Час повторити: {total}" if total else "Черга повторень порожня"
        )

    def set_stats(self, overall: dict, weak: list, activity: dict[str, int],
                  xp: int, streak: int, active_seconds: float = 0.0,
                  xp_by_day: dict[str, int] | None = None) -> None:
        self.stats.set_data(overall, weak, activity, xp, streak, active_seconds,
                            xp_by_day)

    def set_digest_summary(self, digest) -> None:
        self.stats.set_digest_summary(digest)

    def set_plan(self, plan) -> None:
        self.plan.set_plan(plan)
        self.nav_buttons[3].setToolTip(
            f"План на сьогодні: {len(plan.steps)} кроків, ≈{plan.minutes} хв"
            if not plan.empty else "План на сьогодні порожній"
        )

    def set_mistakes(self, rows: list[dict]) -> None:
        self.reviews.set_mistakes(rows)
        self.nav_buttons[1].setToolTip(
            f"Повторень: {self.reviews.today_list.count()} · "
            f"помилок у журналі: {len(rows)}"
        )
