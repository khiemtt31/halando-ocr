# Plan – Phase 01: Playable Core Game Loop

> **Goal:** When the player presses **PLAY RUN** from the main menu, a fully
> playable card-game round starts immediately.  
> Simple, clean, no skills, no shop — just **4 hands**, a proper 52-card deck,
> poker-hand evaluation, Chips × Mult scoring, and a win/loss screen.

---

## What Exists Right Now

| File | Status | Notes |
|---|---|---|
| `main.py` | ✅ Done | Entry point, unchanged |
| `window.py` | ✅ Done | Creates both views |
| `constants.py` | ✅ Done | Colours, paths, tuning |
| `ui/button.py` | ✅ Done | Hover + click button |
| `sprites/floating_card.py` | ✅ Done | Menu decoration |
| `sprites/gameplay_card.py` | ✅ Done | Hand card with lerp animation |
| `views/main_menu_view.py` | ✅ Done | Animated menu, PLAY → gameplay |
| `views/gameplay_view.py` | ⚠️ Partial | Renders cards but scoring is fake (random chips, hard-coded mult) |

### What is MISSING / BROKEN right now

1. **No real deck** – cards are picked with `random.choice` on 8 ranks, same card can appear multiple times.  
2. **No hand evaluator** – "scoring" just adds `card.value` raw and multiplies by 0.5 each card. No Pair, Flush, etc.  
3. **No Chips × Mult table** – every hand type should have a fixed Chips + Mult base.  
4. **No round structure** – game never truly ends; no win screen, no "Blind Defeated" screen.  
5. **No discard-then-draw** – cards replaced correctly visually, but drawn from unbounded random pool, not a real deck.

---

## Phase 01 Scope (Keep It Simple)

### ✅ IN scope
- Full 52-card deck built from scratch, shuffled, drawn without replacement
- 5-card poker hand evaluator: **High Card, Pair, Two Pair, Three of a Kind, Straight, Flush, Full House, Four of a Kind, Straight Flush, Royal Flush**
- Fixed **Chips × Mult base table** per hand type (Balatro-style numbers)
- 4 hands per round, 4 discards per round (already in constants)
- Win condition: total score ≥ TARGET\_SCORE
- Loss condition: hands\_left == 0 and score < TARGET\_SCORE
- Simple **win/loss overlay** drawn on top of the game screen (no new View needed)
- "Deal next hand" after playing (draw from remaining deck, reshuffle when empty)

