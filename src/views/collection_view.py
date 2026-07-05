"""
views/collection_view.py
------------------------
CollectionView – a Balatro-style unlock browser.
"""

from __future__ import annotations

import arcade

from constants import GOLD
from ui.button import CustomButton
from ui.balatro_theme import (
    ACCENT,
    BLUE,
    GREEN,
    MockCard,
    PANEL,
    PANEL_DARK,
    PURPLE,
    RED,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    draw_background,
    draw_chip,
    draw_header,
    draw_panel,
)


class CollectionView(arcade.View):
    """Shows a placeholder unlock collection in a card-grid layout."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.buttons: list[CustomButton] = []
        self.category_index: int = 0
        self.categories = ["Jokers", "Tarots", "Planets", "Vouchers"]
        self.toast_msg: str = "Browse discovered items and unlock slots."

        self.collection_sets = [
            [
                MockCard("Mime", "Copy scoring text", accent=RED, ribbon="DISCOVERED"),
                MockCard("Blueprint", "Copy a Joker", accent=BLUE, ribbon="DISCOVERED"),
                MockCard("Egg", "Evolves over time", accent=GOLD, ribbon="DISCOVERED"),
                MockCard("Vagabond", "Spend cash to survive", accent=GREEN, ribbon="DISCOVERED"),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
            ],
            [
                MockCard("Fool", "Copy the last Tarot", accent=PURPLE, ribbon="DISCOVERED"),
                MockCard("Magician", "Enhance the selected card", accent=RED, ribbon="DISCOVERED"),
                MockCard("Wheel", "50/50 gain or loss", accent=BLUE, ribbon="DISCOVERED"),
                MockCard("Death", "Transform a card", accent=GOLD, ribbon="DISCOVERED"),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
            ],
            [
                MockCard("Mercury", "Pair bonus planet", accent=BLUE, ribbon="DISCOVERED"),
                MockCard("Venus", "Three of a kind planet", accent=RED, ribbon="DISCOVERED"),
                MockCard("Earth", "Full house planet", accent=GREEN, ribbon="DISCOVERED"),
                MockCard("Mars", "Four of a kind planet", accent=PURPLE, ribbon="DISCOVERED"),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
            ],
            [
                MockCard("Burnt Voucher", "Permanent perk", accent=GOLD, ribbon="DISCOVERED"),
                MockCard("Overclock", "Faster shop refresh", accent=RED, ribbon="DISCOVERED"),
                MockCard("Inbox", "Extra consumable slot", accent=BLUE, ribbon="DISCOVERED"),
                MockCard("Safety Net", "Keeps one blind safe", accent=GREEN, ribbon="DISCOVERED"),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
                MockCard("Locked Slot", "Unknown effect", accent=PANEL_DARK, fill=PANEL_DARK, locked=True),
            ],
        ]

    def on_show_view(self) -> None:
        self._build_buttons()

    def _build_buttons(self) -> None:
        width = self.window.width
        self.buttons = [
            CustomButton(120, 60, 180, 42, "BACK", self.back_to_menu),
            CustomButton(width - 120, 60, 180, 42, "NEXT CATEGORY", self.next_category),
            CustomButton(width - 120, 118, 180, 42, "PREV CATEGORY", self.prev_category),
        ]

    def back_to_menu(self) -> None:
        self.window.show_view(self.window.main_menu_view)

    def next_category(self) -> None:
        self.category_index = (self.category_index + 1) % len(self.categories)
        self.toast_msg = f"Showing {self.categories[self.category_index]}."

    def prev_category(self) -> None:
        self.category_index = (self.category_index - 1) % len(self.categories)
        self.toast_msg = f"Showing {self.categories[self.category_index]}."

    def on_draw(self) -> None:
        self.clear()
        draw_background(self.window.width, self.window.height)
        draw_header(
            "COLLECTION",
            "A sketch of the unlock browser and discovery screen.",
            x=60,
            y=self.window.height - 50,
        )

        draw_panel(self.window.width / 2, self.window.height / 2 + 20, self.window.width - 120, 530)
        self._draw_category_tabs()
        self._draw_grid()
        self._draw_summary_panel()

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

    def _draw_category_tabs(self) -> None:
        x = 110
        y = self.window.height - 150
        for index, category in enumerate(self.categories):
            selected = index == self.category_index
            draw_panel(x + index * 150, y, 130, 34, fill=PANEL if selected else PANEL_DARK, outline=ACCENT if selected else TEXT_DIM, border_width=2)
            arcade.draw_text(
                category,
                x + index * 150,
                y,
                TEXT if selected else TEXT_MUTED,
                font_size=12,
                anchor_x="center",
                anchor_y="center",
                bold=selected,
            )

    def _draw_grid(self) -> None:
        cards = self.collection_sets[self.category_index]
        start_x = 280
        start_y = self.window.height / 2 + 120
        gap_x = 220
        gap_y = 180

        for index, card in enumerate(cards):
            row = index // 3
            col = index % 3
            card.draw(
                start_x + col * gap_x,
                start_y - row * gap_y,
                width=180,
                height=150,
                selected=not card.locked and index == 0,
            )

    def _draw_summary_panel(self) -> None:
        x = self.window.width - 210
        y = self.window.height / 2 - 10
        draw_panel(x, y, 260, 280, fill=PANEL_DARK, outline=GOLD, border_width=2)
        arcade.draw_text("DISCOVERY", x, y + 96, TEXT_MUTED, 12, anchor_x="center", bold=True)
        arcade.draw_text("12", x, y + 50, GOLD, 36, anchor_x="center", bold=True)
        arcade.draw_text("items sketched", x, y + 20, TEXT_MUTED, 11, anchor_x="center")
        draw_chip(x, y - 28, 190, 46, "Category", self.categories[self.category_index], accent=ACCENT)
        draw_chip(x, y - 80, 190, 46, "Progress", "6 / 12", accent=GREEN)
        arcade.draw_text(
            "Future work can wire these cards to real unlock data.",
            x,
            y - 132,
            TEXT_DIM,
            font_size=10,
            anchor_x="center",
            width=180,
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
