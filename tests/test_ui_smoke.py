"""Smoke-тести інтерфейсу: вікно збирається, перевірка працює, прогрес пишеться.

Вікно не показується на екрані (QT_QPA_PLATFORM=offscreen), а база даних,
роадмап і progress.json створюються в тимчасовій папці — тому тести не
чіпають реальний прогрес.
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
)

from curriculum import find_task, study_tasks, topic_of  # noqa: E402
from trainer.core.db import Database  # noqa: E402
from trainer.core.review import cold_seconds  # noqa: E402
from trainer.ui.main_window import MainWindow  # noqa: E402
from trainer.ui.task_panel import TAB_HINTS, TAB_REVIEW  # noqa: E402
from trainer.ui.theme import Colors, apply_theme, scale, set_scale  # noqa: E402


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name)
        self.db = Database(folder / "test.db")
        self.window = MainWindow(
            db=self.db,
            roadmap_path=folder / "roadmap.md",
            progress_path=folder / "progress.json",
            settings_path=None,       # тести не чіпають справжній pytrainer.ini
        )

    def tearDown(self):
        self.window.close()
        self.tmp.cleanup()

    # ---------- допоміжне ----------

    def _wait_for_run(self) -> None:
        for _ in range(2000):
            self.app.processEvents()
            if not self.window._running:
                return
            time.sleep(0.01)
        self.fail("Запуск не завершився за відведений час")

    def _answer_dialogs(self, answer=QMessageBox.StandardButton.Yes):
        original = QMessageBox.question
        QMessageBox.question = staticmethod(lambda *args, **kwargs: answer)
        self.addCleanup(lambda: setattr(QMessageBox, "question", original))

    def _check_cards(self) -> list:
        """Картки перевірок у вкладці «Тести» (без пружного відступу в кінці)."""
        box = self.window.panel.checks_box
        cards = []
        for index in range(box.count()):
            widget = box.itemAt(index).widget()
            if widget is not None:
                cards.append(widget)
        return cards

    def _review_text(self) -> str:
        """Увесь текст із карток розбору коду — щоб шукати в ньому підрядок."""
        parts = []
        for card in self.window.panel.review_cards:
            for label in card.findChildren(QLabel):
                parts.append(label.text())
            for button in card.findChildren(QPushButton):
                parts.append(button.text())
        return " | ".join(parts)

    SLOPPY = (
        "import math\n"
        "import random\n"
        "\n\n"
        "def AvgOfMarks(marks):\n"
        "    total = 0\n"
        "    for i in range(len(marks)):\n"
        "        total = total + marks[i]\n"
        "    avg = total / len(marks)\n"
        "    if avg == None:\n"
        "        return 0\n"
        "    if avg >= 4.5:\n"
        "        return True\n"
        "    else:\n"
        "        return False\n"
    )

    def _card_text(self) -> str:
        """Увесь текст із карток перевірок — щоб шукати в ньому підрядок."""
        parts = []
        for card in self._check_cards():
            for label in card.findChildren(QLabel):
                parts.append(label.text())
            for button in card.findChildren(QPushButton):
                parts.append(button.text())
        return " | ".join(parts)

    # ---------- базове ----------

    def test_opens_first_unfinished_task(self):
        self.assertEqual(self.window._task.id, "w1-hello")

    def test_stub_task_can_be_marked_manually(self):
        self.window.open_task("m2-git")
        self.assertIsNone(self.window._task)
        self.assertIn("познач галочкою", self.window.status_msg.text())

        self.window.panel.manual_toggle_requested.emit("m2-git")
        self.assertEqual(self.db.status("m2-git"), "done")
        self.assertIn("- [x] Git: перший коміт у своєму проєкті",
                      self.window.roadmap_path.read_text(encoding="utf-8"))

    def test_manual_milestone_can_be_unmarked(self):
        self.window.open_task("m2-pytest")
        self.window.toggle_manual_done("m2-pytest")
        self._answer_dialogs()
        self.window.toggle_manual_done("m2-pytest")
        self.assertEqual(self.db.status("m2-pytest"), "todo")

    def test_solution_hint_is_locked_at_start(self):
        self.window.open_task("w1-calc")
        locked = [widgets for widgets in self.window.panel._hint_widgets
                  if widgets["hint"].solution][0]
        self.assertFalse(locked["button"].isEnabled())
        self.assertIn("заблоковано", locked["button"].text())

    def test_solution_hint_unlocks_after_time(self):
        self.window.open_task("w1-calc")
        self.db.add_active_seconds("w1-calc", 20 * 60)
        self.window.panel.tick(20 * 60)
        unlocked = [widgets for widgets in self.window.panel._hint_widgets
                    if widgets["hint"].solution][0]
        self.assertTrue(unlocked["button"].isEnabled())
        self.assertFalse(unlocked["use_button"].isHidden())

    def test_stdin_fixture_is_shown(self):
        self.window.open_task("w1-input")
        self.assertIn("Аня", self.window.stdin_label.text())

    # ---------- розбір коду (вкладка «Рев'ю») ----------

    def test_review_tab_waits_until_there_is_something_to_review(self):
        self.assertEqual(self.window.panel.tabs.tabText(TAB_REVIEW), "Рев'ю")
        self.assertEqual(self.window.panel.review_cards, [])

        self.window.panel.review_requested.emit()

        self.assertIn("заготовка", self.window.panel.review_summary.text())
        self.assertEqual(self.window.panel.review_cards, [])

    def test_written_code_gets_remarks_with_line_buttons(self):
        self.window.editor.setPlainText(self.SLOPPY)

        self.window.review_current_code()

        self.assertEqual(self.window.panel.tabs.currentIndex(), TAB_REVIEW)
        self.assertEqual(self.window.panel.tabs.tabText(TAB_REVIEW), "Рев'ю · 6")
        text = self._review_text()
        for expected in ("Імпорт `math`", "не за домовленістю", "range(len",
                         "None", "return умова"):
            self.assertIn(expected, text)
        self.assertIn("6 зауважень", self.window.panel.review_summary.text())

    def test_line_button_moves_the_cursor(self):
        self.window.editor.setPlainText(self.SLOPPY)
        self.window.review_current_code()

        card = self.window.panel.review_cards[0]
        button = card.findChild(QPushButton)
        self.assertIn("Рядок 1", button.text())
        button.click()

        self.assertEqual(self.window.editor.textCursor().blockNumber(), 0)
        self.assertIn("Рядок 1", self.window.status_msg.text())

    def test_clean_code_earns_praise_not_remarks(self):
        self.window.editor.setPlainText(
            'def average_marks(marks):\n'
            '    """Середній бал."""\n'
            '    if not marks:\n'
            '        return None\n'
            '    return sum(marks) / len(marks)\n'
        )

        self.window.review_current_code()

        self.assertEqual(self.window.panel.tabs.tabText(TAB_REVIEW), "Рев'ю")
        self.assertIn("Жодних зауважень", self.window.panel.review_summary.text())
        self.assertIn("описана", self._review_text())

    def test_review_refreshes_itself_after_a_run(self):
        self.window.run_checks()          # у редакторі заготовка
        self._wait_for_run()
        self.assertIn("заготовка", self.window.panel.review_summary.text())

        self.window.editor.setPlainText("import random\nprint('готово')\n")
        self.window.run_code_only()
        self._wait_for_run()

        self.assertEqual(self.window.panel.tabs.tabText(TAB_REVIEW), "Рев'ю · 1")
        self.assertIn("random", self._review_text())

    def test_review_does_not_blame_imports_of_hidden_checks(self):
        """`BASE_URL` потрібний перевіркам — радити його прибрати не можна."""
        self.window.open_task("m3-http")
        self.window.editor.setPlainText(
            self.window._task.starter + "\nprint('перевіряю')\n"
        )

        self.window.review_current_code()

        self.assertNotIn("BASE_URL", self._review_text())

    def test_switching_task_forgets_the_previous_review(self):
        self.window.editor.setPlainText("import random\nprint('готово')\n")
        self.window.review_current_code()
        self.assertEqual(self.window.panel.tabs.tabText(TAB_REVIEW), "Рев'ю · 1")

        self.window.open_task("w2-for")

        self.assertEqual(self.window.panel.tabs.tabText(TAB_REVIEW), "Рев'ю")
        self.assertEqual(self.window.panel.review_cards, [])
        self.assertIn("Натисни", self.window.panel.review_summary.text())

    # ---------- холодне повторення ----------

    def _solve(self, task_id: str, *, due_in: int | None = None) -> None:
        """Здає задачу без вікна — так, як це зробив би тренажер."""
        self.db.mark_solved(task_id, 100)
        self.db.add_active_seconds(task_id, 600)
        if due_in is not None:
            self.db.schedule_review(task_id, due_in, 0)
        self.window._refresh_all()

    def test_cold_review_starts_from_the_stub_with_hints_locked(self):
        self.window.open_task("w2-for")   # щоб здана задача не була відкритою
        self._solve("w1-hello")
        saved = "print('мій розвʼязок')"
        self.db.save_code("w1-hello", saved)

        self.window.start_cold_review()

        self.assertTrue(self.window._review_mode)
        self.assertEqual(self.window._task.id, "w1-hello")
        self.assertEqual(self.window.editor.toPlainText(),
                         find_task("w1-hello").starter)
        self.assertTrue(self.window.panel.locked)
        self.assertFalse(self.window.panel.cold_note.isHidden())
        self.assertFalse(self.window.btn_hint.isEnabled())
        self.assertEqual(self.window.panel.tabs.tabText(TAB_HINTS), "Підказки 🔒")
        self.assertEqual(self.window._cold_left, cold_seconds(self.window._task))
        self.assertIn("Холодне повторення", self.window.timer_label.text())
        self.assertIn("випадкова зі зданих", self.window.status_msg.text())
        for widgets in self.window.panel._hint_widgets:
            self.assertFalse(widgets["button"].isEnabled())

    def test_cold_review_does_not_reveal_previously_used_hints(self):
        self._solve("w1-input")
        self.db.reveal_hint("w1-input", 3)

        self.window.start_cold_review()

        self.assertTrue(self.window.panel._hint_widgets)
        self.assertFalse(any(widgets["button"].isChecked()
                             for widgets in self.window.panel._hint_widgets))
        self.assertTrue(all(widgets["text"].isHidden()
                            for widgets in self.window.panel._hint_widgets))

    def test_cold_review_button_sits_on_the_review_page(self):
        self.window.open_task("w2-for")
        self._solve("w1-hello")
        self.window.sidebar.reviews.cold_review_requested.emit()
        self.assertTrue(self.window._review_mode)
        self.assertEqual(self.window._task.id, "w1-hello")

    def test_cold_review_without_solved_tasks_explains_itself(self):
        task_id = self.window._task.id
        self.window.start_cold_review()
        self.assertFalse(self.window._review_mode)
        self.assertEqual(self.window._task.id, task_id)
        self.assertIn("зданих задач", self.window.status_msg.text())

    def test_cold_review_prefers_the_due_queue(self):
        self._solve("w1-hello")             # здана, але не в черзі
        self._solve("w1-vars", due_in=0)    # час повторювати вже сьогодні

        self.window.start_cold_review()

        self.assertEqual(self.window._task.id, "w1-vars")
        self.assertIn("з черги повторень", self.window.status_msg.text())

    def test_cold_clock_counts_down_then_stops_at_zero(self):
        self.window.open_task("w2-for")
        self._solve("w1-hello")
        self.window.start_cold_review()
        limit = cold_seconds(self.window._task)

        self.window._advance_cold(60)
        self.assertEqual(self.window._cold_left, limit - 60)
        self.assertIn("лишилось", self.window.timer_label.text())

        self.window._advance_cold(limit)
        self.assertEqual(self.window._cold_left, 0)
        self.assertIn("час вийшов", self.window.timer_label.text())

    def test_failed_cold_review_queues_task_and_keeps_the_saved_code(self):
        self._solve("w1-vars")
        saved = "print('код, який шкода втратити')"
        self.db.save_code("w1-vars", saved)

        self.window.start_cold_review()
        self.window.run_checks()          # у редакторі заготовка → не пройде
        self._wait_for_run()

        self.assertEqual(self.db.saved_code("w1-vars"), saved)
        review = self.db.review("w1-vars")
        self.assertIsNotNone(review, "провал має повернути задачу в чергу")
        self.assertEqual(review["interval_index"], 0)
        self.assertFalse(self.window._review_mode)
        self.assertFalse(self.window.panel.locked)
        self.assertTrue(self.window.btn_hint.isEnabled())
        self.assertIn("не згадав", self.window.console.toPlainText())

    def test_cold_review_pass_moves_the_queue_forward(self):
        self._solve("w2-for", due_in=0)

        self.window.start_cold_review()
        self.assertEqual(self.window._task.id, "w2-for")
        self.window.editor.setPlainText(find_task("w2-for").solution_hint.text)
        self.window.run_checks()
        self._wait_for_run()

        self.assertEqual(self.db.review("w2-for")["interval_index"], 1)
        self.assertGreater(self.db.bonus_xp("w2-for"), 0)
        self.assertIn("бонус за повторення", self.window.console.toPlainText())
        self.assertIn("Холодне повторення: згадав", self.window.console.toPlainText())

    def test_cold_review_survives_a_theme_switch(self):
        """Ctrl+D посеред спроби не має стирати написане й обнуляти таймер.

        У холодному повторенні код не зберігається в базу — тому перемальовку
        вікна він має пережити в редакторі.
        """
        self.window.open_task("w2-for")
        self._solve("w1-hello")
        self.window.start_cold_review()
        self.window.editor.setPlainText("print('почав згадувати')")
        self.window._advance_cold(120)
        left = self.window._cold_left

        self.window.toggle_theme()

        self.assertTrue(self.window._review_mode)
        self.assertEqual(self.window.editor.toPlainText(), "print('почав згадувати')")
        self.assertEqual(self.window._cold_left, left)
        self.assertTrue(self.window.panel.locked)
        self.assertFalse(self.window.btn_hint.isEnabled())
        self.window.toggle_theme()      # повертаємо тему, як було

    def test_cold_review_of_mastered_task_keeps_it_mastered(self):
        self.window.open_task("w2-for")          # щоб w1-hello не був відкритою
        self._solve("w1-hello")                  # здана чисто, поза чергою

        self.window.start_cold_review()
        self.assertEqual(self.window._task.id, "w1-hello")
        self.window.editor.setPlainText(find_task("w1-hello").solution_hint.text)
        self.window.run_checks()
        self._wait_for_run()

        self.assertIsNone(self.db.review("w1-hello"))
        self.assertTrue(self.window.session.is_mastered("w1-hello"))
        self.assertGreater(self.db.bonus_xp("w1-hello"), 0)

    def test_task_with_files_shows_them(self):
        self.window.open_task("m2-module")
        self.assertIn("utils.py", self.window.stdin_label.text())

    # ---------- перевірка коду ----------

    def test_correct_solution_is_marked_done(self):
        self.window.editor.setPlainText('print("Привіт, світ!")\nprint("Мене звати Аня")')
        self.window.run_checks()
        self._wait_for_run()
        self.assertIn("здана", self.window.status_msg.text())
        self.assertEqual(self.db.status("w1-hello"), "done")
        self.assertGreater(self.db.total_xp(), 0)

    def test_failed_task_goes_to_review_queue(self):
        self.window.run_checks()          # заготовка нічого не виводить
        self._wait_for_run()
        review = self.db.review("w1-hello")
        self.assertIsNotNone(review)
        self.assertEqual(review["interval_index"], 0)
        self.assertEqual(self.window.sidebar.reviews.later_list.count(), 1)

    def test_due_review_is_shown_in_badge(self):
        self.window.run_checks()
        self._wait_for_run()
        self.db.connection.execute(
            "UPDATE reviews SET due_date = DATE('now') WHERE task_id = 'w1-hello'"
        )
        self.db.connection.commit()
        self.window._refresh_reviews()
        self.assertIn("На повторення: 1", self.window.review_badge.text())
        self.assertEqual(self.window.sidebar.reviews.today_list.count(), 1)

    def test_hint_reduces_xp(self):
        self.window.editor.setPlainText('print("Привіт, світ!")\nprint("Мене звати Аня")')
        self.window.panel.hint_revealed.emit(1, False)
        self.window.run_checks()
        self._wait_for_run()
        self.assertEqual(self.db.best_xp("w1-hello"), 85)

    def test_runner_gets_task_files(self):
        """Задача з файлами: розв'язок імпортує utils.py із тієї ж папки."""
        self.window.open_task("m2-module")
        solution = find_task("m2-module").solution_hint.text
        self.window.editor.setPlainText(solution)
        self.window.run_checks()
        self._wait_for_run()
        self.assertIn("здана", self.window.status_msg.text())

    # ---------- інформаційний шар ----------

    def test_planned_checks_are_listed_before_running(self):
        """До запуску видно, ЩО перевірять — але не сам код тесту."""
        self.window.open_task("w1-hello")
        self.assertEqual(len(self._check_cards()), 2)
        self.assertIn("ще не запускались", self.window.panel.tests_summary.text())
        self.assertIn("Привіт", self._card_text())
        self.assertIn("приховані", self.window.panel.tests_detail.text())

    def test_checks_show_results_after_failure(self):
        self.window.run_checks()          # заготовка нічого не виводить
        self._wait_for_run()
        self.assertIn("0 із 2", self.window.panel.tests_summary.text())
        self.assertIn("✕", self._card_text())

    def test_all_checks_pass_after_correct_solution(self):
        self.window.editor.setPlainText(
            'print("Привіт, світ!")\nprint("Мене звати Аня")'
        )
        self.window.run_checks()
        self._wait_for_run()
        self.assertIn("✓", self._card_text())
        self.assertNotIn("✕", self._card_text())

    def test_error_advice_explains_the_exception(self):
        """NameError має бути пояснений українською, а не лише в traceback."""
        self.window.editor.setPlainText("print(змінна_якої_немає)")
        self.window.run_code_only()
        self._wait_for_run()
        self.assertIn("Код впав з помилкою", self.window.panel.tests_summary.text())
        self.assertIn("NameError", self._card_text())
        self.assertIn("Що робити", self._card_text())

    def test_task_position_and_time_are_shown(self):
        self.window.open_task("w1-hello")
        meta = self.window.panel.meta_label.text()
        self.assertIn("Задача 1 із", meta)
        self.assertIn("хв", meta)

    def test_cheatsheet_is_picked_for_the_topic(self):
        self.window.open_task("m3-lc-two-sum")
        self.assertEqual(
            self.window.panel.sheet_picker.currentText(),
            "Словники (dict) і множини (set)",
        )
        self.assertTrue(self.window.panel.sheet_view.toPlainText().strip())

    def test_cheatsheet_switch_does_not_change_the_task(self):
        self.window.open_task("w1-hello")
        self.window.panel.sheet_picker.setCurrentIndex(0)   # «Основи»
        self.assertEqual(self.window.panel.sheet_picker.currentText()[:6], "Основи")
        self.assertEqual(self.window._task.id, "w1-hello")

    def test_manual_milestone_gets_a_relevant_sheet(self):
        self.window.open_task("m2-git")
        self.assertIn("Git", self.window.panel.sheet_picker.currentText())

    def test_hints_tab_index_is_used_by_toolbar(self):
        self.window.open_hints_tab()
        self.assertEqual(self.window.panel.tabs.currentIndex(), TAB_HINTS)
        self.assertEqual(self.window.panel.tabs.tabText(TAB_HINTS), "Підказки")

    # ---------- план на сьогодні ----------

    def test_plan_page_shows_steps(self):
        plan = self.window.sidebar.plan
        self.assertGreater(plan.steps.count(), 0)
        self.assertIn("План на сьогодні", plan.summary.text())
        self.assertIn("кроків", plan.summary.text())

    def test_plan_step_opens_its_task(self):
        item = self.window.sidebar.plan.steps.item(0)
        task_id = item.data(Qt.ItemDataRole.UserRole)
        self.window.sidebar.plan._on_clicked(item)
        self.assertEqual(self.window._task.id, task_id)

    def test_plan_reacts_to_a_solved_task(self):
        first = self.window.sidebar.plan.steps.item(0).data(Qt.ItemDataRole.UserRole)
        self.db.mark_solved(first, 100)
        self.window._refresh_all()
        ids = [self.window.sidebar.plan.steps.item(index).data(Qt.ItemDataRole.UserRole)
               for index in range(self.window.sidebar.plan.steps.count())]
        self.assertNotIn(first, ids)

    def test_all_solved_gives_an_empty_plan(self):
        for task in study_tasks():
            self.db.mark_solved(task.id, 100)
        self.window._refresh_all()
        self.assertEqual(self.window.sidebar.plan.steps.count(), 0)
        self.assertTrue(self.window.sidebar.plan.empty.isVisible()
                        or not self.window.sidebar.plan.isVisible())

    # ---------- журнал помилок і перехід до рядка ----------

    def test_failed_run_lands_in_the_mistake_log(self):
        self.window.open_task("m3-lc-two-sum")   # задача ще не здана
        self.window.editor.setPlainText(
            "def two_sum(numbers, target):\n    return number\n"
        )
        self.window.run_checks()
        self._wait_for_run()

        self.assertEqual(self.window.sidebar.reviews.mistakes_list.count(), 1)
        text = self.window.sidebar.reviews.mistakes_list.item(0).text()
        self.assertIn("NameError", text)
        self.assertIn("Two Sum", text)

    def test_jump_button_points_at_the_broken_line(self):
        self.window.open_task("m3-lc-two-sum")
        self.window.editor.setPlainText(
            "def two_sum(numbers, target):\n    return number\n"
        )
        self.window.run_checks()
        self._wait_for_run()

        self.assertEqual(self.window.panel.jump_line, 2)
        self.assertIn("Перейти до рядка 2", self._card_text())

        self.window.panel.jump_to_line_requested.emit(self.window.panel.jump_line)
        cursor = self.window.editor.textCursor()
        self.assertEqual(cursor.blockNumber(), 1)          # рядок 2 — індекс 1
        self.assertEqual(cursor.selectedText(), "    return number")

    def test_jump_button_is_absent_for_a_plain_wrong_answer(self):
        self.window.open_task("m3-lc-two-sum")
        self.window.editor.setPlainText(
            "def two_sum(numbers, target):\n    return [0, 0]\n"
        )
        self.window.run_checks()
        self._wait_for_run()
        self.assertEqual(self.window.panel.jump_line, 0)
        self.assertNotIn("Перейти до рядка", self._card_text())

    def test_solved_task_leaves_the_mistake_log(self):
        """Галочка «зроблено поза тренажером» закриває помилку.

        Задачу могли розв'язати в своєму редакторі — тримати її в списку
        означало б плутати людину замість допомагати.
        """
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               failed_check="виводить привітання",
                               error_kind="NameError")
        self.window._refresh_all()
        self.assertEqual(self.window.sidebar.reviews.mistakes_list.count(), 1)

        self.db.mark_solved("w1-hello", 100)
        self.window._refresh_all()
        self.assertEqual(self.window.sidebar.reviews.mistakes_list.count(), 0)

    def test_mistake_closed_with_help_stays_visible(self):
        """«Здав» і «здав сам» — різні речі: підказка лишає помилку в списку.

        Раніше задача, здана з підказкою, зникала з журналу разом із
        проблемою, яку ще варто повторити.
        """
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               failed_check="виводить привітання",
                               error_kind="NameError")
        self.db.reveal_hint("w1-hello", 1)
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=50,
                               clean=False)
        self.db.mark_solved("w1-hello", 100)
        self.window._refresh_all()

        widget = self.window.sidebar.reviews.mistakes_list
        self.assertEqual(widget.count(), 1)
        self.assertIn("закрито з допомогою", widget.item(0).text())
        self.assertIn("холодним повторенням",
                      self.window.sidebar.reviews.mistakes_note.text())

    def test_clean_pass_removes_the_mistake(self):
        """А чистий прохід — справжнє закриття: без підказок, без розв'язку."""
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               failed_check="виводить привітання",
                               error_kind="NameError")
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100,
                               clean=True)
        self.db.mark_solved("w1-hello", 100)
        self.window._refresh_all()
        self.assertEqual(self.window.sidebar.reviews.mistakes_list.count(), 0)

    def test_open_mistake_is_listed_before_a_helped_one(self):
        """Спершу те, що ще висить; жовте — після нього, щоб не затуляло."""
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               error_kind="NameError")
        self.db.record_attempt("w1-vars", ok=False, with_checks=True,
                               error_kind="SyntaxError")
        self.db.reveal_hint("w1-vars", 1)
        self.db.record_attempt("w1-vars", ok=True, with_checks=True, clean=False)
        self.db.mark_solved("w1-vars", 100)
        self.window._refresh_all()

        widget = self.window.sidebar.reviews.mistakes_list
        self.assertEqual(widget.count(), 2)
        self.assertIn("Перший вивід", widget.item(0).text())
        self.assertIn("Змінні", widget.item(1).text())

    # ---------- тижневий огляд ----------

    def test_stats_page_has_the_digest_entry(self):
        stats = self.window.sidebar.stats
        self.assertIn("занять ще не було", stats.digest_line.text())

        stats.digest_button.click()
        self.assertIsNotNone(self.window.digest_dialog)
        self.assertFalse(self.window.digest_dialog.isHidden())

    def test_digest_shows_the_week_numbers(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100,
                               clean=True)
        self.db.mark_solved("w1-hello", 100)
        self.window.show_digest()

        dialog = self.window.digest_dialog
        self.assertIn("Тиждень", dialog.title.text())
        self.assertEqual(dialog.cards["checks"].text(), "1")
        self.assertEqual(dialog.cards["passes"].text(), "1")
        self.assertEqual(dialog.cards["solved"].text(), "1")
        solved = dialog.solved_list.item(0).text()
        self.assertIn(find_task("w1-hello").title, solved)

    def test_digest_is_reused_and_refreshed(self):
        """Вікно не плодиться, а цифри в ньому не застигають."""
        self.window.show_digest()
        first = self.window.digest_dialog
        self.assertEqual(first.cards["checks"].text(), "0")

        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100,
                               clean=True)
        self.window._refresh_all()
        self.window.show_digest()

        self.assertIs(first, self.window.digest_dialog)
        self.assertEqual(first.cards["checks"].text(), "1")
        self.assertIn("1 перевірка", self.window.sidebar.stats.digest_line.text())

    def test_digest_row_click_opens_the_task(self):
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               failed_check="виводить привітання",
                               error_kind="NameError")
        self.window.open_task("w1-vars")
        self.window.show_digest()

        dialog = self.window.digest_dialog
        dialog.mistakes_list.itemClicked.emit(dialog.mistakes_list.item(0))

        self.assertEqual(self.window._task.id, "w1-hello")
        self.assertIsNone(self.window.digest_dialog)     # вікно відступило

    def test_digest_actions_include_due_reviews_and_tolerate_a_click(self):
        """Рядок «повторити» не веде до конкретної задачі — і не має падати."""
        today = self.db.connection.execute(
            "SELECT DATE('now') AS day"
        ).fetchone()["day"]
        self.db.connection.execute(
            "INSERT OR REPLACE INTO reviews (task_id, due_date, interval_index,"
            " updated_at) VALUES ('w1-hello', ?, 0, ?)",
            (today, f"{today} 20:00:00"),
        )
        self.db.connection.commit()
        self.window.show_digest()

        dialog = self.window.digest_dialog
        rows = [dialog.actions_list.item(index)
                for index in range(dialog.actions_list.count())]
        review_row = [row for row in rows if "Повторити" in row.text()]
        self.assertEqual(len(review_row), 1)

        dialog._on_clicked(review_row[0])
        self.assertIsNotNone(self.window.digest_dialog)   # вікно лишилось

    def test_digest_offers_a_task_from_the_weakest_topic(self):
        """Огляд не лише констатує слабку тему, а дає задачу для неї."""
        for _ in range(3):
            self.db.record_attempt("w1-arith", ok=False, with_checks=True,
                                   error_kind="SyntaxError")
        self.window.show_digest()

        rows = [self.window.digest_dialog.actions_list.item(index).text()
                for index in range(self.window.digest_dialog.actions_list.count())]
        weak = [row for row in rows if "Слабка тема" in row]
        self.assertEqual(len(weak), 1)
        self.assertIn(topic_of("w1-arith"), weak[0])
        self.assertIn(find_task("w1-hello").title, weak[0])

    def test_digest_tolerates_a_mistake_from_an_unknown_task(self):
        """У журналі могла лишитись задача, якої вже немає в курсі."""
        self.db.record_attempt("gone-task", ok=False, with_checks=True,
                               error_kind="NameError")
        self.window.show_digest()
        row = self.window.digest_dialog.mistakes_list.item(0).text()
        self.assertIn("gone-task", row)

    def test_digest_report_saves_to_a_file(self):
        self.window.show_digest()
        target = Path(self.tmp.name) / "week.md"
        original = QFileDialog.getSaveFileName
        QFileDialog.getSaveFileName = staticmethod(lambda *args, **kwargs: (str(target), ""))
        try:
            self.window.digest_dialog.save_report()
        finally:
            QFileDialog.getSaveFileName = original

        self.assertTrue(target.exists())
        saved = target.read_text(encoding="utf-8")
        self.assertIn("Тиждень", saved)
        self.assertIn("## Що робити далі", saved)
        self.assertEqual(self.window.digest_dialog.saved_note.text(),
                         "Збережено: week.md")

    def test_digest_save_can_be_cancelled(self):
        self.window.show_digest()
        original = QFileDialog.getSaveFileName
        QFileDialog.getSaveFileName = staticmethod(lambda *args, **kwargs: ("", ""))
        try:
            self.window.digest_dialog.save_report()
        finally:
            QFileDialog.getSaveFileName = original
        self.assertEqual(self.window.digest_dialog.saved_note.text(), "")

    def test_digest_save_reports_an_unwritable_path(self):
        self.window.show_digest()
        warnings = []
        warn = QMessageBox.warning
        QMessageBox.warning = staticmethod(lambda *args, **kwargs: warnings.append(args))
        original = QFileDialog.getSaveFileName
        QFileDialog.getSaveFileName = staticmethod(
            lambda *args, **kwargs: (self.tmp.name, "")   # тека, а не файл
        )
        try:
            self.window.digest_dialog.save_report()
        finally:
            QFileDialog.getSaveFileName = original
            QMessageBox.warning = warn

        self.assertTrue(warnings, "про невдалий запис ніхто не сказав")
        self.assertEqual(self.window.digest_dialog.saved_note.text(), "")

    # ---------- слабкі теми й графік ----------

    def test_weak_topic_click_opens_practice_task(self):
        for _ in range(3):
            self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                                   error_kind="NameError")
        self.window._refresh_all()

        weak = self.window.sidebar.stats.weak_list
        self.assertTrue(weak.count(), "слабка тема не з'явилась")
        topic = weak.item(0).data(Qt.ItemDataRole.UserRole)
        self.window.sidebar.stats._on_weak_clicked(weak.item(0))

        self.assertEqual(self.window.sidebar.stack.currentIndex(), 0)
        self.assertEqual(topic_of(self.window._task.id), topic)

    def test_xp_chart_receives_the_history(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.window._refresh_stats()
        chart = self.window.sidebar.stats.xp_chart
        self.assertEqual(sum(chart._by_day.values()), 100)
        self.assertEqual(len(chart._days()), chart.DAYS)

    # ---------- стан інтерфейсу ----------

    def test_refresh_keeps_search_and_expansion(self):
        self.window.sidebar.search.setText("словник")
        self.window.sidebar.tree.expandAll()
        self.window._refresh_all()

        visible_titles = [
            item.text(0).lower() for item in self.window.sidebar.tree._items.values()
            if not item.isHidden()
        ]
        self.assertTrue(visible_titles)
        self.assertTrue(all("словник" in title for title in visible_titles),
                        visible_titles)
        self.assertIn("Знайдено задач", self.window.sidebar.search_note.text())
        # і дерево справді лишилось розкритим, а не згорнулось у корінь
        self.assertTrue(self.window.sidebar.tree._items["w3-dict"].parent().isExpanded())

    def test_code_is_kept_between_tasks(self):
        self.window.editor.setPlainText("# мій код")
        self.window.open_task("w1-vars")
        self.window.open_task("w1-hello")
        self.assertEqual(self.window.editor.toPlainText(), "# мій код")

    def test_autosave_writes_code_on_tick(self):
        self.window.editor.setPlainText("# чернетка")
        self.window.activateWindow()          # _tick працює лише для активного вікна
        self.window._running = False
        self.db.save_code("w1-hello", "старе")   # імітуємо, що в базі давніший код
        self.window._last_saved = "старе"
        self.window.isActiveWindow = lambda: True  # у тестах вікно не має фокуса
        self.window._tick()
        self.assertEqual(self.db.saved_code("w1-hello"), "# чернетка")

    # ---------- прогрес, роадмап, статистика ----------

    def test_progress_and_stats_update(self):
        self.db.mark_solved("w1-hello", 100)
        self.window._refresh_all()
        self.assertGreater(self.window.sidebar.progress.value(), 0)
        self.assertEqual(self.window.sidebar.stats.cards["done"].text().split("/")[0], "1")
        self.assertEqual(self.window.sidebar.stats.cards["mastered"].text(), "1")

    def test_roadmap_file_is_written(self):
        self.window.rewrite_roadmap()
        text = self.window.roadmap_path.read_text(encoding="utf-8")
        self.assertIn("МІСЯЦЬ 1", text)
        self.assertIn("Перший вивід: print()", text)

    def test_progress_file_is_written(self):
        self.db.record_attempt("w1-hello", ok=True, with_checks=True, xp=100)
        self.db.mark_solved("w1-hello", 100)
        self.window._write_progress()
        data = json.loads(self.window.progress_path.read_text(encoding="utf-8"))
        self.assertEqual(data["progress"][0]["task_id"], "w1-hello")
        self.assertEqual(data["progress"][0]["status"], "done")

    def test_progress_writes_are_throttled_but_force_writes(self):
        self.db.mark_solved("w1-hello", 100)
        self.window._write_progress()
        first = self.window.progress_path.read_text(encoding="utf-8")
        self.assertIn("w1-hello", first)

        self.db.mark_solved("w1-vars", 85)
        self.window._write_progress()
        self.assertEqual(
            self.window.progress_path.read_text(encoding="utf-8"), first,
            "другий запис поспіль має пропуститись — дзеркала пишуться рідко",
        )

        self.window._write_progress(force=True)
        self.assertIn(
            "w1-vars",
            self.window.progress_path.read_text(encoding="utf-8"),
        )

    def test_progress_roundtrip_restores_state(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.mark_solved("w1-vars", 85)
        snapshot = self.db.snapshot()

        fresh = Database(Path(self.tmp.name) / "fresh.db")
        try:
            restored = fresh.restore(snapshot)
            self.assertEqual(restored, 2)
            self.assertEqual(fresh.status("w1-hello"), "done")
            self.assertEqual(fresh.total_xp(), 185)
        finally:
            fresh.close()   # закриваємо до прибирання тимчасової папки (Windows)

    def test_export_solutions_writes_files(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.save_code("w1-hello", 'print("Привіт, світ!")')

        empty = QMessageBox.information
        QMessageBox.information = staticmethod(lambda *args, **kwargs: None)
        original_dialog = QFileDialog.getExistingDirectory
        QFileDialog.getExistingDirectory = staticmethod(
            lambda *args, **kwargs: self.tmp.name
        )
        try:
            self.window.export_solutions()
        finally:
            QMessageBox.information = empty
            QFileDialog.getExistingDirectory = original_dialog

        exported = Path(self.tmp.name) / "w1-hello.py"
        self.assertTrue(exported.exists())
        self.assertIn("Привіт, світ!", exported.read_text(encoding="utf-8"))

    # ---------- пошук ----------

    def test_search_filters_the_tree(self):
        self.window.sidebar.search.setText("SQL")
        found = self.window.sidebar.tree.filter("SQL")
        self.assertGreaterEqual(found, 1)
        self.assertIn("Знайдено задач", self.window.sidebar.search_note.text())

    def test_search_restores_all_tasks_when_cleared(self):
        self.window.sidebar.search.setText("SQL")
        total = self.window.sidebar.tree.filter("")
        self.assertGreaterEqual(total, 60)

    # ---------- стан вікна, тема, шрифт ----------

    def test_state_is_remembered_between_runs(self):
        """Закрив — і наступного разу та сама задача, тема й масштаб."""
        settings = Path(self.tmp.name) / "settings.ini"
        self.addCleanup(self._restore_theme)       # тема змінюється для всього застосунку

        def make_window():
            return MainWindow(
                db=Database(Path(self.tmp.name) / "state.db"),
                roadmap_path=Path(self.tmp.name) / "roadmap.md",
                progress_path=Path(self.tmp.name) / "progress.json",
                settings_path=settings,
            )

        first = make_window()
        first.open_task("w1-vars")
        first.toggle_theme()                       # світла тема
        first.change_font_scale(0.1)
        first.sidebar.set_mode(2)
        first.panel.tabs.setCurrentIndex(1)
        first.close()                              # тут стан і зберігається

        second = make_window()
        try:
            self.assertEqual(second._task.id, "w1-vars")
            self.assertEqual(Colors.name, "light")
            self.assertAlmostEqual(scale(), 1.1, places=2)
            self.assertEqual(second.sidebar.stack.currentIndex(), 2)
            self.assertEqual(second.panel.tabs.currentIndex(), 1)
        finally:
            second.close()          # закриває базу до прибирання тимчасової папки

    def test_theme_toggle_keeps_working(self):
        original = Colors.name
        self.addCleanup(self._restore_theme)

        self.window.toggle_theme()
        self.assertNotEqual(Colors.name, original)
        self.assertTrue(self.window.panel.statement.toHtml().strip())

        self.window.toggle_theme()
        self.assertEqual(Colors.name, original)

    def test_font_scale_changes_the_editor_font(self):
        self.addCleanup(self._restore_theme)
        before = self.window.editor.font().pointSize()
        self.window.change_font_scale(0.15)
        self.assertGreater(self.window.editor.font().pointSize(), before)

    def _restore_theme(self) -> None:
        Colors.use("dark")
        set_scale(1.0)
        apply_theme(self.app)

    # ---------- бейдж практики ----------

    def test_today_badge_counts_activity(self):
        self.assertIn("Сьогодні: 0", self.window.today_badge.text())
        self.db.record_attempt("w1-hello", ok=False, with_checks=True)
        self.window._refresh_stats()
        self.assertIn("Сьогодні: 1 запусків", self.window.today_badge.text())


if __name__ == "__main__":
    unittest.main()
