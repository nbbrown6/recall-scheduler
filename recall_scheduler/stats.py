"""Retention rate and streak stats over a history of review outcomes.

Card and LeitnerCard only carry current scheduling state (ease factor,
box, due date, ...), not a log of past reviews, so there's nothing in
either dataclass to compute retention or streaks from directly. These
functions work on whatever outcome history the caller keeps instead: a
sequence of booleans, oldest first, meaning "did I recall this card".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ReviewStats:
    total: int
    passed: int
    retention_rate: float
    current_streak: int
    longest_streak: int


def summarize(outcomes: Iterable[bool]) -> ReviewStats:
    """Summarize a sequence of pass/fail review outcomes, oldest first.

    retention_rate is passed / total, 0.0 for an empty sequence.
    current_streak is the run of consecutive passes ending at the last
    outcome (0 if the last outcome was a fail or there were no reviews).
    longest_streak is the longest such run anywhere in the sequence.
    """
    outcomes = list(outcomes)
    total = len(outcomes)
    passed = sum(1 for outcome in outcomes if outcome)
    retention_rate = passed / total if total else 0.0

    longest_streak = 0
    running = 0
    for outcome in outcomes:
        if outcome:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
    current_streak = running

    return ReviewStats(
        total=total,
        passed=passed,
        retention_rate=retention_rate,
        current_streak=current_streak,
        longest_streak=longest_streak,
    )


def quality_passed(quality: int, threshold: int = 3) -> bool:
    """Convert an SM-2 quality score (0-5) into a pass/fail outcome.

    Uses the same threshold review() applies internally: a quality of
    3 or above counts as a successful recall.
    """
    return quality >= threshold
