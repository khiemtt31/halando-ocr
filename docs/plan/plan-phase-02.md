# Plan – Phase 02: Shop, Jokers & Multi-Blind Run

> **Goal:** After the player beats a Blind (or loses), they enter a **Shop screen**
> where they can buy Joker cards with the gold they earn each round.
> Jokers persist across rounds and apply effects during scoring — making each
> run feel different.  Add two more blinds per ante so there is a proper
> game loop with progression.

---

## What Phase 01 Delivered (recap)

| Feature | Status |
|---|---|
| Real 52-card deck (no repeats) | ✅ Done |
| All 10 poker hand types detected | ✅ Done |
| Chips × Mult scoring per hand | ✅ Done |
| Round score accumulates across 4 hands | ✅ Done |
| Win / Loss overlay + R restart / M menu | ✅ Done |
| Joker visual placeholder (PIL crop) | ✅ Done |

---

## Phase 02 Scope

### ✅ IN scope
- **Ante system**: Small Blind → Big Blind → Boss Blind (3 blinds × N antes)
- **Gold reward**: earn gold after each blind clear (`gold += 4` base)
- **Shop screen** (`ShopView`): buy Jokers, browse items between rounds
- **Joker data model** (`core/joker.py`): each Joker has a trigger + effect
- **Wire jokers to scoring**: `apply_jokers()` in `scoring.py` reads live Joker objects
- **At least 4 Jokers** with different effects:
  - **Greedy Joker** — `+4 Mult` each hand
  - **Lusty Joker** — `+3 Mult` if hand contains a Heart
  - **Wrathful Joker** — `+3 Mult` if hand contains a Spade
  - **Gluttonous Joker** — `+3 Mult` if hand contains a Club
- **Run state manager** (`core/run_state.py`): track current ante, blind, gold, owned jokers across the whole run

### ❌ OUT of scope (Phase 03+)
- Tarot / Planet / Spectral cards
- Vouchers
- Deck customisation (adding / removing cards)
- Persistent save files between sessions
- Sound / music

---

## New Files to Create

```
src/
├── core/
│   ├── joker.py          ← Joker data model + all joker definitions
│   └── run_state.py      ← Persistent run data shared across views
├── views/
│   └── shop_view.py      ← ShopView: browse and buy Jokers
```

---

## Files to Modify

| File | What changes |
|---|---|
| `constants.py` | Add ante config: `ANTES`, blind targets per ante |
| `window.py` | Add `shop_view` attribute; transition to shop after blind clear |
| `views/gameplay_view.py` | On win: transition to `ShopView`; on loss: show game-over overlay |
| `core/scoring.py` | `apply_jokers()` reads real Joker objects and applies effects |

---

## Detailed File Plan

### `src/core/joker.py`

```
DATACLASS  JokerEffect
  - effect_type: str       ("add_mult", "add_chips", "multiply_mult")
  - amount: float
  - condition: str | None  ("has_heart", "has_spade", "has_club", "has_diamond", None=always)

CLASS  Joker
  - id: str                unique identifier  e.g. "joker_greedy"
  - name: str              display name       e.g. "Greedy Joker"
  - description: str       tooltip text
  - cost: int              gold cost in shop  (default 5)
  - effect: JokerEffect

# Factory functions that return pre-built Joker objects
def make_greedy_joker() → Joker     # +4 Mult always
def make_lusty_joker()  → Joker     # +3 Mult if hand has Heart
def make_wrathful_joker()→ Joker    # +3 Mult if hand has Spade
def make_gluttonous_joker()→ Joker  # +3 Mult if hand has Club

# List of all available jokers the shop can sell
ALL_JOKERS: list[Joker] = [make_greedy_joker(), ...]
```

---

### `src/core/run_state.py`

```
CLASS  RunState
  ante:      int       current ante (1-based)
  blind:     int       0=Small, 1=Big, 2=Boss
  gold:      int       total gold owned
  jokers:    list[Joker]   jokers the player owns (max 5)

  # Blind target for current position
  def current_target() → int
      # Small Blind: 300 × (2^(ante-1))
      # Big Blind:   450 × (2^(ante-1))
      # Boss Blind:  600 × (2^(ante-1))

  def advance_blind() → bool
      # Move to next blind.  Returns True if a new ante started.
      # After Boss Blind, ante += 1, blind resets to 0

  def earn_gold(amount: int) → None
  def spend_gold(amount: int) → bool  # returns False if not enough
```

---

### `src/views/shop_view.py`

