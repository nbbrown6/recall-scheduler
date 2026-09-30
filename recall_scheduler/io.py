"""Reading card decks from a file path, an already-open file, or stdin."""

from __future__ import annotations

import csv
import json
import sys
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, TextIO, TypeVar, Union

from .leitner import LeitnerCard
from .scheduler import Card

Source = Union[str, "os.PathLike[str]", TextIO, None]
Dest = Union[str, "os.PathLike[str]", TextIO, None]


@contextmanager
def _open_source(source: Source) -> Iterator[TextIO]:
    """Yield a readable text stream for source.

    None or "-" means stdin, so callers don't need a branch for the
    pipe case. Anything with a .read() is used as-is and left open,
    since we didn't open it. Everything else is treated as a path.
    """
    if source is None or source == "-":
        yield sys.stdin
        return
    if hasattr(source, "read"):
        yield source  # type: ignore[misc]
        return
    with open(source, "r", encoding="utf-8") as f:
        yield f


def iter_cards(source: Source = None) -> Iterator[Card]:
    """Lazily parse a newline-delimited JSON deck into Card objects.

    Blank lines and lines starting with '#' are skipped so decks can
    carry comments. See Source for what source may be.
    """
    with _open_source(source) as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {lineno}: invalid JSON ({exc})") from None
            yield Card.from_dict(record)


def load_cards(source: Source = None) -> list[Card]:
    """Eagerly load a deck into a list. See iter_cards for accepted sources."""
    return list(iter_cards(source))


@contextmanager
def _open_dest(dest: Dest) -> Iterator[TextIO]:
    """Yield a writable text stream for dest.

    None or "-" means stdout, mirroring _open_source. Anything with a
    .write() is used as-is and left open, since we didn't open it.
    Everything else is treated as a path.
    """
    if dest is None or dest == "-":
        yield sys.stdout
        return
    if hasattr(dest, "write"):
        yield dest  # type: ignore[misc]
        return
    with open(dest, "w", encoding="utf-8") as f:
        yield f


def write_cards(cards: Iterable[Card], dest: Dest = None) -> None:
    """Write cards as newline-delimited JSON to dest.

    One JSON object per line, so the output round-trips through
    load_cards. See Dest for what dest may be.
    """
    with _open_dest(dest) as f:
        for card in cards:
            f.write(json.dumps(card.to_dict()))
            f.write("\n")


CardT = TypeVar("CardT", Card, LeitnerCard)

# CSV has no types, so numeric columns come back as strings and need
# converting before they reach from_dict.
_CSV_INT_FIELDS = ("interval", "repetitions", "box")
_CSV_FLOAT_FIELDS = ("ease_factor",)


def _csv_record(row: dict[str, str]) -> dict[str, Any]:
    """Turn one DictReader row into a dict that from_dict accepts.

    Empty cells are dropped so the card's defaults apply, the same as a
    missing key in a JSONL record. Unknown columns are ignored.
    """
    record: dict[str, Any] = {
        key: value for key, value in row.items() if key and value not in (None, "")
    }
    for key in _CSV_INT_FIELDS:
        if key in record:
            record[key] = int(record[key])
    for key in _CSV_FLOAT_FIELDS:
        if key in record:
            record[key] = float(record[key])
    return record


def iter_csv_cards(
    source: Source = None, card_type: type[CardT] = Card  # type: ignore[assignment]
) -> Iterator[CardT]:
    """Lazily parse a CSV deck into cards of card_type (Card or LeitnerCard).

    The first row must be a header naming the columns; front and back are
    required, the rest are optional and use the same names as the JSONL
    format. Comment lines are not supported, since a leading '#' is
    legitimate card text in CSV. See Source for what source may be.
    """
    with _open_source(source) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                yield card_type.from_dict(_csv_record(row))
            except ValueError as exc:
                raise ValueError(f"line {reader.line_num}: {exc}") from None


def load_csv_cards(
    source: Source = None, card_type: type[CardT] = Card  # type: ignore[assignment]
) -> list[CardT]:
    """Eagerly load a CSV deck into a list. See iter_csv_cards."""
    return list(iter_csv_cards(source, card_type))


def write_csv_cards(
    cards: Iterable[CardT],
    dest: Dest = None,
    card_type: type[CardT] = Card,  # type: ignore[assignment]
) -> None:
    """Write cards as CSV with a header row to dest.

    card_type picks the columns, so the header is written even for an
    empty deck and the output reads back through load_csv_cards with the
    same card_type. See Dest for what dest may be.
    """
    fieldnames = list(card_type(front="", back="").to_dict())
    with _open_dest(dest) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for card in cards:
            writer.writerow(card.to_dict())


def iter_leitner_cards(source: Source = None) -> Iterator[LeitnerCard]:
    """Lazily parse a newline-delimited JSON deck into LeitnerCard objects.

    Same format and comment/blank-line handling as iter_cards, but for
    the Leitner box scheduler's card type. See Source for what source
    may be.
    """
    with _open_source(source) as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {lineno}: invalid JSON ({exc})") from None
            yield LeitnerCard.from_dict(record)


def load_leitner_cards(source: Source = None) -> list[LeitnerCard]:
    """Eagerly load a deck into a list. See iter_leitner_cards for accepted sources."""
    return list(iter_leitner_cards(source))


def write_leitner_cards(cards: Iterable[LeitnerCard], dest: Dest = None) -> None:
    """Write LeitnerCard cards as newline-delimited JSON to dest.

    One JSON object per line, so the output round-trips through
    load_leitner_cards. See Dest for what dest may be.
    """
    with _open_dest(dest) as f:
        for card in cards:
            f.write(json.dumps(card.to_dict()))
            f.write("\n")
