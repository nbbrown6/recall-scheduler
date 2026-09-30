import io
import json
import os
import tempfile
import unittest
from datetime import date

from recall_scheduler.io import (
    iter_cards,
    iter_leitner_cards,
    load_cards,
    load_csv_cards,
    load_leitner_cards,
    write_cards,
    write_csv_cards,
    write_leitner_cards,
)
from recall_scheduler.leitner import LeitnerCard
from recall_scheduler.scheduler import Card


class IterCardsTests(unittest.TestCase):
    def test_reads_from_open_file_like_object(self):
        stream = io.StringIO(
            '{"front": "capital of France", "back": "Paris"}\n'
            "\n"
            "# a comment\n"
            '{"front": "capital of Peru", "back": "Lima", "due_date": "2026-09-01"}\n'
        )
        cards = list(iter_cards(stream))
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].front, "capital of France")
        self.assertEqual(cards[1].due_date, date(2026, 9, 1))

    def test_invalid_json_reports_line_number(self):
        stream = io.StringIO("not json\n")
        with self.assertRaises(ValueError) as ctx:
            list(iter_cards(stream))
        self.assertIn("line 1", str(ctx.exception))

    def test_reads_from_path(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"front": "q", "back": "a"}\n')
            path = f.name
        try:
            cards = load_cards(path)
        finally:
            os.remove(path)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].front, "q")


class WriteCardsTests(unittest.TestCase):
    def test_round_trips_through_load_cards(self):
        deck = [
            Card(front="a", back="1"),
            Card(front="b", back="2", due_date=date(2026, 1, 1)),
        ]
        stream = io.StringIO()
        write_cards(deck, stream)
        stream.seek(0)
        self.assertEqual(load_cards(stream), deck)

    def test_writes_to_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "deck.jsonl")
            write_cards([Card(front="q", back="a")], path)
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["front"], "q")


class IterLeitnerCardsTests(unittest.TestCase):
    def test_reads_from_open_file_like_object(self):
        stream = io.StringIO(
            '{"front": "capital of France", "back": "Paris", "box": 2}\n'
            "\n"
            "# a comment\n"
            '{"front": "capital of Peru", "back": "Lima", "due_date": "2026-09-01"}\n'
        )
        cards = list(iter_leitner_cards(stream))
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].box, 2)
        self.assertEqual(cards[1].due_date, date(2026, 9, 1))

    def test_invalid_json_reports_line_number(self):
        stream = io.StringIO("not json\n")
        with self.assertRaises(ValueError) as ctx:
            list(iter_leitner_cards(stream))
        self.assertIn("line 1", str(ctx.exception))

    def test_reads_from_path(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"front": "q", "back": "a"}\n')
            path = f.name
        try:
            cards = load_leitner_cards(path)
        finally:
            os.remove(path)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].front, "q")


class WriteLeitnerCardsTests(unittest.TestCase):
    def test_round_trips_through_load_leitner_cards(self):
        deck = [
            LeitnerCard(front="a", back="1"),
            LeitnerCard(front="b", back="2", box=3, due_date=date(2026, 1, 1)),
        ]
        stream = io.StringIO()
        write_leitner_cards(deck, stream)
        stream.seek(0)
        self.assertEqual(load_leitner_cards(stream), deck)

    def test_writes_to_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "deck.jsonl")
            write_leitner_cards([LeitnerCard(front="q", back="a")], path)
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["front"], "q")


class CsvCardsTests(unittest.TestCase):
    def test_reads_header_and_applies_defaults_for_empty_cells(self):
        stream = io.StringIO(
            "front,back,due_date,interval,ease_factor\n"
            "capital of France,Paris,,,\n"
            "capital of Peru,Lima,2026-09-01,6,2.1\n"
        )
        cards = load_csv_cards(stream)
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].interval, 0)
        self.assertEqual(cards[0].ease_factor, 2.5)
        self.assertEqual(cards[1].due_date, date(2026, 9, 1))
        self.assertEqual(cards[1].interval, 6)
        self.assertEqual(cards[1].ease_factor, 2.1)

    def test_quoted_fields_with_commas(self):
        stream = io.StringIO('front,back\n"one, two",three\n')
        cards = load_csv_cards(stream)
        self.assertEqual(cards[0].front, "one, two")

    def test_missing_required_column_reports_line_number(self):
        stream = io.StringIO("front,back\nq,a\nonly-front,\n")
        with self.assertRaises(ValueError) as ctx:
            load_csv_cards(stream)
        self.assertIn("line 3", str(ctx.exception))

    def test_bad_number_reports_line_number(self):
        stream = io.StringIO("front,back,interval\nq,a,soon\n")
        with self.assertRaises(ValueError) as ctx:
            load_csv_cards(stream)
        self.assertIn("line 2", str(ctx.exception))

    def test_round_trips_sm2_cards(self):
        deck = [
            Card(front="a, with comma", back="1"),
            Card(
                front="b",
                back="2",
                due_date=date(2026, 1, 1),
                interval=6,
                repetitions=2,
                ease_factor=2.36,
                last_reviewed=date(2025, 12, 26),
            ),
        ]
        stream = io.StringIO()
        write_csv_cards(deck, stream)
        stream.seek(0)
        self.assertEqual(load_csv_cards(stream), deck)

    def test_round_trips_leitner_cards(self):
        deck = [
            LeitnerCard(front="a", back="1"),
            LeitnerCard(front="b", back="2", box=3, due_date=date(2026, 1, 1)),
        ]
        stream = io.StringIO()
        write_csv_cards(deck, stream, card_type=LeitnerCard)
        stream.seek(0)
        self.assertEqual(load_csv_cards(stream, card_type=LeitnerCard), deck)

    def test_empty_deck_still_writes_header(self):
        stream = io.StringIO()
        write_csv_cards([], stream, card_type=LeitnerCard)
        self.assertTrue(stream.getvalue().startswith("front,back,box,"))

    def test_writes_to_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "deck.csv")
            write_csv_cards([Card(front="q", back="a")], path)
            cards = load_csv_cards(path)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].back, "a")


if __name__ == "__main__":
    unittest.main()
