"""
ui/balatro_theme.py
-------------------
Shared drawing helpers for the Balatro-inspired sketch screens.
"""

from __future__ import annotations

from dataclasses import dataclass

import arcade


BACKGROUND = (18, 12, 11)
BACKGROUND_ALT = (29, 16, 15)
PANEL = (54, 28, 23)
PANEL_DARK = (32, 16, 15)
PANEL_LIGHT = (76, 40, 31)
ACCENT = (233, 189, 111)
ACCENT_SOFT = (247, 218, 156)
TEXT = (246, 232, 210)
TEXT_MUTED = (187, 160, 135)
TEXT_DIM = (137, 112, 95)
RED = (198, 74, 60)
GREEN = (108, 158, 98)
BLUE = (91, 136, 188)
PURPLE = (150, 104, 200)
SHADOW = (0, 0, 0, 120)


def draw_background(width: float, height: float) -> None:
    """Draw a layered backdrop that reads like Balatro's warm table UI."""
    arcade.draw_rect_filled(
        arcade.rect.XYWH(width / 2, height / 2, width, height),
        BACKGROUND,
    )
    arcade.draw_circle_filled(-60, height + 80, width * 0.8, (255, 170, 120, 28))
    arcade.draw_circle_filled(width + 120, -60, width * 0.75, (70, 40, 110, 24))
    arcade.draw_rect_filled(
        arcade.rect.XYWH(width / 2, height / 2, width, height),
        (0, 0, 0, 25),
    )


def draw_panel(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    *,
    fill: tuple[int, int, int] = PANEL,
    outline: tuple[int, int, int] = ACCENT,
    border_width: int = 3,
    shadow_offset: tuple[float, float] = (6, -6),
) -> None:
    """Draw a warm panel with a soft shadow."""
    arcade.draw_rect_filled(
        arcade.rect.XYWH(center_x + shadow_offset[0], center_y + shadow_offset[1], width, height),
        SHADOW,
    )
    arcade.draw_rect_filled(arcade.rect.XYWH(center_x, center_y, width, height), fill)
    arcade.draw_rect_outline(
        arcade.rect.XYWH(center_x, center_y, width, height),
        outline,
        border_width=border_width,
    )


def draw_header(
    title: str,
    subtitle: str,
    *,
    x: float,
    y: float,
    title_size: int = 42,
    subtitle_size: int = 14,
) -> None:
    arcade.draw_text(
        title,
        x,
        y,
        TEXT,
        font_size=title_size,
        anchor_x="left",
        anchor_y="center",
        bold=True,
    )
    arcade.draw_text(
        subtitle,
        x,
        y - title_size * 0.9,
        TEXT_MUTED,
        font_size=subtitle_size,
        anchor_x="left",
        anchor_y="center",
        italic=True,
    )


def draw_chip(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    label: str,
    value: str,
    *,
    accent: tuple[int, int, int] = ACCENT,
) -> None:
    draw_panel(center_x, center_y, width, height, fill=PANEL_DARK, outline=accent, border_width=2)
    arcade.draw_text(
        label,
        center_x - width * 0.38,
        center_y + 10,
        TEXT_MUTED,
        font_size=10,
        anchor_x="left",
        anchor_y="center",
        bold=True,
    )
    arcade.draw_text(
        value,
        center_x - width * 0.38,
        center_y - 10,
        TEXT,
        font_size=16,
        anchor_x="left",
        anchor_y="center",
        bold=True,
    )


def draw_meter(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    progress: float,
    *,
    fill: tuple[int, int, int] = RED,
    background: tuple[int, int, int] = PANEL_DARK,
    outline: tuple[int, int, int] = ACCENT,
) -> None:
    progress = max(0.0, min(1.0, progress))
    draw_panel(center_x, center_y, width, height, fill=background, outline=outline, border_width=2)
    inner_width = max(0.0, width - 10)
    filled_width = inner_width * progress
    arcade.draw_rect_filled(
        arcade.rect.XYWH(center_x - inner_width / 2 + filled_width / 2, center_y, filled_width, height - 10),
        fill,
    )


@dataclass(slots=True)
class MockCard:
    """Simple drawn card used on shell screens."""

    title: str
    subtitle: str
    accent: tuple[int, int, int] = ACCENT
    fill: tuple[int, int, int] = PANEL
    footer: str = ""
    ribbon: str = ""
    locked: bool = False

    def draw(
        self,
        center_x: float,
        center_y: float,
        *,
        width: float = 180,
        height: float = 240,
        selected: bool = False,
    ) -> None:
        fill = (34, 27, 24) if self.locked else self.fill
        outline = ACCENT_SOFT if selected else self.accent
        draw_panel(center_x, center_y, width, height, fill=fill, outline=outline, border_width=3)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(center_x, center_y + height / 2 - 18, width - 14, 18),
            (255, 255, 255, 18),
        )
        arcade.draw_text(
            self.title.upper(),
            center_x,
            center_y + 40,
            TEXT,
            font_size=18,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        arcade.draw_text(
            self.subtitle,
            center_x,
            center_y + 8,
            TEXT_MUTED,
            font_size=12,
            anchor_x="center",
            anchor_y="center",
        )
        if self.ribbon:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(center_x, center_y - 54, width - 24, 26),
                (0, 0, 0, 60),
            )
            arcade.draw_text(
                self.ribbon,
                center_x,
                center_y - 54,
                ACCENT_SOFT,
                font_size=11,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )
        if self.footer:
            arcade.draw_text(
                self.footer,
                center_x,
                center_y - 88,
                TEXT_DIM,
                font_size=10,
                anchor_x="center",
                anchor_y="center",
            )
        if self.locked:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(center_x, center_y, width - 20, height - 20),
                (0, 0, 0, 86),
            )
            arcade.draw_text(
                "LOCKED",
                center_x,
                center_y,
                ACCENT_SOFT,
                font_size=16,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )
