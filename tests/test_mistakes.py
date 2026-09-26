"""Тести журналу помилок: коли помилка вважається закритою.

Тут перевіряється головне правило модуля: «здав» і «здав сам» — різні речі.
Помилка, закрита з підказкою або вставленим розв'язком, лишається видимою і
просить холодного повторення; помилка, яку закрили чистим проходом, зникає.
"""

import unittest

from trainer.core.db import Database
from trainer.core.mistakes import (
    CLOSED,
    HELPED,
    OPEN,
    mistake_states,
    open_states,
)


class MistakeStateTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    # ---------- допоміжне ----------

    def fail(self, task_id: str = "w1-hello", kind: str = "NameError") -> None:
        self.db.record_attempt(task_id, ok=False, with_checks=True,
                               failed_check="виводить привітання",
                               error_kind=kind)

    def passed(self, task_id: str = "w1-hello", *, clean: bool = True) -> None:
        self.db.record_attempt(task_id, ok=True, with_checks=True, xp=100,
                               clean=clean)
        self.db.mark_solved(task_id, 100)

    def only(self):
        states = mistake_states(self.db)
        self.assertEqual(len(states), 1)
        return states[0]

    # ---------- три стани ----------

    def test_plain_failure_is_open(self):
        self.fail()
        state = self.only()
        self.assertEqual(state.status, OPEN)
        self.assertTrue(state.is_open)
        self.assertFalse(state.is_closed)
        self.assertEqual(state.label, "відкрито")
        self.assertEqual(state.times, 1)
        self.assertIsNone(state.passed_at)
        self.assertEqual(open_states([state]), [state])

    def test_failure_never_passed_stays_open_even_if_other_task_solved(self):
        self.fail("w1-hello")
        self.passed("w1-arith")
        self.assertEqual(self.only().status, OPEN)

    def test_pass_with_help_closes_only_partly(self):
        self.fail()
        self.db.reveal_hint("w1-hello", 1)
        self.passed(clean=False)

        state = self.only()
        self.assertEqual(state.status, HELPED)
        self.assertEqual(state.label, "закрито з допомогою")
        self.assertFalse(state.is_closed)         # усе ще просить повторення
        self.assertFalse(state.is_open)           # але вже не «висить»
        self.assertEqual(open_states([state]), [state])
        self.assertIsNotNone(state.passed_at)

    def test_clean_pass_closes_completely(self):
        self.fail()
        self.passed(clean=True)

        state = self.only()
        self.assertEqual(state.status, CLOSED)
        self.assertTrue(state.is_closed)
        self.assertEqual(open_states([state]), [])
        self.assertIsNotNone(state.clean_at)

    def test_clean_pass_after_a_hint_earlier_still_closes(self):
        """Підказка тижневої давнини не тримає помилку відкритою вічно."""
        self.fail()
        self.db.reveal_hint("w1-hello", 1)
        self.fail()                       # друга невдача, уже після підказки
        self.passed(clean=True)           # і чистий прохід — нехай пізніше

        self.assertEqual(self.only().status, CLOSED)

    def test_repeated_failure_after_a_clean_pass_reopens(self):
        """Задача знову почала падати — помилка повертається у список."""
        self.passed(clean=True)
        self.fail(kind="TypeError")
        state = self.only()
        self.assertEqual(state.status, OPEN)
        self.assertEqual(state.kind, "TypeError")

    def test_mark_solved_by_hand_closes_without_an_attempt(self):
        """Галочка «зроблено поза тренажером» — теж закриття, і чесне."""
        self.fail()
        self.db.mark_solved("w1-hello", 0)

        state = self.only()
        self.assertEqual(state.status, CLOSED)
        self.assertTrue(state.manual)
        self.assertIsNone(state.passed_at)

    # ---------- кілька помилок і межа вибірки ----------

    def test_each_error_kind_is_classified_on_its_own(self):
        """Старий NameError закритий, свіжий TypeError — ні."""
        self.fail(kind="NameError")
        self.passed(clean=True)
        self.fail(kind="TypeError")

        states = {state.kind: state.status for state in mistake_states(self.db)}
        self.assertEqual(states, {"NameError": CLOSED, "TypeError": OPEN})

    def test_plain_runs_never_land_in_the_journal(self):
        """Запуск без тестів — це не помилка знань, і в журнал він не йде."""
        self.db.record_attempt("w1-hello", ok=False, with_checks=False,
                               failed_check="", error_kind="")
        self.assertEqual(mistake_states(self.db), [])

    def test_limit_keeps_the_newest_and_counts_repeats(self):
        for index in range(4):
            self.fail(f"w1-hello", kind=f"Error{index}")
        self.fail(kind="NameError")
        self.fail(kind="NameError")

        states = mistake_states(self.db, limit=3)
        self.assertEqual(len(states), 3)
        self.assertEqual(states[0].kind, "NameError")   # найсвіжіша — перша
        self.assertEqual(states[0].times, 2)


if __name__ == "__main__":
    unittest.main()
