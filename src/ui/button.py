"""
ui/button.py
------------
CustomButton – a hover-animated button drawn with Arcade 3.x primitives.
"""

import arcade
from constants import DARK_PURPLE, NEON_PURPLE, NEON_CYAN, NEON_PINK, LIGHT_GRAY


class CustomButton:
    """A simple interactive button with hover scale animation."""

    def __init__(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        text: str,
        action_callback,
    ):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.height = height
        self.text = text
        self.action = action_callback

        # Interactive states
        self.scale: float = 1.0
        self.target_scale: float = 1.0
        self.is_hovered: bool = False

        # Style
        self.base_color = DARK_PURPLE
        self.hover_color = NEON_PURPLE
        self.outline_color = NEON_CYAN
        self.text_color = LIGHT_GRAY

    # ------------------------------------------------------------------
    def draw(self) -> None:
        # Smooth scale lerp (runs every frame inside draw)
        self.scale += (self.target_scale - self.scale) * 0.15

        w = self.width  * self.scale
        h = self.height * self.scale

        color = self.hover_color if self.is_hovered else self.base_color

        # Shadow
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.center_x + 5, self.center_y - 5, w, h),
            (0, 0, 0, 120),
        )
        # Background
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.center_x, self.center_y, w, h),
            color,
        )
        # Outline
        outline_c = NEON_PINK if self.is_hovered else self.outline_color
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.center_x, self.center_y, w, h),
            outline_c,
            border_width=3,
        )
        # Label
        arcade.draw_text(
            self.text,
            self.center_x,
            self.center_y,
            self.text_color,
            font_size=16 * self.scale,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    # ------------------------------------------------------------------
    def check_hover(self, x: float, y: float) -> bool:
        left   = self.center_x - self.width  / 2
        right  = self.center_x + self.width  / 2
        bottom = self.center_y - self.height / 2
        top    = self.center_y + self.height / 2

        self.is_hovered = left <= x <= right and bottom <= y <= top
        self.target_scale = 1.08 if self.is_hovered else 1.0
        return self.is_hovered

    # ------------------------------------------------------------------
    def on_click(self) -> None:
        if self.action:
            self.action()
