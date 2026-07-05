"""
core/__init__.py
----------------
Marks `src/core/` as a Python package.
This file is intentionally empty.

The `core` package contains ALL pure game logic:
  deck.py           → 52-card Deck, Card dataclass
  hand_evaluator.py → Poker hand detection
  scoring.py        → Chips × Mult calculation table

IMPORTANT RULE FOR THIS PACKAGE:
  Do NOT import arcade here or in any core/ module.
  Core logic must be pure Python so it can be unit-tested
  without a display and reused in future phases.
"""
