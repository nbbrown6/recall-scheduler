import io
import json
import os
import tempfile
import unittest
from datetime import date

from recall_scheduler.io import iter_cards, load_cards, write_cards
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


if __name__ == "__main__":
    unittest.main()
