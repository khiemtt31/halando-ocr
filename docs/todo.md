# Halando – Development Checklist

Track what is **done**, **in progress**, and **not yet started** across all phases.

---

## Phase 00 – Foundation (All Done ✅)

- [x] Python 3.11 + venv set up
- [x] `arcade==3.3.3` installed
- [x] Project directory structure created (`src/`, `views/`, `sprites/`, `ui/`, `assets/`)
- [x] `main.py` – entry point wired
- [x] `window.py` – `HalandoWindow` creates and switches views
- [x] `constants.py` – colours, paths, tuning values centralised
- [x] `ui/button.py` – `CustomButton` with hover + click
- [x] `sprites/floating_card.py` – animated menu decoration card
- [x] `views/main_menu_view.py` – animated menu with floating cards and logo wobble
- [x] Asset fallbacks – game launches without any asset files (text fallback for logo, colour fallback for background)

---

## Phase 01 – Playable Core Game Loop ✅

> Plan: [`docs/plan/plan-phase-01.md`](plan/plan-phase-01.md)

### Core Logic (`src/core/`)

- [x] `core/__init__.py` – package marker created
- [x] `core/deck.py`
  - [x] `_RANK_DEFS` – all 13 ranks (2–A) with chip values and rank indices
  - [x] `Card` dataclass – suit, rank, value, rank_index, image_path auto-resolved
  - [x] `Card.__post_init__` – builds filename, falls back to `card_spades_A.png`
  - [x] `Deck.__init__` – builds all 52 Card objects, calls shuffle
  - [x] `Deck.shuffle()` – reclaims discard pile, random.shuffle
  - [x] `Deck.draw(n)` – removes n cards from top; auto-reshuffles when low
  - [x] `Deck.remaining()` – returns len of drawable pile
  - [x] **Bug fixed**: `draw()` had `self._cards = self._cards[:n]` (kept drawn cards) → corrected to `self._cards[n:]`
- [x] `core/hand_evaluator.py`
  - [x] `HAND_TABLE` – 10 hand types with base Chips × Mult
  - [x] `HandResult` dataclass
  - [x] `_rank_groups()` – Counter by rank_index
  - [x] `_is_flush()` – all 5 same suit
  - [x] `_is_straight()` – consecutive 5 ranks, including A-low wheel (A-2-3-4-5)
  - [x] `_cards_with_rank()` – filter cards by rank
  - [x] `_make_result()` – convenience builder
  - [x] `evaluate()` – detects all 10 hand types in priority order
- [x] `core/scoring.py`
  - [x] `calculate_score()` – base_chips + card values; delegates to apply_jokers stub
  - [x] `final_score()` – returns int(chips × mult)
  - [x] `apply_jokers()` – Phase 01 stub (pass-through, ready for Phase 02)

### Gameplay View (`src/views/gameplay_view.py`)

- [x] `_load_jokers()` – fixed Arcade 3.x crash (`load_texture()` no longer accepts `x=`, `y=`); now uses PIL for spritesheet cropping with graceful fallback
- [x] Imports wired – `from core.deck import Deck`, `evaluate`, `calculate_score`, `final_score`
- [x] `self.deck: Deck` added to instance state
- [x] `self.round_score: int` – cumulative score across all hands in a round
- [x] `self._pending_chips / _pending_mult / _hand_name` – pre-computed per hand
- [x] `setup_game()` – creates `Deck()`, resets `round_score`, resets `game_over`
- [x] `deal_hand()` – draws from real deck (`self.deck.draw(HAND_SIZE)`) instead of random helper
- [x] `_replace_discarded()` – draws replacements from deck, not random
- [x] `play_hand_action()` – calls `evaluate()` + `calculate_score()`, stores pending result
- [x] Animation Stage 1 – pulses cards visually, commits `round_score += final_score(...)` at end
- [x] Animation Stage 3 – win check uses `round_score >= target_score` (not per-hand total)
- [x] `_draw_score_panel()` – displays `round_score` as cumulative total
- [x] `_draw_game_over_overlay()` – win/loss overlay
- [x] `on_key_press()` – R restarts, M returns to menu
- [x] `self.game_over` state blocks input after round ends

