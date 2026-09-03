# recall-scheduler

A small Python library for scheduling spaced repetition reviews. It
implements the SM-2 algorithm (the one behind early versions of Anki and
SuperMemo) and nothing else — no storage layer, no UI, no network calls.
You bring the cards, it tells you when to see them again.

## Why

Every spaced repetition app needs the same core: given a card's review
history and how well you remembered it just now, compute the next due
date. That logic is small and well understood, but most implementations
bury it inside a specific app's database models and UI code, which makes
it awkward to reuse. This is that logic, pulled out on its own.

## Install

No PyPI package yet — copy the `recall_scheduler` directory into your
project, or point at this repo as a path dependency. There are no
third-party dependencies to worry about either way, just the standard
library.

## Usage

Scheduling a single review:

```python
from datetime import date
from recall_scheduler import Card, review

card = Card(front="capital of France", back="Paris")
card = review(card, quality=4, on=date(2026, 8, 29))
print(card.due_date, card.interval, card.ease_factor)
# 2026-08-30 1 2.5
```

Grading again a few reviews later pushes the interval out further:

```python
card = review(card, quality=5, on=date(2026, 8, 30))
card = review(card, quality=5, on=date(2026, 9, 5))
print(card.due_date)
```

`quality` follows the SM-2 0-5 scale: 0-2 means you failed to recall the
card and its streak resets, 3-5 means you recalled it with decreasing
amounts of effort.

## Reading cards from files or stdin

Card decks are stored as newline-delimited JSON, one card per line. The
loader accepts a file path, an already-open file object, or nothing at
all (meaning read from stdin), so the same code works whether cards come
from disk or a pipe:

```python
from recall_scheduler import load_cards, due_cards

# from a file path
deck = load_cards("deck.jsonl")

# from stdin, e.g. `cat deck.jsonl | python my_script.py`
deck = load_cards()

# or explicitly
import sys
deck = load_cards(sys.stdin)

for card in due_cards(deck):
    print(card.front)
```

A deck file looks like:

```
{"front": "capital of France", "back": "Paris"}
{"front": "capital of Peru", "back": "Lima", "due_date": "2026-09-01"}
```

Blank lines and lines starting with `#` are ignored, so decks can carry
comments.

## Saving a deck

`write_cards` takes the same kind of destination as the loaders accept
for sources: a file path, an already-open file object, or nothing at
all (meaning write to stdout).

```python
from recall_scheduler import write_cards

write_cards(deck, "deck.jsonl")
```

The output is newline-delimited JSON with one card per line, so it
reads back in with `load_cards` unchanged.

## Status

Early skeleton. The scheduling math and the file/stdin readers and
writer are real, but there's no CLI yet, no test suite, and no
packaging beyond a bare `pyproject.toml`.

## License

MIT, see LICENSE.
