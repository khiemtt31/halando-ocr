"""
core/scoring.py
---------------
PURPOSE:
  Translate a HandResult + the played cards into a final (chips, mult) pair
  that gets added to the round's running score.

FORMULA (Balatro-style):
  round_score += int(chips * mult)
  where:
    chips = hand.base_chips  +  sum(card.value for card in played_cards)
    mult  = hand.base_mult
    (Joker effects are added in Phase 02 via apply_jokers())

WHY SEPARATE FROM HAND_EVALUATOR?
  hand_evaluator knows WHAT hand you have.
  scoring knows HOW MANY POINTS that hand gives.
  Changing scoring rules (e.g. "+10 Chips for Flush") only touches this file.

NO ARCADE IMPORTS — pure Python only.

USAGE EXAMPLE:
  from core.hand_evaluator import evaluate
  from core.scoring import calculate_score, final_score

  result = evaluate(played_cards)
  chips, mult = calculate_score(result, played_cards)
  total = final_score(chips, mult)
  print(f"{result.hand_name}: {chips} × {mult} = {total}")
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.deck import Card
    from core.hand_evaluator import HandResult


# ---------------------------------------------------------------------------
# calculate_score
# ---------------------------------------------------------------------------

def calculate_score(
    result: "HandResult",
    played_cards: list["Card"],
) -> tuple[int, float]:
    """
    Compute the (chips, mult) pair from a HandResult and the played cards.

    Phase 01 rules
    --------------
    1. Start from the hand's base values:
         chips = result.base_chips
         mult  = result.base_mult

    2. Add each played card's chip value to chips:
         for card in played_cards:
             chips += card.value

       NOTE: Strictly speaking, only `result.scored_cards` contribute chip
       value in Balatro (kickers do not score).  For Phase 01 simplicity we
       add ALL played cards.  Tighten to scored_cards in Phase 02 if desired.

    3. Joker effects — delegated to apply_jokers() (stub in Phase 01).

    Parameters
    ----------
    result : HandResult
        Evaluated hand (name + base chips/mult + scored_cards).
    played_cards : list[Card]
        All cards the player chose to play (1–5 cards).

    Returns
    -------
    tuple[int, float]
        (chips, mult) — NOT yet multiplied together.
        Pass to final_score() to get the integer total.
    """
    chips: int   = result.base_chips
    mult:  float = result.base_mult

    # Each played card adds its face value to the chip count
    for card in played_cards:
        chips += card.value

    # Phase 01: no joker effects yet
    chips, mult = apply_jokers([], chips, mult)

    return chips, mult


# ---------------------------------------------------------------------------
# final_score
# ---------------------------------------------------------------------------

def final_score(chips: int, mult: float) -> int:
    """
    Multiply chips × mult and return the integer result.

    This is the number added to the round's cumulative score.

    Parameters
    ----------
    chips : int
        Total chip count (base + card values + joker chip bonuses).
    mult : float
        Multiplier (base + joker mult bonuses).

    Returns
    -------
    int
        The final score contribution from this single hand play.
    """
    return int(chips * mult)


# ---------------------------------------------------------------------------
# apply_jokers  (STUB — Phase 02 will fill this in)
# ---------------------------------------------------------------------------

def apply_jokers(
    jokers: list,       # list of Joker objects (defined in Phase 02)
    chips: int,
    mult: float,
) -> tuple[int, float]:
    """
    Apply all active Joker effects in sequence to chips and mult.

    Phase 01 stub — returns chips and mult unchanged.

    In Phase 02 each Joker will carry a trigger condition and an effect:
      - "+4 Mult"             → mult += 4
      - "+30 Chips"           → chips += 30
      - "×1.5 Mult if Flush"  → mult *= 1.5  (only when hand is a Flush)

    Parameters
    ----------
    jokers : list
        Active Joker objects (currently unused).
    chips : int
        Current chip total before joker effects.
    mult : float
        Current multiplier before joker effects.

    Returns
    -------
    tuple[int, float]
        Updated (chips, mult) after all joker effects are applied.
    """
    # Phase 01: no jokers wired — pass through unchanged
    return chips, mult
