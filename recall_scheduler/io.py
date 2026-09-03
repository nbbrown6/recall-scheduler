"""Reading card decks from a file path, an already-open file, or stdin."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from typing import Iterable, Iterator, TextIO, Union

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
