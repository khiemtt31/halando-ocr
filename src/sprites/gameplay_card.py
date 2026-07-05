"""
sprites/gameplay_card.py
------------------------
GamePlayCard – the interactive playing-card sprite used during a round.
Supports selection lift, smooth positional animation, and hover scaling.
Fully compatible with Arcade 3.3.3.
"""

import arcade
from constants import CARD_SCALE


class GamePlayCard(arcade.Sprite):
    """
    A hand card with smooth physics-like lerp movement and selection state.

    Arcade 3.3.3 notes
    ------------------
    * ``sprite.scale`` is a plain ``tuple`` – read with ``self.scale[0]``.
    * ``collides_with_point`` takes a single ``(x, y)`` tuple (not two args).
    """

    def __init__(
        self,
        filename: str,
        suit: str,
        rank: str,
        value: int,
        scale: float = CARD_SCALE,
    ):
        super().__init__(filename, scale=scale)
        self.suit  = suit
        self.rank  = rank
        self.value = value

        # Selection / animation state
        self.is_selected: bool    = False
        self.target_y_offset: float = 0.0
        self.y_offset: float       = 0.0

        # Store the base scale separately so we can lerp back to it
        self.base_scale: float  = scale
        self.target_scale: float = scale

        # Destination coordinates – we animate toward these each frame
        self.target_x: float = 0.0
        self.target_y: float = 0.0

    # ------------------------------------------------------------------
    def update(self) -> None:
        """Called automatically by SpriteList.update() every frame."""
        # Horizontal slide
        self.center_x += (self.target_x - self.center_x) * 0.2

        # Vertical lift when selected
        self.target_y_offset = 35.0 if self.is_selected else 0.0
        self.y_offset += (self.target_y_offset - self.y_offset) * 0.25
        self.center_y += (self.target_y + self.y_offset - self.center_y) * 0.2

        # Scale lerp – scale is a plain tuple in Arcade 3.3.3
        current = self.scale[0]
        new_s   = current + (self.target_scale - current) * 0.2
        self.scale = (new_s, new_s)
