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
        folder = Path(self.tmp.name)
        self.db = Database(folder / "test.db")
        self.window = MainWindow(
            db=self.db,
            roadmap_path=folder / "roadmap.md",
            progress_path=folder / "progress.json",
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

    # ---------- бейдж практики ----------

    def test_today_badge_counts_activity(self):
        self.assertIn("Сьогодні: 0", self.window.today_badge.text())
        self.db.record_attempt("w1-hello", ok=False, with_checks=True)
        self.window._refresh_stats()
        self.assertIn("Сьогодні: 1 запусків", self.window.today_badge.text())


if __name__ == "__main__":
    unittest.main()
