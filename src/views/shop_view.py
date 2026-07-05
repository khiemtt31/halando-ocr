"""
views/shop_view.py
------------------
ShopView – a simple shop shell with card slots and purchase buttons.
"""

from __future__ import annotations

import random

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


class ShopView(arcade.View):
    """Placeholder shop layout with static purchase slots."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.buttons: list[CustomButton] = []
        self.selected_slot: int = 0
        self.toast_msg: str = "Select a slot, then purchase or return to the table."
        self.balance: int = 30
        self.shop_items: list[MockCard] = []
        self._roll_items()

    def on_show_view(self) -> None:
        self._build_buttons()

    def _build_buttons(self) -> None:
        width = self.window.width
        self.buttons = [
            CustomButton(120, 60, 180, 42, "BACK TO TABLE", self.back_to_table),
            CustomButton(width / 2, 60, 180, 42, "BUY", self.buy_selected),
            CustomButton(width - 120, 60, 180, 42, "REROLL", self.reroll_shop),
            CustomButton(width - 120, 118, 180, 42, "MAIN MENU", self.back_to_menu),
        ]

    def _roll_items(self) -> None:
        pool = [
            ("Hologram", "Copy a card", RED),
            ("Midas", "Extra chip gain", GOLD),
            ("Brainstorm", "Duplicate the best card", BLUE),
            ("Sculptor", "Upgrade a suit", GREEN),
            ("Voucher", "Future passive", PURPLE),
        ]
        self.shop_items = [
            MockCard(name, subtitle, accent=accent, ribbon=f"${random.randint(3, 9)}", fill=PANEL)
            for name, subtitle, accent in random.sample(pool, 4)
        ]
        self.selected_slot = 0

    def back_to_table(self) -> None:
        self.window.show_view(self.window.gameplay_view)

    def back_to_menu(self) -> None:
        self.window.show_view(self.window.main_menu_view)

    def reroll_shop(self) -> None:
        self._roll_items()
        self.toast_msg = "Shop refreshed."

    def buy_selected(self) -> None:
        cost = 6 + self.selected_slot * 2
        item = self.shop_items[self.selected_slot]
        if self.balance < cost:
            self.toast_msg = "Not enough gold."
            return
        self.balance -= cost
        self.toast_msg = f"Reserved {item.title} for later wiring."

    def on_draw(self) -> None:
        self.clear()
        draw_background(self.window.width, self.window.height)
        draw_header(
            "SHOP",
            "A Balatro-like store layout for future inventory and purchase logic.",
            x=60,
            y=self.window.height - 50,
        )

        draw_panel(self.window.width / 2, self.window.height / 2 + 12, self.window.width - 120, 530)
        self._draw_top_bar()
        self._draw_shop_row()
        self._draw_side_panel()

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

    def _draw_top_bar(self) -> None:
        x = self.window.width / 2
        y = self.window.height - 150
        draw_panel(x, y, 820, 84, fill=PANEL_DARK, outline=ACCENT, border_width=2)
        draw_chip(x - 240, y, 170, 44, "Gold", f"${self.balance}", accent=GOLD)
        draw_chip(x, y, 220, 44, "Selected slot", str(self.selected_slot + 1), accent=ACCENT)
        draw_chip(x + 240, y, 170, 44, "Reroll", "Manual", accent=BLUE)

    def _draw_shop_row(self) -> None:
        start_x = 260
        y = self.window.height / 2 + 20
        for index, item in enumerate(self.shop_items):
            selected = index == self.selected_slot
            item.draw(start_x + index * 220, y, width=180, height=260, selected=selected)
            draw_panel(start_x + index * 220, y - 155, 128, 34, fill=PANEL_DARK, outline=ACCENT if selected else TEXT_DIM, border_width=2)
            arcade.draw_text(
                f"Cost ${6 + index * 2}",
                start_x + index * 220,
                y - 155,
                TEXT if selected else TEXT_MUTED,
                font_size=12,
                anchor_x="center",
                anchor_y="center",
                bold=selected,
            )

    def _draw_side_panel(self) -> None:
        x = self.window.width - 220
        y = self.window.height / 2 - 40
        draw_panel(x, y, 240, 300, fill=PANEL_DARK, outline=GOLD, border_width=2)
        arcade.draw_text("SHOPPING LIST", x, y + 108, TEXT_MUTED, 12, anchor_x="center", bold=True)
        arcade.draw_text("3", x, y + 60, GOLD, 34, anchor_x="center", bold=True)
        arcade.draw_text("turns to wire later", x, y + 28, TEXT_MUTED, 11, anchor_x="center")
        draw_chip(x, y - 22, 180, 46, "Current slot", f"{self.selected_slot + 1}", accent=ACCENT)
        draw_chip(x, y - 74, 180, 46, "Next price", f"${6 + self.selected_slot * 2}", accent=RED)
        arcade.draw_text(
            "Click the card row or use the future inventory system to buy.",
            x,
            y - 132,
            TEXT_DIM,
            font_size=10,
            anchor_x="center",
            width=170,
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

        start_x = 260
        row_y = self.window.height / 2 + 20
        for index in range(len(self.shop_items)):
            left = start_x + index * 220 - 90
            right = start_x + index * 220 + 90
            bottom = row_y - 130
            top = row_y + 130
            if left <= x <= right and bottom <= y <= top:
                self.selected_slot = index
                self.toast_msg = f"Selected {self.shop_items[index].title}."
                return

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)
        self._build_buttons()