### ❌ OUT of scope (future phases)
- Shop between rounds
- Joker card effects (keep placeholder, don't wire logic)
- Skills / special abilities
- Sound effects
- Persistence / save files

---

## New Files to Create

```
src/
├── core/                         ← NEW directory
│   ├── __init__.py               ← empty, marks it a package
│   ├── deck.py                   ← Deck class: build, shuffle, draw
│   ├── hand_evaluator.py         ← evaluate 1–5 cards → HandResult
│   └── scoring.py                ← Chips × Mult table + apply jokers (stub)
```

### Why a `core/` directory?
Game logic (deck, evaluator, scoring) must be **completely separate from rendering**.
This is the standard MVC / ECS pattern used in game development:

```
core/       ← pure Python, no arcade imports — easy to unit-test
sprites/    ← visual representation only
views/      ← orchestrates core + sprites, handles input
```

---

## Files to Modify

| File | What changes |
|---|---|
| `constants.py` | Add `HAND_CHIPS_MULT` dict for all 10 hand types |
| `views/gameplay_view.py` | Wire real Deck, real evaluator, real scoring; add win/loss overlay |

---

## Detailed File Plan

### `src/core/__init__.py`
Empty. Just marks `core/` as a Python package so you can do `from core.deck import Deck`.

---

### `src/core/deck.py`
Responsible for managing the 52-card pool.

```
CLASS  Card(dataclass)
  - suit: str          ("clubs", "diamonds", "hearts", "spades")
  - rank: str          ("2" … "A")
  - value: int         (2–10, J=10, Q=10, K=10, A=11)
  - rank_index: int    (0–12, used for straight detection)
  - image_path: str    (resolved on construction from CARDS_DIR)

CLASS  Deck
  __init__()           → build all 52 Card objects, call shuffle()
  shuffle()            → random.shuffle the internal list + reset drawn pile
  draw(n)              → pop n cards; auto-reshuffle if < n remain
  remaining()          → int, how many cards are left
```

---

### `src/core/hand_evaluator.py`
Pure logic, no arcade. Takes a list of `Card` objects, returns a result.

```
DATACLASS  HandResult
  - hand_name: str     ("Pair", "Flush", …)
  - base_chips: int    (from HAND_CHIPS_MULT table)
  - base_mult: float
  - scored_cards: list[Card]   (the cards that actually count)

FUNCTION  evaluate(cards: list[Card]) → HandResult
  - Accepts 1–5 Card objects
  - Detects the best hand among them
  - Returns a HandResult with the correct name and base values
  - Detection order (highest wins): Royal Flush → Straight Flush →
    Four of a Kind → Full House → Flush → Straight →
    Three of a Kind → Two Pair → Pair → High Card
```

---

### `src/core/scoring.py`
Translates a `HandResult` + played cards → final Chips and Mult.

```
HAND_CHIPS_MULT dict
  "High Card"         → (5,  1)
  "Pair"              → (10, 2)
  "Two Pair"          → (20, 2)
  "Three of a Kind"   → (30, 3)
  "Straight"          → (30, 4)
  "Flush"             → (35, 4)
  "Full House"        → (40, 4)
  "Four of a Kind"    → (60, 7)
  "Straight Flush"    → (100, 8)
  "Royal Flush"       → (100, 8)  ← same base, name differs for display

FUNCTION  calculate_score(result: HandResult, played_cards: list[Card]) → tuple[int, float]
  - Start from result.base_chips, result.base_mult
  - For each card in played_cards: chips += card.value
  - Return (total_chips, mult)
  - (Joker effects are a stub: just return unchanged for Phase 01)

FUNCTION  final_score(chips: int, mult: float) → int
  - return int(chips * mult)
```

---

### `views/gameplay_view.py` — changes

```
setup_game()
  - Create a new Deck()
  - Store as self.deck
  - Draw 8 cards → self.hand_cards

play_hand_action()
  - selected = [cards that are selected]
  - result = evaluate(selected)         ← from hand_evaluator
  - chips, mult = calculate_score(result, selected)
  - self.score_chips += chips
  - self.score_mult  = mult             (replace, not add)
  - self.toast_msg   = f"{result.hand_name}!"
  - Animate scoring stages (existing code)
  - After animation: remove selected cards, draw replacements from self.deck

_replace_discarded()
  - Draw new cards from self.deck instead of random

_check_win_loss()
  - Called at end of each hand
  - if total >= target: set self.game_over = "win"
  - elif hands_left == 0: set self.game_over = "loss"

on_draw()
  - If self.game_over is set, draw a semi-transparent overlay:
    WIN:  "BLIND DEFEATED!" in gold
    LOSS: "GAME OVER" in red
    Both show: "Press R to restart | M for Menu"

on_key_press()
  - 'R' → setup_game() (restart)
  - 'M' → show main menu
```

---

## Coding Order (do these IN ORDER)

```
Step 1  →  src/core/__init__.py          (empty file, 2 lines)
Step 2  →  src/core/deck.py             (Card dataclass + Deck class)
Step 3  →  src/core/hand_evaluator.py   (evaluate function)
Step 4  →  src/core/scoring.py          (HAND_CHIPS_MULT + calculate_score)
Step 5  →  constants.py                 (add HAND_CHIPS_MULT, clean up)
Step 6  →  views/gameplay_view.py       (wire everything together)
Step 7  →  TEST: python src/main.py     (click PLAY RUN, play hands)
```

---

## How the Scoring Feels (Target)

```
Example: You play a Pair (two 5s + three other cards)
  Base:    Chips=10, Mult=2
  Cards:   +5 +5 = Chips=20
  Final:   20 × 2 = 40 points

Example: You play a Flush (five hearts)
  Base:    Chips=35, Mult=4
  Cards:   K(10)+Q(10)+J(10)+7(7)+3(3) = Chips=35+40=75
  Final:   75 × 4 = 300 points
```

---

## Architecture Diagram

```
main.py
  └── HalandoWindow (window.py)
        ├── MainMenuView  (views/main_menu_view.py)
        │     └── [PLAY RUN] ──► GamePlayView.setup_game()
        └── GamePlayView  (views/gameplay_view.py)
              ├── Deck          (core/deck.py)          ← NEW
              ├── evaluate()    (core/hand_evaluator.py) ← NEW
              ├── calculate_score() (core/scoring.py)   ← NEW
              ├── GamePlayCard  (sprites/gameplay_card.py)
              └── CustomButton  (ui/button.py)
```

---

## After Phase 01 — What Phase 02 Could Be

- Shop screen between rounds (buy Jokers with gold)
- Multiple blinds / antes (Small → Big → Boss Blind)
- Joker effects wired to scoring
- Sound effects
