"""Тести тижневого огляду: що саме потрапляє у звіт і як він читається.

Дати тут задаються явно — інакше тест «за останні сім днів» залежав би від
дня, коли його запустили, і кожен понеділок падав би сам по собі.
"""

import unittest
from datetime import date, datetime

from curriculum import find_task, study_tasks, topic_of
from trainer.core.db import Database
from trainer.core.digest import DAYS, weekly_digest, write_digest

TODAY = date(2026, 9, 26)          # субота; тиждень виходить 20–26 вересня


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    # ---------- допоміжне ----------

    def attempt(self, task_id: str, day: str, ok: bool, *, kind: str = "",
                checks: bool = True, clean: bool = False, xp: int = 0) -> None:
        """Записує спробу із заданою датою — минулі тижні інакше не перевірити."""
        self.db.mark_in_progress(task_id)
        self.db.connection.execute(
            """
            INSERT INTO attempts
                (task_id, created_at, ok, with_checks, clean, xp,
                 failed_check, error_kind)
            VALUES (?, ?, ?, ?, ?, ?, '', ?)
            """,
            (task_id, f"{day} 20:00:00", 1 if ok else 0, 1 if checks else 0,
             1 if clean else 0, xp, kind),
        )
        self.db.connection.commit()

    def solved(self, task_id: str, day: str) -> None:
        self.db.mark_in_progress(task_id)
        self.db.connection.execute(
            "UPDATE progress SET status = 'done', solved_at = ? WHERE task_id = ?",
            (f"{day} 21:00:00", task_id),
        )
        self.db.connection.commit()

    def due_review(self, task_id: str, day: str) -> None:
        self.db.connection.execute(
            "INSERT OR REPLACE INTO reviews (task_id, due_date, interval_index,"
            " updated_at) VALUES (?, ?, 0, ?)",
            (task_id, day, f"{day} 20:00:00"),
        )
        self.db.connection.commit()

    # ---------- порожній тиждень ----------

    def test_empty_week_is_honest_not_broken(self):
        digest = weekly_digest(self.db, today=TODAY)
        self.assertFalse(digest.active)
        self.assertEqual(digest.checks, 0)
        self.assertEqual(digest.solved, [])
        self.assertIn("занять не було", digest.verdict)
        self.assertIn("Тиждень 20–26 вересня", digest.as_lines()[0])

    def test_window_ignores_older_attempts(self):
        self.attempt("w1-hello", "2026-09-19", ok=False, kind="NameError")
        self.attempt("w1-hello", "2026-09-20", ok=True, clean=True)
        self.attempt("w1-hello", "2026-09-26", ok=True, clean=True)

        digest = weekly_digest(self.db, today=TODAY)
        self.assertEqual(digest.checks, 2)
        self.assertEqual(digest.passes, 2)
        self.assertEqual(digest.failures, 0)
        self.assertEqual(digest.days_active, 2)

    def test_days_parameter_narrows_the_window(self):
        self.attempt("w1-hello", "2026-09-24", ok=True)
        digest = weekly_digest(self.db, today=TODAY, days=3)
        self.assertEqual(digest.start, "2026-09-24")
        self.assertEqual(digest.checks, 1)
        self.assertIn("Тиждень 24–26 вересня", digest.title)

    def test_title_crosses_the_month_border(self):
        digest = weekly_digest(self.db, today=date(2026, 10, 3))
        self.assertEqual(digest.title, "Тиждень 27 вересня – 3 жовтня")

    # ---------- що здано ----------

    def test_solved_this_week_are_listed_with_titles(self):
        self.solved("w1-hello", "2026-09-22")
        self.solved("m2-git", "2026-09-24")          # галочка поза тренажером
        self.solved("w1-arith", "2026-09-10")        # минулого тижня

        digest = weekly_digest(self.db, today=TODAY)
        ids = [task_id for task_id, _ in digest.solved]
        self.assertEqual(ids, ["m2-git", "w1-hello"])
        self.assertIn(f"✓ {find_task('w1-hello').title} (w1-hello)",
                      "\n".join(digest.as_lines()))

    # ---------- найважче ----------

    def test_hardest_counts_only_checks_and_sorts_by_repeats(self):
        self.attempt("w1-hello", "2026-09-21", ok=False, kind="NameError")
        self.attempt("w1-hello", "2026-09-22", ok=False, kind="NameError")
        self.attempt("w1-arith", "2026-09-23", ok=False, kind="ValueError")
        self.attempt("w1-vars", "2026-09-23", ok=False, kind="NameError",
                     checks=False)               # запуск без тестів

        digest = weekly_digest(self.db, today=TODAY)
        self.assertEqual([count for _, _, count in digest.hardest], [2, 1])
        self.assertEqual(digest.hardest[0][0], "w1-hello")
        self.assertEqual(digest.hardest[0][1], find_task("w1-hello").title)
        lines = "\n".join(digest.as_lines())
        self.assertIn("⚠", lines)
        self.assertIn("2 провалів", lines)

    # ---------- слабкі теми й «що робити далі» ----------

    def test_weak_topic_gets_a_concrete_task_to_practice(self):
        for day in ("2026-09-21", "2026-09-22", "2026-09-23"):
            self.attempt("w1-arith", day, ok=False, kind="SyntaxError")

        digest = weekly_digest(self.db, today=TODAY)
        self.assertIn("Слабка тема", digest.as_markdown())
        self.assertTrue(digest.weakest)
        name, rate = digest.weakest[0]
        self.assertEqual(name, topic_of("w1-arith"))
        self.assertLess(rate, 0.6)

        self.assertIsNotNone(digest.weak_pick)
        task_id, title = digest.weak_pick
        self.assertEqual(topic_of(task_id), name)
        self.assertEqual(digest.weak_topic, name)
        self.assertNotEqual(self.db.status(task_id), "done")
        self.assertEqual(title, find_task(task_id).title)

    def test_next_tasks_are_the_first_unsolved_ones(self):
        self.solved("w1-hello", "2026-09-22")
        digest = weekly_digest(self.db, today=TODAY)
        expected = [
            (task.id, task.title)
            for task in study_tasks()
            if self.db.status(task.id) != "done"
        ][:3]
        self.assertEqual(digest.next_tasks, expected)

    def test_reviews_due_respect_the_given_day(self):
        self.due_review("w1-hello", "2026-09-25")
        self.assertEqual(weekly_digest(self.db, today=TODAY).reviews_due, 1)
        self.assertEqual(
            weekly_digest(self.db, today=date(2026, 9, 20)).reviews_due, 0
        )
        self.assertIn("Час повторити: 1 задач",
                      weekly_digest(self.db, today=TODAY).as_markdown())

    # ---------- журнал помилок у звіті ----------

    def test_only_this_week_mistakes_are_reported(self):
        self.attempt("w1-hello", "2026-08-30", ok=False, kind="NameError")
        self.attempt("w1-marks", "2026-09-24", ok=False, kind="TypeError")

        digest = weekly_digest(self.db, today=TODAY)
        self.assertEqual([state.task_id for state in digest.mistakes],
                         ["w1-marks"])
        self.assertEqual(len(digest.open_mistakes), 1)

    def test_helped_and_closed_mistakes_are_counted_separately(self):
        self.attempt("w1-hello", "2026-09-21", ok=False, kind="NameError")
        self.attempt("w1-hello", "2026-09-22", ok=True, clean=True)
        self.attempt("w1-marks", "2026-09-23", ok=False, kind="TypeError")
        self.db.reveal_hint("w1-marks", 1)          # здав, але з опорою
        self.attempt("w1-marks", "2026-09-24", ok=True, clean=False)
        self.db.mark_solved("w1-marks", 100)

        digest = weekly_digest(self.db, today=TODAY)
        self.assertEqual(len(digest.closed_mistakes), 1)
        self.assertEqual(len(digest.helped_mistakes), 1)
        self.assertEqual(len(digest.open_mistakes), 0)

    # ---------- вердикт ----------

    def test_verdict_says_the_week_was_ragged(self):
        self.attempt("w1-hello", "2026-09-25", ok=True, clean=True)
        digest = weekly_digest(self.db, today=TODAY)
        self.assertIn("рваним", digest.verdict)
        self.assertIn("1 з 7 днів", digest.verdict)

    def test_verdict_points_at_open_mistakes(self):
        for day in ("2026-09-22", "2026-09-23", "2026-09-24"):
            self.attempt("w1-hello", day, ok=True, clean=True)
        self.attempt("w1-hello", "2026-09-25", ok=False, kind="NameError")

        digest = weekly_digest(self.db, today=TODAY)
        self.assertIn("відкритих помилок", digest.verdict)

    def test_verdict_closes_a_clean_week(self):
        for day in ("2026-09-22", "2026-09-23", "2026-09-24"):
            self.attempt("w1-hello", day, ok=True, clean=True)

        digest = weekly_digest(self.db, today=TODAY)
        self.assertEqual(digest.open_mistakes, [])
        self.assertIn("закрито чисто", digest.verdict)

    # ---------- текст і файл ----------

    def test_markdown_is_a_readable_report(self):
        self.attempt("w1-hello", "2026-09-22", ok=False, kind="NameError")
        self.attempt("w1-hello", "2026-09-23", ok=True, clean=True)
        self.solved("w1-hello", "2026-09-23")

        text = weekly_digest(self.db, today=TODAY).as_markdown(
            generated=datetime(2026, 9, 26, 21, 30)
        )
        self.assertIn("# Тиждень 20–26 вересня", text)
        self.assertIn("Звіт створено 26.09.2026 21:30", text)
        self.assertIn("| Здано нових задач | 1 |", text)
        self.assertIn(f"- {find_task('w1-hello').title} (`w1-hello`)", text)
        self.assertIn("| `NameError` | 1 | закрито |", text)
        self.assertIn("## Що робити далі", text)

    def test_markdown_survives_an_empty_week(self):
        text = weekly_digest(self.db, today=TODAY).as_markdown()
        self.assertIn("Нічого — і це нормально", text)
        self.assertIn("Провалів не було.", text)
        self.assertIn("жодної помилки", text)

    def test_write_digest_saves_the_file(self):
        import tempfile
        from pathlib import Path

        digest = weekly_digest(self.db, today=TODAY)
        with tempfile.TemporaryDirectory() as folder:
            path = write_digest(Path(folder) / "week.md", digest,
                                generated=datetime(2026, 9, 26, 21, 30))
            self.assertTrue(path.exists())
            saved = path.read_text(encoding="utf-8")
        self.assertIn(digest.title, saved)
        self.assertIn(digest.verdict, saved)

    def test_days_constant_is_a_week(self):
        self.assertEqual(DAYS, 7)


if __name__ == "__main__":
    unittest.main()