```
CLASS  ShopView(arcade.View)

  on_show_view():
    - Generate 2–3 random Jokers from ALL_JOKERS for sale (not already owned)
    - Display them as clickable cards with cost shown
    - Show "CONTINUE" button to start next round

  on_draw():
    - Dark background with neon border
    - Title: "SHOP — Ante X, Blind Y"
    - Show jokers for sale as cards with name + description + cost
    - Show player's gold in top right
    - Show currently owned jokers in a row at the bottom
    - "CONTINUE" button

  on_mouse_press():
    - If clicked a joker: spend gold, add to run_state.jokers
    - If clicked CONTINUE: transition to GamePlayView.setup_game()

  _draw_joker_card(joker, x, y, is_buyable):
    - Draws a neon-bordered card with joker name and description
    - Shows cost; grays out if player can't afford it
```

---

### Constants changes (`constants.py`)

```python
MAX_JOKERS    = 5     # max jokers the player can hold at once

# Blind target multipliers per ante (base × multiplier)
BLIND_BASES = {
    "Small": 300,
    "Big":   450,
    "Boss":  600,
}
# Target for Ante N = BLIND_BASES[blind] * (2 ** (ante - 1))
# Ante 1 Small = 300,  Ante 1 Boss = 600
# Ante 2 Small = 600,  Ante 2 Boss = 1200
# Ante 3 Small = 1200, Ante 3 Boss = 2400
```

---

### `core/scoring.py` — `apply_jokers` implementation

```python
def apply_jokers(jokers, chips, mult, played_cards=None):
    # played_cards needed to check conditions like "has_heart"
    suits_in_hand = {c.suit for c in (played_cards or [])}
    for joker in jokers:
        effect = joker.effect
        # Check condition
        if effect.condition is None:
            triggers = True
        elif effect.condition == "has_heart":
            triggers = "hearts" in suits_in_hand
        elif effect.condition == "has_spade":
            triggers = "spades" in suits_in_hand
        elif effect.condition == "has_club":
            triggers = "clubs" in suits_in_hand
        elif effect.condition == "has_diamond":
            triggers = "diamonds" in suits_in_hand
        else:
            triggers = False
        # Apply effect
        if triggers:
            if effect.effect_type == "add_mult":
                mult += effect.amount
            elif effect.effect_type == "add_chips":
                chips += int(effect.amount)
            elif effect.effect_type == "multiply_mult":
                mult *= effect.amount
    return chips, mult
```

---

### `views/gameplay_view.py` — transition changes

```
setup_game(run_state: RunState):
  - Accept a RunState parameter
  - self.hands_left = START_HANDS
  - self.discards_left = START_DISCARDS
  - self.target_score = run_state.current_target()
  - self.deck = Deck()

On WIN (Stage 3):
  - run_state.earn_gold(4)        # base gold per blind
  - run_state.advance_blind()
  - transition to ShopView

On LOSS:
  - show game-over overlay (already done in Phase 01)
  - R restarts from Ante 1 with a fresh RunState
```

---

## Coding Order for Phase 02

```
Step 1  → constants.py            add MAX_JOKERS, BLIND_BASES
Step 2  → core/joker.py           Joker dataclass + 4 factory functions
Step 3  → core/run_state.py       RunState class + current_target(), advance_blind()
Step 4  → core/scoring.py         implement apply_jokers() with conditions
Step 5  → views/shop_view.py      ShopView skeleton → on_draw → on_mouse_press
Step 6  → window.py               add shop_view; wire transitions
Step 7  → views/gameplay_view.py  accept RunState param; transition to shop on win
Step 8  → TEST: full run          menu → play → shop → play → shop …
```

---

## How Jokers Feel in Play

```
Example run with Greedy Joker (always +4 Mult):

  Hand: Pair (K,K)
  Base:  Chips=10, Mult=2
  Cards: K(10)+K(10) = Chips=30
  Joker: Mult 2 + 4 = 6
  Final: 30 × 6 = 180 points

  vs. without joker: 30 × 2 = 60 points  →  3× multiplier from one joker!

Example with Lusty Joker (Hearts → +3 Mult):

  Hand: Flush (all hearts)
  Base:  Chips=35, Mult=4
  Cards: +7+8+9+10+J = Chips=35+44=79
  Joker: hand has hearts → Mult 4 + 3 = 7
  Final: 79 × 7 = 553 points
```

---

## Architecture After Phase 02

```
main.py
  └── HalandoWindow (window.py)
        ├── MainMenuView    → "PLAY RUN" → creates RunState → GamePlayView
        ├── GamePlayView    → on WIN → ShopView
        │     ├── RunState              (core/run_state.py)   ← NEW
        │     ├── Deck                  (core/deck.py)
        │     ├── evaluate()            (core/hand_evaluator.py)
        │     ├── calculate_score()     (core/scoring.py)
        │     └── apply_jokers()        (core/scoring.py)      ← WIRED
        └── ShopView        → on CONTINUE → GamePlayView       ← NEW
              ├── RunState              (shared reference)
              └── ALL_JOKERS            (core/joker.py)        ← NEW
```