### Sprites

- [x] `sprites/gameplay_card.py` – `GamePlayCard` with lerp animation, selection lift, hover scale

---

## Phase 02 – Shop, Jokers & Multi-Blind Run (Not Started 🔲)

> Plan: [`docs/plan/plan-phase-02.md`](plan/plan-phase-02.md)

### New Core Files

- [ ] `core/joker.py`
  - [ ] `JokerEffect` dataclass (effect_type, amount, condition)
  - [ ] `Joker` class (id, name, description, cost, effect)
  - [ ] `make_greedy_joker()` – +4 Mult always
  - [ ] `make_lusty_joker()` – +3 Mult if hand has Heart
  - [ ] `make_wrathful_joker()` – +3 Mult if hand has Spade
  - [ ] `make_gluttonous_joker()` – +3 Mult if hand has Club
  - [ ] `ALL_JOKERS` list – all available jokers the shop can sell
- [ ] `core/run_state.py`
  - [ ] `RunState` class (ante, blind, gold, jokers list)
  - [ ] `current_target()` – scaled blind target by ante
  - [ ] `advance_blind()` – progress Small → Big → Boss → next Ante
  - [ ] `earn_gold()` / `spend_gold()`

### Core Modifications

- [ ] `core/scoring.py` – implement `apply_jokers()` with real condition checking
- [ ] `constants.py` – add `MAX_JOKERS`, `BLIND_BASES` dict

### New Views

- [ ] `views/shop_view.py`
  - [ ] `on_show_view()` – generate 2–3 random jokers for sale
  - [ ] `on_draw()` – joker cards, gold display, owned jokers row, CONTINUE button
  - [ ] `on_mouse_press()` – buy joker, CONTINUE transitions to next round
  - [ ] `_draw_joker_card()` – neon card with name + description + cost

### View / Window Modifications

- [ ] `window.py` – add `shop_view` attribute; wire transitions
- [ ] `views/gameplay_view.py`
  - [ ] Accept `RunState` parameter in `setup_game()`
  - [ ] Use `run_state.current_target()` for blind target
  - [ ] On WIN: `run_state.earn_gold(4)`, `advance_blind()`, transition to `ShopView`
  - [ ] On LOSS: overlay shows final ante/blind reached

---

## Phase 03 – Polish & Persistence (Future 🔮)

- [ ] Sound effects (card flip, scoring, win/loss)
- [ ] Background music
- [ ] Proper Options screen (volume, fullscreen, resolution)
- [ ] Collection / deck-viewer screen
- [ ] Persist run state to disk (high scores, unlock tracking)
- [ ] Tarot / Planet cards
- [ ] Vouchers
- [ ] Deck customisation (add / remove cards)
- [ ] Boss Blind special rules (e.g. "No Flushes", "Must play 4+ cards")

---

## Asset Files Status

| Asset | Location | Status |
|---|---|---|
| `background.png` | `src/assets/textures/background.png` | Add any 1024×768+ dark image |
| `logo.png` | `src/assets/ui/logo.png` | Optional – text fallback if missing |
| Card PNGs (`card_{suit}_{rank}.png`) | `src/assets/cards/PNG/Cards (large)/` | **Required** for real card art |
| `joker_sprites.png` | `src/assets/textures/joker_sprites.png` | Optional – 512×512 3×2 grid |

---

## Quick Run Reference

```bash
# From project root with venv active:
source venv/bin/activate
python src/main.py

# In-game controls (Phase 01):
# Click cards       → select / deselect (up to 5)
# PLAY HAND         → evaluate + score selected cards
# DISCARD           → discard selected, draw replacements
# MAIN MENU         → return to menu
# R (game-over)     → restart round
# M (game-over)     → return to main menu
```
