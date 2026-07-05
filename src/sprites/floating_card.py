"""
sprites/floating_card.py
------------------------
FloatingCard – decorative, bobbing playing-card sprite used on the
main-menu screen.  Fully compatible with Arcade 3.3.3.
"""

import math
import random
import arcade


class FloatingCard(arcade.Sprite):
    """
    An animated playing-card sprite that bobs, rotates, and scales on hover.

    Arcade 3.3.3 notes
    ------------------
    * ``sprite.scale`` is a plain ``tuple`` – read with ``self.scale[0]``.
    * ``collides_with_point`` takes a single ``(x, y)`` tuple (not two args).
    """

    def __init__(self, filename: str, scale: float = 1.0):
        super().__init__(filename, scale=scale)
        self.base_scale: float  = scale
        self.target_scale: float = scale

        # Randomise phase so cards don't move in sync
        self.time_accumulator: float = random.random() * 10.0
        self.float_speed: float      = random.uniform(1.5, 2.5)
        self.float_amplitude: float  = random.uniform(6.0, 12.0)
        self.base_angle: float       = random.uniform(-10.0, 10.0)

        self.is_hovered: bool = False

    # ------------------------------------------------------------------
    def update_animation(self, delta_time: float) -> None:
        self.time_accumulator += delta_time

        # Bobbing & gentle rotation when idle
        if not self.is_hovered:
            self.center_y += (
                math.sin(self.time_accumulator * self.float_speed)
                * self.float_amplitude
                * delta_time
            )
            self.angle = self.base_angle + math.cos(self.time_accumulator * 1.2) * 4.0
        else:
            # Snap upright when hovered
            self.angle += (0.0 - self.angle) * 0.15

        # Smooth scale lerp – scale is a plain tuple in Arcade 3.3.3
        current = self.scale[0]
        new_scale = current + (self.target_scale - current) * 0.2
        self.scale = (new_scale, new_scale)
