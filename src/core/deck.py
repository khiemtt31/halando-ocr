"""
core/deck.py
------------
PURPOSE:
  Owns the full 52-card standard playing card deck.
  Provides Card (data) and Deck (logic) — no arcade, no UI, pure Python.

WHY SEPARATE FROM GAMEPLAY_VIEW?
  GamePlayView only handles DISPLAY and INPUT.
  The deck is a data / logic concern — keeping it here means:
  - Easy to unit-test (no screen needed)
  - Reusable in future game modes (e.g. multi-round)
  - Swap deck type (e.g. custom joker deck) without touching rendering

USAGE EXAMPLE:
  from core.deck import Deck
  deck = Deck()           # builds + shuffles 52 cards
  hand = deck.draw(8)     # deal 8 cards → list[Card]
  deck.remaining()        # how many cards left
"""

import os
import random
from dataclasses import dataclass, field

from constants import CARDS_DIR


# ---------------------------------------------------------------------------
# Rank definitions
# ---------------------------------------------------------------------------
# Each tuple is: (display_name, chip_value, rank_index)
#   display_name  → used to build the image filename  e.g. "A", "K", "02"
#   chip_value    → added to Chips when card is scored
#   rank_index    → integer 0–12, used for Straight detection (A can be 0 or 12)
#
# TODO (you write this): fill in all 13 ranks in ascending order.
# The list below is a STUB – add all ranks from 2 through Ace.
_RANK_DEFS: list[tuple[str, int, int]] = [
    # (display_name, chip_value, rank_index)
    ("2", 2, 0),
    ("3", 3, 1),
    ("4", 4, 2),
    ("5", 5, 3),
    ("6", 6, 4),
    ("7", 7, 5),
    ("8", 8, 6),
    ("9", 9, 7),
    ("10", 10, 8),
    ("J", 10, 9),
    ("Q", 10, 10),
    ("K", 10, 11),
    ("A", 11, 12),
]

# The four suits and their image-filename prefix
_SUITS: list[str] = ["clubs", "diamonds", "hearts", "spades"]

# Fallback image when the card file is missing from assets
_FALLBACK_IMAGE = os.path.join(CARDS_DIR, "card_spades_A.png")


# ---------------------------------------------------------------------------
# Card dataclass
# ---------------------------------------------------------------------------
@dataclass
class Card:
    """
    Immutable data for one playing card.

    Fields
    ------
    suit : str
        One of "clubs", "diamonds", "hearts", "spades".
    rank : str
        Display name: "2"…"10", "J", "Q", "K", "A".
    value : int
        Chip value added when the card is scored (2–11).
    rank_index : int
        Numeric rank 0–12.  Used by the evaluator to detect Straights.
        Ace is always 12 here; the evaluator handles the A-low case (A=0).
    image_path : str
        Absolute path to the card's PNG sprite.  Resolved at construction.
        Falls back to `_FALLBACK_IMAGE` when the file doesn't exist.

    NOTE: Do NOT add arcade.Sprite or any rendering data here.
          This is pure game data, not a visual object.
    """

    suit: str
    rank: str
    value: int
    rank_index: int
    image_path: str = field(init=False)  # set in __post_init__

    def __post_init__(self) -> None:
        """
        Resolve the image path after the dataclass is constructed.

        TODO: The filename pattern depends on your assets folder.
              Check `docs/todo.md` section 2c for the naming convention.
              Example filename: "card_hearts_K.png"
                                 ^---- suit ----^ ^rank^

        Steps you need to complete:
          1. Build the filename string using self.suit and self.rank.
             For ranks 2–9 you may need zero-padding (e.g. "02", "05").
             Check the actual filenames in src/assets/cards/PNG/Cards (large)/
          2. Join with CARDS_DIR using os.path.join(...)
          3. If the file doesn't exist, fall back to _FALLBACK_IMAGE
        """
        filename = f"card_{self.suit}_{self.rank}.png"
        path = os.path.join(CARDS_DIR, filename)
        self.image_path = path if os.path.exists(path) else _FALLBACK_IMAGE

    def __repr__(self) -> str:
        # Handy when you print cards during debugging
        return f"Card({self.rank} of {self.suit})"


# ---------------------------------------------------------------------------
# Deck class
# ---------------------------------------------------------------------------
class Deck:
    """
    A standard 52-card deck that tracks drawn and remaining cards.

    Lifecycle
    ---------
    1. __init__()  → builds all 52 Card objects, calls shuffle()
    2. draw(n)     → remove and return n cards from the top of the deck
    3. When fewer than n cards remain, auto-reshuffle (reclaim drawn cards)
    4. remaining() → int, how many undrawn cards are left

    Internal storage
    ----------------
    _cards   : list[Card]  – cards still available to draw (the "deck pile")
    _discard : list[Card]  – cards that have been drawn (to reshuffle later)

    Usage
    -----
    deck = Deck()
    hand: list[Card] = deck.draw(8)
    print(deck.remaining())  # 44
    """

    def __init__(self) -> None:
        self._cards: list[Card] = []
        self._discard: list[Card] = []
        for suit in _SUITS:
            for rank_name, value, rank_index in _RANK_DEFS:
                card = Card(
                    suit=suit, rank=rank_name, value=value, rank_index=rank_index
                )
                self._cards.append(card)
        self.shuffle()

    # ------------------------------------------------------------------
    def shuffle(self) -> None:
        """
        Shuffle the deck.

        Also reclaims any cards from _discard back into _cards so a
        depleted deck can be reused for the next deal.

        TODO:
          1. self._cards.extend(self._discard)
          2. self._discard.clear()
          3. random.shuffle(self._cards)
        """
        self._cards.extend(self._discard)
        self._discard.clear()
        random.shuffle(self._cards)

    # ------------------------------------------------------------------
    def draw(self, n: int = 1) -> list[Card]:
        """
        Draw (remove) n cards from the deck and return them.

        If fewer than n cards remain, shuffle first (reclaim discards),
        then draw.  This prevents the game from crashing mid-round.

        Parameters
        ----------
        n : int
            Number of cards to draw.

        Returns
        -------
        list[Card]
            The drawn cards (length may be < n only if the total deck
            has fewer than n unique cards — should never happen in practice).

        TODO:
          1. if len(self._cards) < n: self.shuffle()
          2. drawn = self._cards[:n]
          3. self._cards = self._cards[n:]   (remove from top)
          4. self._discard.extend(drawn)
          5. return drawn
        """
        if len(self._cards) < n:
            self.shuffle()
        drawn = self._cards[:n]
        self._cards = self._cards[n:]
        self._discard.extend(drawn)
        return drawn

    # ------------------------------------------------------------------
    def remaining(self) -> int:
        """Return how many cards are still in the drawable pile."""
        return len(self._cards)
