"""
views/main_menu_view.py
-----------------------
MainMenuView – the animated main-menu screen.
Fully compatible with Arcade 3.3.3.

Key 3.x fixes vs the old single-file code
------------------------------------------
* Background drawn via ``arcade.draw_texture_rect`` (``draw_scaled`` removed).
* ``card.collides_with_point(x, y)``  –  no tuple wrapper.
* ``arcade.Sprite(path, scale=...)``  – keyword argument.
"""

import math
import os

import arcade

from constants import (
    LIGHT_GRAY,
    NEON_PINK,
    NEON_CYAN,
    TEX_DIR,
    UI_DIR,
    CARDS_DIR,
    MENU_CARD_SCALE,
)
from ui.button import CustomButton
from ui.balatro_theme import draw_background, draw_panel, MockCard, ACCENT, PANEL_DARK, PANEL
from sprites.floating_card import FloatingCard


# Decorative cards shown on the menu background
_MENU_CARD_FILES = [
    "card_spades_A.png",
    "card_hearts_K.png",
    "card_diamonds_Q.png",
    "card_clubs_J.png",
    "card_joker_red.png",
]


class MainMenuView(arcade.View):
    """Animated main-menu with floating cards, wobbling logo and neon buttons."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.bg_texture: arcade.Texture | None = None
        self.logo_sprite: arcade.Sprite | None = None
        self.logo_base_y: float = 0.0
        self.time_elapsed: float = 0.0
        self.buttons: list[CustomButton] = []
        self.cards: arcade.SpriteList = arcade.SpriteList()
        self.hovered_card: FloatingCard | None = None

    # ------------------------------------------------------------------
    def on_show_view(self) -> None:
        bg_path = os.path.join(TEX_DIR, "background.png")
        if os.path.exists(bg_path):
            self.bg_texture = arcade.load_texture(bg_path)

        # Logo -------------------------------------------------------
        logo_path = os.path.join(UI_DIR, "logo.png")
        if os.path.exists(logo_path):
            self.logo_sprite = arcade.Sprite(logo_path, scale=0.6)
            self.logo_sprite.center_x = self.window.width / 2
            self.logo_sprite.center_y = self.window.height - 180
            self.logo_base_y = self.logo_sprite.center_y

        # Buttons ----------------------------------------------------
        self._build_buttons()

        # Decorative floating cards ----------------------------------
        self.cards.clear()
        for i, card_file in enumerate(_MENU_CARD_FILES):
            card_path = os.path.join(CARDS_DIR, card_file)
            if not os.path.exists(card_path):
                continue
            card = FloatingCard(card_path, scale=MENU_CARD_SCALE)
            n = len(_MENU_CARD_FILES)
            card.center_x = 150 + i * (self.window.width - 300) // (n - 1)
            card.center_y = 450 + (i % 2) * 50
            card.time_accumulator = float(i) * 2.0
            self.cards.append(card)

    # ------------------------------------------------------------------
    def _build_buttons(self) -> None:
        w, h = 220, 50
        cx = self.window.width / 2
        self.buttons = [
            CustomButton(cx, 340, w, h, "NEW RUN",    self.start_game),
            CustomButton(cx, 275, w, h, "COLLECTION", self.show_collection),
            CustomButton(cx, 210, w, h, "OPTIONS",    self.show_options),
            CustomButton(cx, 145, w, h, "QUIT",       self.quit_game),
        ]

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    def start_game(self) -> None:
        self.window.show_view(self.window.run_setup_view)

    def show_collection(self) -> None:
        self.window.show_view(self.window.collection_view)

    def show_options(self) -> None:
        self.window.show_view(self.window.options_view)

    def quit_game(self) -> None:
        self.window.close()

    # ------------------------------------------------------------------
    def on_draw(self) -> None:
        self.clear()

        # 1. Animated background -------------------------------------
        draw_background(self.window.width, self.window.height)
        if self.bg_texture:
            arcade.draw_texture_rect(
                self.bg_texture,
                arcade.LRBT(0, self.window.width, 0, self.window.height),
            )

        # 2. Floating decorative cards --------------------------------
        self.cards.draw()

        # 2b. Menu showcase panel ------------------------------------
        draw_panel(self.window.width - 250, self.window.height / 2 + 40, 300, 300, fill=PANEL_DARK, outline=ACCENT, border_width=2)
        MockCard("New Run", "Deck + Stake", accent=ACCENT, fill=PANEL, ribbon="START").draw(self.window.width - 250, self.window.height / 2 + 65, width=180, height=220, selected=True)

        # 3. Logo with vertical float --------------------------------
        # Arcade 3.x removed Sprite.draw() — use arcade.draw_sprite() instead
        if self.logo_sprite:
            arcade.draw_sprite(self.logo_sprite)
        else:
            # Fallback title text when logo image is missing
            arcade.draw_text(
                "HALANDO",
                self.window.width / 2,
                self.window.height - 160,
                (255, 0, 128),
                font_size=64,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )

        # 4. Interactive buttons -------------------------------------
        for button in self.buttons:
            button.draw()

        # 5. Footer --------------------------------------------------
        arcade.draw_text(
            "Balatro-style sketch shell  •  UI first, logic later",
            self.window.width / 2,
            35,
            LIGHT_GRAY,
            12,
            anchor_x="center",
            italic=True,
        )

    # ------------------------------------------------------------------
    def on_update(self, delta_time: float) -> None:
        self.time_elapsed += delta_time

        # Logo wobble
        if self.logo_sprite:
            self.logo_sprite.center_y = (
                self.logo_base_y + math.sin(self.time_elapsed * 1.8) * 10
            )
            self.logo_sprite.angle = math.cos(self.time_elapsed * 1.2) * 3.0

        # Floating cards
        for card in self.cards:
            card.update_animation(delta_time)

    # ------------------------------------------------------------------
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        for button in self.buttons:
            button.check_hover(x, y)

        # Card hover  — 3.3.3: collides_with_point takes a (x, y) tuple
        self.hovered_card = None
        for card in self.cards:
            if card.collides_with_point((x, y)):
                card.is_hovered   = True
                card.target_scale = MENU_CARD_SCALE * 1.2
                self.hovered_card = card
            else:
                card.is_hovered   = False
                card.target_scale = MENU_CARD_SCALE

    # ------------------------------------------------------------------
    def on_mouse_press(
        self, x: float, y: float, button: int, modifiers: int
    ) -> None:
        for btn in self.buttons:
            if btn.is_hovered:
                btn.on_click()
                break

    # ------------------------------------------------------------------
    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)
        if self.logo_sprite:
            self.logo_sprite.center_x = width / 2
            self.logo_sprite.center_y = height - 180
            self.logo_base_y = self.logo_sprite.center_y

        self._build_buttons()

        n = len(self.cards)
        if n > 1:
            for i, card in enumerate(self.cards):
                card.center_x = 150 + i * (width - 300) // (n - 1)
