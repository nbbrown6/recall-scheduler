import unittest
from datetime import date, timedelta

from recall_scheduler.leitner import (
    DEFAULT_BOX_INTERVALS,
    LeitnerCard,
    due_cards,
    review,
)


class ReviewTests(unittest.TestCase):
    def test_recall_advances_box(self):
        card = LeitnerCard(front="q", back="a", box=1)
        result = review(card, recalled=True, on=date(2026, 1, 1))
        self.assertEqual(result.box, 2)
        self.assertEqual(
            result.due_date, date(2026, 1, 1) + timedelta(days=DEFAULT_BOX_INTERVALS[1])
        )
        self.assertEqual(result.last_reviewed, date(2026, 1, 1))

    def test_recall_at_top_box_stays(self):
        top = len(DEFAULT_BOX_INTERVALS)
        card = LeitnerCard(front="q", back="a", box=top)
        result = review(card, recalled=True, on=date(2026, 1, 1))
        self.assertEqual(result.box, top)

    def test_miss_resets_to_box_one(self):
        card = LeitnerCard(front="q", back="a", box=5)
        result = review(card, recalled=False, on=date(2026, 1, 1))
        self.assertEqual(result.box, 1)
        self.assertEqual(
            result.due_date, date(2026, 1, 1) + timedelta(days=DEFAULT_BOX_INTERVALS[0])
        )

    def test_custom_box_intervals(self):
        card = LeitnerCard(front="q", back="a", box=1)
        result = review(card, recalled=True, on=date(2026, 1, 1), box_intervals=(1, 10))
        self.assertEqual(result.box, 2)
        self.assertEqual(result.due_date, date(2026, 1, 11))

    def test_empty_box_intervals_raises(self):
        card = LeitnerCard(front="q", back="a")
        with self.assertRaises(ValueError):
            review(card, recalled=True, box_intervals=())

    def test_review_does_not_mutate_input(self):
        card = LeitnerCard(front="q", back="a", box=1)
        review(card, recalled=True, on=date(2026, 1, 1))
        self.assertEqual(card.box, 1)
        self.assertIsNone(card.last_reviewed)

    def test_defaults_to_today_when_no_date_given(self):
        card = LeitnerCard(front="q", back="a")
        result = review(card, recalled=True)
        self.assertEqual(result.last_reviewed, date.today())


class DueCardsTests(unittest.TestCase):
    def test_filters_by_cutoff(self):
        early = LeitnerCard(front="a", back="1", due_date=date(2026, 1, 1))
        later = LeitnerCard(front="b", back="2", due_date=date(2026, 2, 1))
        self.assertEqual(due_cards([early, later], on=date(2026, 1, 15)), [early])

    def test_includes_cards_due_exactly_on_cutoff(self):
        card = LeitnerCard(front="a", back="1", due_date=date(2026, 1, 1))
        self.assertEqual(due_cards([card], on=date(2026, 1, 1)), [card])


class LeitnerCardSerializationTests(unittest.TestCase):
    def test_round_trip(self):
        card = LeitnerCard(
            front="capital of France",
            back="Paris",
            box=3,
            due_date=date(2026, 1, 1),
            last_reviewed=date(2025, 12, 26),
        )
        self.assertEqual(LeitnerCard.from_dict(card.to_dict()), card)

    def test_missing_required_field_raises(self):
        with self.assertRaises(ValueError):
            LeitnerCard.from_dict({"front": "only front"})

    def test_defaults_applied_for_optional_fields(self):
        card = LeitnerCard.from_dict({"front": "q", "back": "a"})
        self.assertEqual(card.box, 1)
        self.assertIsNone(card.last_reviewed)
        self.assertEqual(card.due_date, date.today())


if __name__ == "__main__":
    unittest.main()
