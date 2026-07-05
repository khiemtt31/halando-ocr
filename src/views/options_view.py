"""
views/options_view.py
---------------------
OptionsView – placeholder toggles and presentation settings.
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
    draw_header,
    draw_meter,
    draw_panel,
)


class OptionsView(arcade.View):
    """Sketch of the settings screen with toggles and simple meters."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.buttons: list[CustomButton] = []
        self.music_on: bool = True
        self.sfx_on: bool = True
        self.shake_on: bool = True
        self.motion_on: bool = True
        self.master_volume: float = 0.75
        self.toast_msg: str = "These controls are placeholders for later persistence."

    def on_show_view(self) -> None:
        self._build_buttons()

    def _build_buttons(self) -> None:
        width = self.window.width
        self.buttons = [
            CustomButton(120, 60, 180, 42, "BACK", self.back_to_menu),
            CustomButton(width / 2, 60, 180, 42, "RESET", self.reset_options),
            CustomButton(width - 120, 60, 180, 42, "TOGGLE SFX", self.toggle_sfx),
            CustomButton(width - 120, 118, 180, 42, "TOGGLE SHAKE", self.toggle_shake),
        ]

    def back_to_menu(self) -> None:
        self.window.show_view(self.window.main_menu_view)

    def reset_options(self) -> None:
        self.music_on = True
        self.sfx_on = True
        self.shake_on = True
        self.motion_on = True
        self.master_volume = 0.75
        self.toast_msg = "Settings reset to the default sketch state."

    def toggle_sfx(self) -> None:
        self.sfx_on = not self.sfx_on
        self.toast_msg = f"SFX is now {'on' if self.sfx_on else 'off'}."

    def toggle_shake(self) -> None:
        self.shake_on = not self.shake_on
        self.toast_msg = f"Screenshake is now {'on' if self.shake_on else 'off'}."

    def on_draw(self) -> None:
        self.clear()
        draw_background(self.window.width, self.window.height)
        draw_header(
            "OPTIONS",
            "Audio, motion, and accessibility placeholders for the final system.",
            x=60,
            y=self.window.height - 50,
        )

        draw_panel(self.window.width / 2, self.window.height / 2 + 10, self.window.width - 120, 520)
        self._draw_settings_cards()
        self._draw_accessibility_panel()

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

    def _draw_settings_cards(self) -> None:
        left_x = 290
        center_y = self.window.height / 2 + 120

        draw_panel(left_x, center_y, 410, 140, fill=PANEL_DARK, outline=ACCENT, border_width=2)
        arcade.draw_text("SOUND", left_x - 170, center_y + 46, TEXT_MUTED, 12, anchor_x="left", bold=True)
        arcade.draw_text("MASTER VOLUME", left_x - 170, center_y + 16, TEXT, 16, anchor_x="left", bold=True)
        draw_meter(left_x - 30, center_y - 32, 300, 20, self.master_volume, fill=GOLD, background=PANEL, outline=ACCENT)
        arcade.draw_text("MUSIC", left_x - 170, center_y - 58, TEXT_MUTED, 11, anchor_x="left", bold=True)
        arcade.draw_text("ON" if self.music_on else "OFF", left_x - 80, center_y - 58, GREEN if self.music_on else RED, 14, anchor_x="left", bold=True)

        draw_panel(left_x, center_y - 170, 410, 140, fill=PANEL_DARK, outline=ACCENT, border_width=2)
        arcade.draw_text("PLAY FEEL", left_x - 170, center_y - 124, TEXT_MUTED, 12, anchor_x="left", bold=True)
        arcade.draw_text("MOTION", left_x - 170, center_y - 154, TEXT, 16, anchor_x="left", bold=True)
        arcade.draw_text("ON" if self.motion_on else "OFF", left_x - 80, center_y - 154, GREEN if self.motion_on else RED, 14, anchor_x="left", bold=True)
        arcade.draw_text("SHAKE", left_x - 170, center_y - 188, TEXT_MUTED, 11, anchor_x="left", bold=True)
        arcade.draw_text("ON" if self.shake_on else "OFF", left_x - 80, center_y - 188, GREEN if self.shake_on else RED, 14, anchor_x="left", bold=True)

    def _draw_accessibility_panel(self) -> None:
        x = self.window.width - 250
        y = self.window.height / 2 + 20
        draw_panel(x, y, 320, 360, fill=PANEL_DARK, outline=GOLD, border_width=2)
        arcade.draw_text("ACCESSIBILITY", x, y + 136, TEXT_MUTED, 12, anchor_x="center", bold=True)
        arcade.draw_text("Later", x, y + 82, GOLD, 36, anchor_x="center", bold=True)
        arcade.draw_text("This area is reserved for future persistence, key remapping, and color mode settings.", x, y + 30, TEXT_DIM, 11, anchor_x="center", width=260, align="center")
        draw_panel(x, y - 70, 220, 34, fill=PANEL, outline=ACCENT, border_width=2)
        arcade.draw_text("Color mode", x - 82, y - 70, TEXT_MUTED, 10, anchor_x="left", anchor_y="center", bold=True)
        arcade.draw_text("Classic", x + 48, y - 70, TEXT, 12, anchor_x="center", anchor_y="center", bold=True)
        draw_panel(x, y - 120, 220, 34, fill=PANEL, outline=ACCENT, border_width=2)
        arcade.draw_text("Auto save", x - 82, y - 120, TEXT_MUTED, 10, anchor_x="left", anchor_y="center", bold=True)
        arcade.draw_text("Enabled", x + 50, y - 120, TEXT, 12, anchor_x="center", anchor_y="center", bold=True)

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
