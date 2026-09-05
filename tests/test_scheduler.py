import unittest
from datetime import date

from recall_scheduler.scheduler import (
    DEFAULT_EASE_FACTOR,
    MIN_EASE_FACTOR,
    Card,
    due_cards,
    review,
)


class ReviewTests(unittest.TestCase):
    def test_first_success_sets_interval_to_one(self):
        card = Card(front="q", back="a")
        result = review(card, quality=4, on=date(2026, 1, 1))
        self.assertEqual(result.interval, 1)
        self.assertEqual(result.repetitions, 1)
        self.assertEqual(result.due_date, date(2026, 1, 2))
        self.assertEqual(result.last_reviewed, date(2026, 1, 1))

    def test_second_success_sets_interval_to_six(self):
        card = Card(front="q", back="a", interval=1, repetitions=1)
        result = review(card, quality=4, on=date(2026, 1, 1))
        self.assertEqual(result.interval, 6)
        self.assertEqual(result.repetitions, 2)

    def test_third_success_uses_ease_factor(self):
        card = Card(front="q", back="a", interval=6, repetitions=2, ease_factor=2.5)
        result = review(card, quality=4, on=date(2026, 1, 1))
        self.assertEqual(result.repetitions, 3)
        self.assertEqual(result.interval, round(6 * 2.5))

    def test_failure_resets_repetitions_and_interval(self):
        card = Card(front="q", back="a", interval=30, repetitions=5, ease_factor=2.6)
        result = review(card, quality=1, on=date(2026, 1, 1))
        self.assertEqual(result.repetitions, 0)
        self.assertEqual(result.interval, 1)

    def test_ease_factor_does_not_drop_below_floor(self):
        card = Card(front="q", back="a", ease_factor=MIN_EASE_FACTOR)
        result = review(card, quality=0, on=date(2026, 1, 1))
        self.assertEqual(result.ease_factor, MIN_EASE_FACTOR)

    def test_perfect_recall_raises_ease_factor(self):
        card = Card(front="q", back="a")
        result = review(card, quality=5, on=date(2026, 1, 1))
        self.assertGreater(result.ease_factor, DEFAULT_EASE_FACTOR)

    def test_invalid_quality_raises(self):
        card = Card(front="q", back="a")
        with self.assertRaises(ValueError):
            review(card, quality=6)
        with self.assertRaises(ValueError):
            review(card, quality=-1)

    def test_review_does_not_mutate_input(self):
        card = Card(front="q", back="a")
        review(card, quality=4, on=date(2026, 1, 1))
        self.assertEqual(card.interval, 0)
        self.assertEqual(card.repetitions, 0)
        self.assertIsNone(card.last_reviewed)

    def test_defaults_to_today_when_no_date_given(self):
        card = Card(front="q", back="a")
        result = review(card, quality=4)
        self.assertEqual(result.last_reviewed, date.today())


class DueCardsTests(unittest.TestCase):
    def test_filters_by_cutoff(self):
        early = Card(front="a", back="1", due_date=date(2026, 1, 1))
        later = Card(front="b", back="2", due_date=date(2026, 2, 1))
        self.assertEqual(due_cards([early, later], on=date(2026, 1, 15)), [early])

    def test_includes_cards_due_exactly_on_cutoff(self):
        card = Card(front="a", back="1", due_date=date(2026, 1, 1))
        self.assertEqual(due_cards([card], on=date(2026, 1, 1)), [card])


class CardSerializationTests(unittest.TestCase):
    def test_round_trip(self):
        card = Card(
            front="capital of France",
            back="Paris",
            due_date=date(2026, 1, 1),
            interval=6,
            repetitions=2,
            ease_factor=2.4,
            last_reviewed=date(2025, 12, 26),
        )
        self.assertEqual(Card.from_dict(card.to_dict()), card)

    def test_missing_required_field_raises(self):
        with self.assertRaises(ValueError):
            Card.from_dict({"front": "only front"})

    def test_defaults_applied_for_optional_fields(self):
        card = Card.from_dict({"front": "q", "back": "a"})
        self.assertEqual(card.interval, 0)
        self.assertEqual(card.repetitions, 0)
        self.assertEqual(card.ease_factor, DEFAULT_EASE_FACTOR)
        self.assertIsNone(card.last_reviewed)
        self.assertEqual(card.due_date, date.today())


if __name__ == "__main__":
    unittest.main()
