"""
constants.py
------------
Central location for all game-wide constants: colours, asset paths, and
game tuning values.  Import from here in every other module.
"""

import os

# ---------------------------------------------------------------------------
# Color Palette – Balatro-style warm neon
# ---------------------------------------------------------------------------
BG_DIM_COLOR   = (18, 12, 11)
NEON_PINK      = (198, 74, 60)
NEON_CYAN      = (234, 189, 111)
NEON_PURPLE    = (86, 45, 39)
DARK_PURPLE    = (32, 16, 15)
LIGHT_GRAY     = (246, 232, 210)
GOLD           = (255, 214, 120)

# ---------------------------------------------------------------------------
# Asset Paths
# ---------------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "src", "assets")
CARDS_DIR  = os.path.join(ASSETS_DIR, "cards", "PNG", "Cards (large)")
TEX_DIR    = os.path.join(ASSETS_DIR, "textures")
UI_DIR     = os.path.join(ASSETS_DIR, "ui")

# ---------------------------------------------------------------------------
# Game Tuning
# ---------------------------------------------------------------------------
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE  = "Halando - Balatro-style Prototype"

HAND_SIZE     = 8          # Cards dealt per hand
MAX_SELECTED  = 5          # Max cards selectable at once
CARD_SCALE    = 0.8        # Scale of gameplay cards
MENU_CARD_SCALE = 0.68     # Scale of decorative menu cards

TARGET_SCORE  = 5_000
START_GOLD    = 10
START_HANDS   = 4
START_DISCARDS = 4
