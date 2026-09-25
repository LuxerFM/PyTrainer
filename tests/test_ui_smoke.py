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
from trainer.ui.main_window import MainWindow  # noqa: E402
from trainer.ui.task_panel import TAB_HINTS  # noqa: E402
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
        """Журнал показує лише те, що ще варто виправити.

        Якщо задачу згодом здано — помилка вже не «висить», і тримати її
        в списку означало б плутати людину замість допомагати.
        """
        self.db.record_attempt("w1-hello", ok=False, with_checks=True,
                               failed_check="виводить привітання",
                               error_kind="NameError")
        self.window._refresh_all()
        self.assertEqual(self.window.sidebar.reviews.mistakes_list.count(), 1)

        self.db.mark_solved("w1-hello", 100)
        self.window._refresh_all()
        self.assertEqual(self.window.sidebar.reviews.mistakes_list.count(), 0)

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
