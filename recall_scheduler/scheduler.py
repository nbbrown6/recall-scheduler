"""Core SM-2 based scheduling for spaced repetition review.

Reference for the original algorithm:
https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5


@dataclass
class Card:
    front: str
    back: str
    due_date: date = field(default_factory=date.today)
    interval: int = 0
    repetitions: int = 0
    ease_factor: float = DEFAULT_EASE_FACTOR
    last_reviewed: date | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "front": self.front,
            "back": self.back,
            "due_date": self.due_date.isoformat(),
            "interval": self.interval,
            "repetitions": self.repetitions,
            "ease_factor": self.ease_factor,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
        }

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "Card":
        try:
            front = record["front"]
            back = record["back"]
        except KeyError as exc:
            raise ValueError(f"card record missing required field {exc}") from None
        return cls(
            front=front,
            back=back,
            due_date=_parse_date(record.get("due_date")) or date.today(),
            interval=record.get("interval", 0),
            repetitions=record.get("repetitions", 0),
            ease_factor=record.get("ease_factor", DEFAULT_EASE_FACTOR),
            last_reviewed=_parse_date(record.get("last_reviewed")),
        )


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def review(card: Card, quality: int, on: date | None = None) -> Card:
    """Apply one SM-2 review to card and return the updated card.

    quality is graded 0-5: 0-2 means the card was not recalled and its
    repetition streak resets, 3-5 means it was recalled with decreasing
    amounts of effort. The input card is left untouched.
    """
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    review_date = on or date.today()

    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        repetitions = card.repetitions + 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            interval = round(card.interval * card.ease_factor)

    ease_factor = card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(MIN_EASE_FACTOR, ease_factor)

    return Card(
        front=card.front,
        back=card.back,
        due_date=review_date + timedelta(days=interval),
        interval=interval,
        repetitions=repetitions,
        ease_factor=ease_factor,
        last_reviewed=review_date,
    )


def due_cards(cards: list[Card], on: date | None = None) -> list[Card]:
    """Return the subset of cards due for review on or before the given date."""
    cutoff = on or date.today()
    return [c for c in cards if c.due_date <= cutoff]
