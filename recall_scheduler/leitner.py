"""Leitner box scheduling, a simpler alternative to SM-2.

Reference: https://en.wikipedia.org/wiki/Leitner_system

Where SM-2 grades recall on a 0-5 scale and grows intervals by a
per-card ease factor, Leitner just tracks a box number: recall moves a
card up a box, forgetting sends it back to box one. Box number maps to
a review interval through a fixed schedule. It is coarser than SM-2
but easier to reason about and to run by hand with physical cards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

# Days to wait before the next review, indexed by box number (box 1 is
# box_intervals[0]). A card that keeps getting recalled climbs this list;
# one miss drops it back to box 1 regardless of how high it had climbed.
DEFAULT_BOX_INTERVALS = (1, 2, 4, 8, 16, 32)


@dataclass
class LeitnerCard:
    front: str
    back: str
    box: int = 1
    due_date: date = field(default_factory=date.today)
    last_reviewed: date | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "front": self.front,
            "back": self.back,
            "box": self.box,
            "due_date": self.due_date.isoformat(),
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
        }

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "LeitnerCard":
        try:
            front = record["front"]
            back = record["back"]
        except KeyError as exc:
            raise ValueError(f"card record missing required field {exc}") from None
        return cls(
            front=front,
            back=back,
            box=record.get("box", 1),
            due_date=_parse_date(record.get("due_date")) or date.today(),
            last_reviewed=_parse_date(record.get("last_reviewed")),
        )


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def review(
    card: LeitnerCard,
    recalled: bool,
    on: date | None = None,
    box_intervals: tuple[int, ...] = DEFAULT_BOX_INTERVALS,
) -> LeitnerCard:
    """Apply one Leitner review to card and return the updated card.

    recalled True moves the card up one box (capped at the top box),
    False drops it back to box 1. The input card is left untouched.
    """
    if not box_intervals:
        raise ValueError("box_intervals must not be empty")

    review_date = on or date.today()

    if recalled:
        box = min(card.box + 1, len(box_intervals))
    else:
        box = 1

    interval = box_intervals[box - 1]

    return LeitnerCard(
        front=card.front,
        back=card.back,
        box=box,
        due_date=review_date + timedelta(days=interval),
        last_reviewed=review_date,
    )


def due_cards(cards: list[LeitnerCard], on: date | None = None) -> list[LeitnerCard]:
    """Return the subset of cards due for review on or before the given date."""
    cutoff = on or date.today()
    return [c for c in cards if c.due_date <= cutoff]
