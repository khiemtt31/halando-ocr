"""
views/run_setup_view.py
-----------------------
RunSetupView – the deck and stake selection screen.
"""

from __future__ import annotations

import arcade

from constants import LIGHT_GRAY, GOLD, NEON_PINK, NEON_CYAN
from ui.button import CustomButton
from ui.balatro_theme import (
    ACCENT,
    ACCENT_SOFT,
    BLUE,
    GREEN,
    MockCard,
    PANEL,
    PANEL_DARK,
    RED,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    draw_background,
    draw_chip,
    draw_header,
    draw_meter,
    draw_panel,
)


class RunSetupView(arcade.View):
    """Choose a starting deck and stake before entering the table."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.buttons: list[CustomButton] = []
        self.deck_index: int = 0
        self.stake_index: int = 0
        self.toast_msg: str = "Pick a deck, then start the run."

        self.deck_options = [
            {
                "name": "Red Deck",
                "subtitle": "+1 discard per round",
                "ribbon": "SAFE START",
                "footer": "Best for learning the route.",
                "accent": RED,
            },
            {
                "name": "Blue Deck",
                "subtitle": "+1 hand per round",
                "ribbon": "MORE FLEX",
                "footer": "Lets you see more of the draw.",
                "accent": BLUE,
            },
            {
                "name": "Yellow Deck",
                "subtitle": "Start with extra gold",
                "ribbon": "SHOP READY",
                "footer": "Good for early shop testing.",
                "accent": GOLD,
            },
        ]

        self.stake_options = [
            "White Stake",
            "Red Stake",
            "Green Stake",
            "Black Stake",
            "Blue Stake",
            "Purple Stake",
            "Orange Stake",
            "Gold Stake",
        ]

    def on_show_view(self) -> None:
        self._build_buttons()

    def _build_buttons(self) -> None:
        width = self.window.width
        self.buttons = [
            CustomButton(120, 60, 180, 42, "BACK", self.back_to_menu),
            CustomButton(width / 2, 60, 220, 46, "START RUN", self.start_run),
            CustomButton(width - 120, 60, 180, 42, "NEXT DECK", self.next_deck),
            CustomButton(width - 120, 118, 180, 42, "NEXT STAKE", self.next_stake),
        ]

    def back_to_menu(self) -> None:
        self.window.show_view(self.window.main_menu_view)

    def start_run(self) -> None:
        deck = self.deck_options[self.deck_index]
        stake = self.stake_options[self.stake_index]
        self.window.gameplay_view.run_profile = {
            "deck": deck["name"],
            "stake": stake,
        }
        self.window.gameplay_view.setup_game()
        self.window.show_view(self.window.gameplay_view)

    def next_deck(self) -> None:
        self.deck_index = (self.deck_index + 1) % len(self.deck_options)
        self.toast_msg = f"Selected {self.deck_options[self.deck_index]['name']}."

    def next_stake(self) -> None:
        self.stake_index = (self.stake_index + 1) % len(self.stake_options)
        self.toast_msg = f"Selected {self.stake_options[self.stake_index]}."

    def on_draw(self) -> None:
        self.clear()
        draw_background(self.window.width, self.window.height)
        draw_header(
            "RUN SETUP",
            "Choose a starter deck and stake before the table opens.",
            x=60,
            y=self.window.height - 50,
        )

        draw_panel(self.window.width / 2, self.window.height / 2 + 10, self.window.width - 120, 520)

        self._draw_deck_picker()
        self._draw_stake_ladder()
        self._draw_summary()

        arcade.draw_text(
            self.toast_msg,
            self.window.width / 2,
            22,
            TEXT,
            font_size=12,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        for button in self.buttons:
            button.draw()

    def _draw_deck_picker(self) -> None:
        x = 320
        y = self.window.height / 2 + 18
        draw_panel(x, y, 520, 430, fill=PANEL_DARK, outline=ACCENT, border_width=3)
        arcade.draw_text("STARTING DECK", x - 230, y + 180, TEXT_MUTED, 12, anchor_x="left", bold=True)
        deck = self.deck_options[self.deck_index]
        MockCard(
            deck["name"],
            deck["subtitle"],
            accent=deck["accent"],
            fill=PANEL,
            footer=deck["footer"],
            ribbon=deck["ribbon"],
        ).draw(x, y + 20, width=260, height=320, selected=True)

        preview_left = self.deck_options[(self.deck_index - 1) % len(self.deck_options)]
        preview_right = self.deck_options[(self.deck_index + 1) % len(self.deck_options)]
        MockCard(preview_left["name"], preview_left["subtitle"], accent=preview_left["accent"], fill=(43, 24, 22), footer="Preview").draw(x - 160, y - 130, width=150, height=180)
        MockCard(preview_right["name"], preview_right["subtitle"], accent=preview_right["accent"], fill=(43, 24, 22), footer="Preview").draw(x + 160, y - 130, width=150, height=180)

        draw_chip(x, y - 185, 220, 52, "Deck", deck["name"], accent=deck["accent"])

    def _draw_stake_ladder(self) -> None:
        x = self.window.width - 250
        y = self.window.height / 2 + 80
        draw_panel(x, y, 330, 430, fill=PANEL_DARK, outline=ACCENT_SOFT, border_width=3)
        arcade.draw_text("STAKE LADDER", x - 145, y + 180, TEXT_MUTED, 12, anchor_x="left", bold=True)

        step_y = y + 130
        for index, stake in enumerate(self.stake_options):
            selected = index == self.stake_index
            row_fill = PANEL if selected else (38, 22, 19)
            row_outline = ACCENT_SOFT if selected else TEXT_DIM
            draw_panel(x, step_y - index * 45, 230, 34, fill=row_fill, outline=row_outline, border_width=2)
            arcade.draw_text(
                stake,
                x - 100,
                step_y - index * 45,
                TEXT if selected else TEXT_MUTED,
                font_size=12,
                anchor_x="left",
                anchor_y="center",
                bold=selected,
            )

        draw_meter(x, y - 155, 250, 20, (self.stake_index + 1) / len(self.stake_options), fill=NEON_PINK, background=PANEL_DARK, outline=ACCENT)
        arcade.draw_text(
            f"Selected: {self.stake_options[self.stake_index]}",
            x,
            y - 188,
            TEXT,
            font_size=12,
            anchor_x="center",
            bold=True,
        )

    def _draw_summary(self) -> None:
        x = self.window.width / 2
        y = 115
        draw_panel(x, y, 760, 92, fill=(40, 21, 18), outline=ACCENT, border_width=2)
        arcade.draw_text(
            "Run notes: deck choice sets the starter feel, while stake is the difficulty ladder placeholder.",
            x,
            y + 16,
            TEXT_MUTED,
            font_size=12,
            anchor_x="center",
            anchor_y="center",
        )
        arcade.draw_text(
            "The gameplay logic can be wired to these choices later without changing this screen.",
            x,
            y - 14,
            TEXT_DIM,
            font_size=11,
            anchor_x="center",
            anchor_y="center",
        )

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        for button in self.buttons:
            button.check_hover(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        for btn in self.buttons:
            if btn.is_hovered:
                btn.on_click()
                return

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)
        self._build_buttons()
