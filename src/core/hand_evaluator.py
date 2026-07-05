"""
core/hand_evaluator.py
----------------------
PURPOSE:
  Given 1–5 Card objects, detect the best poker hand they form
  and return a HandResult describing what was found.

WHY SEPARATE FROM SCORING?
  Evaluation (WHAT hand do you have?) is a distinct concern from
  Scoring (HOW MANY POINTS does that hand give you?).
  Keeping them apart means:
  - Swap scoring tables without touching detection logic
  - Add "bonus chips for specific cards" without rewriting the evaluator
  - Unit-test hand detection independently

NO ARCADE IMPORTS — pure Python only.

USAGE EXAMPLE:
  from core.deck import Deck
  from core.hand_evaluator import evaluate

  deck = Deck()
  cards = deck.draw(5)
  result = evaluate(cards)
  print(result.hand_name)    # e.g. "Flush"
  print(result.base_chips)   # e.g. 35
  print(result.base_mult)    # e.g. 4.0
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only imported for type hints — avoids circular imports at runtime
    from core.deck import Card


# ---------------------------------------------------------------------------
# Chips × Mult base table
# ---------------------------------------------------------------------------
# Key   = hand name (str)
# Value = (base_chips: int, base_mult: float)
#
# Phase 01 numbers inspired by Balatro default values.
HAND_TABLE: dict[str, tuple[int, float]] = {
    "High Card":        (5,   1.0),
    "Pair":             (10,  2.0),
    "Two Pair":         (20,  2.0),
    "Three of a Kind":  (30,  3.0),
    "Straight":         (30,  4.0),
    "Flush":            (35,  4.0),
    "Full House":       (40,  4.0),
    "Four of a Kind":   (60,  7.0),
    "Straight Flush":   (100, 8.0),
    "Royal Flush":      (100, 8.0),
}


# ---------------------------------------------------------------------------
# HandResult dataclass
# ---------------------------------------------------------------------------
@dataclass
class HandResult:
    """
    Returned by `evaluate()`.  Describes the best hand found.

    Fields
    ------
    hand_name : str
        Human-readable name, e.g. "Flush".  Key into HAND_TABLE.
    base_chips : int
        Starting chip count for this hand type (before card values are added).
    base_mult : float
        Starting multiplier for this hand type.
    scored_cards : list[Card]
        The subset of played cards that contributed to this hand.
        Used for the scoring animation (these get highlighted / pulsed).
        Examples:
          Pair          → the two matching cards
          Flush         → all five cards
          Four of a Kind → the four matching cards
          High Card     → the single highest-rank card
    """

    hand_name:    str
    base_chips:   int
    base_mult:    float
    scored_cards: list["Card"] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Private helper functions
# ---------------------------------------------------------------------------

def _rank_groups(cards: list["Card"]) -> Counter:
    """
    Return a Counter mapping rank_index → count of cards at that rank.

    Example: [5♠, 5♥, K♣, K♦, A♠] → Counter({3: 2, 11: 2, 12: 1})
    """
    return Counter(c.rank_index for c in cards)


def _is_flush(cards: list["Card"]) -> bool:
    """
    Return True only when ALL 5 cards share the exact same suit.
    Returns False for any hand size other than 5.
    """
    if len(cards) != 5:
        return False
    return len(set(c.suit for c in cards)) == 1


def _is_straight(cards: list["Card"]) -> bool:
    """
    Return True when the 5 cards form a consecutive rank sequence.

    Handles two cases:
      • Normal straight : sorted unique ranks span exactly 4 (e.g. 5-6-7-8-9)
      • Wheel (A-low)   : ranks are exactly [0,1,2,3,12]  →  A-2-3-4-5

    Returns False for any hand size other than 5 or when duplicate ranks exist.
    """
    if len(cards) != 5:
        return False

    rank_set = set(c.rank_index for c in cards)
    if len(rank_set) != 5:          # duplicate ranks → not a straight
        return False

    ranks = sorted(rank_set)

    if ranks[-1] - ranks[0] == 4:  # normal straight: no gaps, span of 4
        return True

    if ranks == [0, 1, 2, 3, 12]:  # wheel: A treated as low card (before 2)
        return True

    return False


def _cards_with_rank(cards: list["Card"], rank_index: int) -> list["Card"]:
    """Return every card in `cards` whose rank_index equals `rank_index`."""
    return [c for c in cards if c.rank_index == rank_index]


def _make_result(name: str, scored_cards: list["Card"]) -> HandResult:
    """Convenience: look up HAND_TABLE and build a HandResult in one call."""
    chips, mult = HAND_TABLE[name]
    return HandResult(name, chips, mult, scored_cards)


# ---------------------------------------------------------------------------
# Main evaluate function
# ---------------------------------------------------------------------------

def evaluate(cards: list["Card"]) -> HandResult:
    """
    Detect the best poker hand in 1–5 cards and return a HandResult.

    Detection priority (highest first):
      Royal Flush → Straight Flush → Four of a Kind → Full House →
      Flush → Straight → Three of a Kind → Two Pair → Pair → High Card

    Parameters
    ----------
    cards : list[Card]
        1 to 5 Card objects the player chose to play.

    Returns
    -------
    HandResult
        The best hand found, with base_chips, base_mult, and the subset
        of cards that formed the hand (scored_cards).
    """
    # Guard: empty hand → High Card with no scored cards
    if not cards:
        return _make_result("High Card", [])

    # Pre-compute helpers used by multiple checks below
    groups   = _rank_groups(cards)          # {rank_index: count}
    counts   = sorted(groups.values(), reverse=True)  # e.g. [3, 2] for Full House
    flush    = _is_flush(cards)
    straight = _is_straight(cards)

    # ------------------------------------------------------------------
    # Royal Flush: T-J-Q-K-A all same suit
    # rank_indices for Ten→Ace = 8,9,10,11,12
    # ------------------------------------------------------------------
    if flush and straight:
        rank_indices = sorted(c.rank_index for c in cards)
        if rank_indices == [8, 9, 10, 11, 12]:
            return _make_result("Royal Flush", list(cards))
        return _make_result("Straight Flush", list(cards))

    # ------------------------------------------------------------------
    # Four of a Kind
    # ------------------------------------------------------------------
    if counts[0] == 4:
        # Find the rank that appears 4 times
        quad_rank = max(groups, key=lambda r: groups[r])
        scored    = _cards_with_rank(cards, quad_rank)
        return _make_result("Four of a Kind", scored)

    # ------------------------------------------------------------------
    # Full House: three-of-a-kind + pair
    # ------------------------------------------------------------------
    if len(counts) >= 2 and counts[0] == 3 and counts[1] == 2:
        return _make_result("Full House", list(cards))

    # ------------------------------------------------------------------
    # Flush (already checked for 5 cards above)
    # ------------------------------------------------------------------
    if flush:
        return _make_result("Flush", list(cards))

    # ------------------------------------------------------------------
    # Straight
    # ------------------------------------------------------------------
    if straight:
        return _make_result("Straight", list(cards))

    # ------------------------------------------------------------------
    # Three of a Kind
    # ------------------------------------------------------------------
    if counts[0] == 3:
        triple_rank = max(groups, key=lambda r: groups[r])
        scored      = _cards_with_rank(cards, triple_rank)
        return _make_result("Three of a Kind", scored)

    # ------------------------------------------------------------------
    # Two Pair
    # ------------------------------------------------------------------
    if len(counts) >= 2 and counts[0] == 2 and counts[1] == 2:
        pair_ranks = [r for r, c in groups.items() if c == 2]
        scored: list["Card"] = []
        for r in pair_ranks:
            scored.extend(_cards_with_rank(cards, r))
        return _make_result("Two Pair", scored)

    # ------------------------------------------------------------------
    # Pair
    # ------------------------------------------------------------------
    if counts[0] == 2:
        pair_rank = max(groups, key=lambda r: groups[r])
        scored    = _cards_with_rank(cards, pair_rank)
        return _make_result("Pair", scored)

    # ------------------------------------------------------------------
    # High Card — take the single card with the highest rank_index
    # ------------------------------------------------------------------
    best_card = max(cards, key=lambda c: c.rank_index)
    return _make_result("High Card", [best_card])
