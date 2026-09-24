"""Smoke-тести інтерфейсу: вікно збирається, перевірка працює, прогрес пишеться.

Вікно не показується на екрані (QT_QPA_PLATFORM=offscreen), а база даних
створюється в тимчасовій папці — тому тести не чіпають реальний прогрес.
"""

import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox  # noqa: E402

from curriculum import find_task  # noqa: E402
from trainer.core.db import Database  # noqa: E402
from trainer.ui.main_window import MainWindow  # noqa: E402
from trainer.ui.theme import apply_theme  # noqa: E402


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.window = MainWindow(
            db=self.db, roadmap_path=Path(self.tmp.name) / "roadmap.md"
        )

    def tearDown(self):
        self.window.close()
        self.tmp.cleanup()

    def _wait_for_run(self) -> None:
        for _ in range(2000):
            self.app.processEvents()
            if not self.window._running:
                return
            time.sleep(0.01)
        self.fail("Запуск не завершився за відведений час")

    # ---------- базові ----------

    def test_opens_first_unfinished_task(self):
        self.assertEqual(self.window._task.id, "w1-hello")

    def test_stub_task_shows_placeholder(self):
        self.window.open_task("m5-bot-basic")
        self.assertIsNone(self.window._task)
        self.assertIn("тема попереду", self.window.status_msg.text())
        self.assertFalse(self.window.btn_check.isEnabled())

    def test_solution_hint_is_locked_at_start(self):
        self.window.open_task("w1-calc")
        locked = [
            widgets for widgets in self.window.panel._hint_widgets
            if widgets["hint"].solution
        ][0]
        self.assertFalse(locked["button"].isEnabled())
        self.assertIn("заблоковано", locked["button"].text())

    def test_solution_hint_unlocks_after_time(self):
        self.window.open_task("w1-calc")
        self.db.add_active_seconds("w1-calc", 20 * 60)
        self.window.panel.tick(20 * 60)
        unlocked = [
            widgets for widgets in self.window.panel._hint_widgets
            if widgets["hint"].solution
        ][0]
        self.assertTrue(unlocked["button"].isEnabled())

    # ---------- перевірка коду ----------

    def test_correct_solution_is_marked_done(self):
        self.window.editor.setPlainText('print("Привіт, світ!")\nprint("Мене звати Аня")')
        self.window.run_checks()
        self._wait_for_run()
        self.assertIn("здана", self.window.status_msg.text())
        self.assertEqual(self.db.status("w1-hello"), "done")
        self.assertGreater(self.db.total_xp(), 0)
        self.assertIn("XP ", self.window.xp_badge.text())

    def test_failed_task_goes_to_review_queue(self):
        self.window.run_checks()          # заготовка нічого не виводить
        self._wait_for_run()
        review = self.db.review("w1-hello")
        self.assertIsNotNone(review)
        # провал ставить повторення на завтра, тому сьогодні воно ще не «дозріло»
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

    def test_stdin_fixture_is_shown(self):
        self.window.open_task("w1-input")
        self.assertIn("Аня", self.window.stdin_label.text())

    # ---------- прогрес і роадмап ----------

    def test_progress_and_stats_update(self):
        self.db.mark_solved("w1-hello", 100)
        self.window._refresh_all()
        self.assertGreater(self.window.sidebar.progress.value(), 0)
        self.assertEqual(self.window.sidebar.stats.done_value.text().split("/")[0], "1")

    def test_code_is_kept_between_tasks(self):
        self.window.editor.setPlainText("# мій код")
        self.window.open_task("w1-vars")
        self.window.open_task("w1-hello")
        self.assertEqual(self.window.editor.toPlainText(), "# мій код")

    def test_roadmap_file_is_written(self):
        self.window.rewrite_roadmap()
        text = self.window.roadmap_path.read_text(encoding="utf-8")
        self.assertIn("МІСЯЦЬ 1", text)
        self.assertIn("Перший вивід: print()", text)

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
        self.assertFalse(self.window.sidebar.search_note.isVisible())

    # ---------- бейдж сьогоднішньої практики ----------

    def test_today_badge_counts_attempts(self):
        self.assertIn("Сьогодні: 0", self.window.today_badge.text())
        self.db.record_attempt("w1-hello", ok=False, with_checks=True)
        self.window._refresh_stats()
        self.assertIn("Сьогодні: 1 спроб", self.window.today_badge.text())

    # ---------- розв'язок і експорт ----------

    def test_use_solution_inserts_code_and_lowers_xp(self):
        original = QMessageBox.question
        QMessageBox.question = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )
        try:
            self.window.open_task("m2-math")
            solution_text = find_task("m2-math").solution_hint.text
            self.window._use_solution(solution_text)
        finally:
            QMessageBox.question = original

        self.assertIn("import math", self.window.editor.toPlainText())
        self.assertTrue(self.db.solution_used("m2-math"))
        self.assertLess(self.window._xp_now(find_task("m2-math")),
                        find_task("m2-math").base_xp)

    def test_export_solutions_writes_files(self):
        self.db.mark_solved("w1-hello", 100)
        self.db.save_code("w1-hello", 'print("Привіт, світ!")')

        empty, original_dialog = QMessageBox.information, QFileDialog.getExistingDirectory
        QMessageBox.information = staticmethod(lambda *args, **kwargs: None)
        QFileDialog.getExistingDirectory = staticmethod(lambda *args, **kwargs: self.tmp.name)
        try:
            self.window.export_solutions()
        finally:
            QMessageBox.information = empty
            QFileDialog.getExistingDirectory = original_dialog

        exported = Path(self.tmp.name) / "w1-hello.py"
        self.assertTrue(exported.exists())
        self.assertIn("Привіт, світ!", exported.read_text(encoding="utf-8"))
        self.assertIn("w1-hello.py", (Path(self.tmp.name) / "README.md").read_text(
            encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
