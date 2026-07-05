"""
views/run_summary_view.py
-------------------------
RunSummaryView – end-of-run summary shell.
"""

from __future__ import annotations

import arcade

from constants import GOLD
from ui.button import CustomButton
from ui.balatro_theme import (
    ACCENT,
    GREEN,
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


class RunSummaryView(arcade.View):
    """Displays a placeholder run result card and action buttons."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.buttons: list[CustomButton] = []
        self.result_label: str = "RUN COMPLETE"
        self.score: int = 0
        self.hands_played: int = 0
        self.gold: int = 0
        self.best_hand: str = "High Card"
        self.deck_name: str = "Red Deck"
        self.stake_name: str = "White Stake"

    def configure(
        self,
        *,
        result_label: str,
        score: int,
        hands_played: int,
        gold: int,
        best_hand: str,
        deck_name: str,
        stake_name: str,
    ) -> None:
        self.result_label = result_label
        self.score = score
        self.hands_played = hands_played
        self.gold = gold
        self.best_hand = best_hand
        self.deck_name = deck_name
        self.stake_name = stake_name

    def on_show_view(self) -> None:
        self._build_buttons()

    def _build_buttons(self) -> None:
        width = self.window.width
        self.buttons = [
            CustomButton(120, 60, 180, 42, "NEW RUN", self.new_run),
            CustomButton(width / 2, 60, 220, 46, "BACK TO MENU", self.back_to_menu),
            CustomButton(width - 120, 60, 180, 42, "PLAY AGAIN", self.play_again),
        ]

    def new_run(self) -> None:
        self.window.show_view(self.window.run_setup_view)

    def back_to_menu(self) -> None:
        self.window.show_view(self.window.main_menu_view)

    def play_again(self) -> None:
        self.window.gameplay_view.setup_game()
        self.window.show_view(self.window.gameplay_view)

    def on_draw(self) -> None:
        self.clear()
        draw_background(self.window.width, self.window.height)
        draw_header(
            "RUN SUMMARY",
            "A simple end screen for the current prototype route.",
            x=60,
            y=self.window.height - 50,
        )

        draw_panel(self.window.width / 2, self.window.height / 2 + 10, 840, 500)
        self._draw_result_card()
        self._draw_metrics()
        self._draw_notes()

        for button in self.buttons:
            button.draw()

    def _draw_result_card(self) -> None:
        x = self.window.width / 2 - 250
        y = self.window.height / 2 + 50
        draw_panel(x, y, 320, 320, fill=PANEL_DARK, outline=GOLD, border_width=3)
        arcade.draw_text(self.result_label, x, y + 110, GOLD, 28, anchor_x="center", bold=True)
        arcade.draw_text("BALATRO-STYLE", x, y + 74, TEXT_MUTED, 12, anchor_x="center", bold=True)
        arcade.draw_text("Prototype", x, y + 48, TEXT, 18, anchor_x="center", bold=True)
        draw_chip(x, y - 2, 220, 50, "Best hand", self.best_hand, accent=ACCENT)
        draw_chip(x, y - 58, 220, 50, "Deck", self.deck_name, accent=GREEN)
        draw_chip(x, y - 114, 220, 50, "Stake", self.stake_name, accent=RED)

    def _draw_metrics(self) -> None:
        x = self.window.width / 2 + 210
        y = self.window.height / 2 + 110
        draw_panel(x, y, 320, 220, fill=PANEL_DARK, outline=ACCENT, border_width=2)
        arcade.draw_text("RUN METRICS", x, y + 72, TEXT_MUTED, 12, anchor_x="center", bold=True)
        arcade.draw_text(f"Score: {self.score}", x - 110, y + 24, TEXT, 16, anchor_x="left", bold=True)
        arcade.draw_text(f"Hands played: {self.hands_played}", x - 110, y - 12, TEXT, 14, anchor_x="left", bold=True)
        arcade.draw_text(f"Gold on exit: ${self.gold}", x - 110, y - 48, GOLD, 14, anchor_x="left", bold=True)
        draw_meter(x, y - 84, 220, 18, min(1.0, self.score / 5000 if self.score else 0.0), fill=GOLD, background=PANEL, outline=ACCENT)

    def _draw_notes(self) -> None:
        x = self.window.width / 2 + 210
        y = self.window.height / 2 - 110
        draw_panel(x, y, 320, 130, fill=(42, 22, 19), outline=ACCENT, border_width=2)
        arcade.draw_text(
            "The summary screen is ready to absorb real run data later.",
            x,
            y + 24,
            TEXT_MUTED,
            font_size=11,
            anchor_x="center",
            width=260,
            align="center",
        )
        arcade.draw_text(
            "It currently acts as a clean navigation endpoint.",
            x,
            y - 12,
            TEXT_DIM,
            font_size=10,
            anchor_x="center",
            width=240,
            align="center",
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
