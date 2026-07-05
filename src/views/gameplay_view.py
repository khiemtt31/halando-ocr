"""
views/gameplay_view.py
----------------------
GamePlayView – the in-round playing screen.
Fully compatible with Arcade 3.3.3.

Key 3.x fixes vs the old single-file code
------------------------------------------
* ``bg_texture.draw_scaled`` removed → ``arcade.draw_texture_rect``.
* ``arcade.schedule`` / ``arcade.unschedule``  →
  ``arcade.clock.schedule_once`` / ``arcade.clock.unschedule``.
* ``card.collides_with_point(x, y)`` – no tuple wrapper.
* ``sprite.scale`` assigned as tuple ``(x, y)`` after reading via ``.x``.

Phase 01 wiring guide
---------------------
This view is the ORCHESTRATOR.  It connects:
  - core/deck.py          → self.deck  (the 52-card pool)
  - core/hand_evaluator.py → evaluate() (detect hand type)
  - core/scoring.py       → calculate_score(), final_score() (get points)
  - sprites/gameplay_card.py → GamePlayCard (visual card)

Search for the string "TODO PHASE-01" to find every spot you need to edit.
"""

import math
import os
import random

import arcade

from constants import (
    LIGHT_GRAY,
    NEON_PINK,
    NEON_CYAN,
    GOLD,
    TEX_DIR,
    CARDS_DIR,
    CARD_SCALE,
    HAND_SIZE,
    MAX_SELECTED,
    TARGET_SCORE,
    START_GOLD,
    START_HANDS,
    START_DISCARDS,
)
from ui.button import CustomButton
from sprites.gameplay_card import GamePlayCard
from ui.balatro_theme import draw_background

# ---------------------------------------------------------------------------
# Core game logic — pure Python, no arcade dependency
# ---------------------------------------------------------------------------
from core.deck import Deck                          # real 52-card deck
from core.hand_evaluator import evaluate            # detect hand type
from core.scoring import calculate_score, final_score  # convert to points


# ---------------------------------------------------------------------------
# Card deck helpers
# ---------------------------------------------------------------------------
_RANKS = [
    ("02", 2),
    ("05", 5),
    ("08", 8),
    ("10", 10),
    ("J",  10),
    ("Q",  10),
    ("K",  10),
    ("A",  11),
]
_SUITS = ["clubs", "diamonds", "hearts", "spades"]

_FALLBACK_CARD = "card_spades_A.png"


def _random_card_path() -> tuple[str, str, int]:
    """Return (path, rank_name, suit, value) for a random playable card."""
    rank_name, rank_val = random.choice(_RANKS)
    suit = random.choice(_SUITS)
    path = os.path.join(CARDS_DIR, f"card_{suit}_{rank_name}.png")
    if not os.path.exists(path):
        path = os.path.join(CARDS_DIR, _FALLBACK_CARD)
        rank_name, suit, rank_val = "A", "spades", 11
    return path, suit, rank_name, rank_val


# ---------------------------------------------------------------------------
class GamePlayView(arcade.View):
    """Interactive poker-hand gameplay screen."""

    def __init__(self, window_parent: arcade.Window):
        super().__init__(window_parent)
        self.bg_texture: arcade.Texture | None = None
        self.time_elapsed: float = 0.0

        # Game state
        self.hand_cards:    arcade.SpriteList = arcade.SpriteList()
        self.active_jokers: arcade.SpriteList = arcade.SpriteList()
        self.deck:          Deck | None = None   # real 52-card deck
        self.run_profile:   dict[str, str] = {"deck": "Red Deck", "stake": "White Stake"}

        # Score tracking
        # score_chips / score_mult: values from the CURRENT hand being scored
        # round_score: accumulated total across ALL hands played this round
        self.score_chips:   int   = 0
        self.score_mult:    float = 1.0
        self.round_score:   int   = 0
        self.target_score:  int   = TARGET_SCORE
        self.gold:          int   = START_GOLD
        self.hands_left:    int   = START_HANDS
        self.discards_left: int   = START_DISCARDS

        # Scoring animation state
        self.anim_timer:     float = 0.0
        self.is_scoring:     bool  = False
        self.scoring_stage:  int   = 0
        self.toast_msg:      str   = "Select up to 5 cards to play or discard!"

        # Pending score computed in play_hand_action, applied in animation Stage 1
        self._pending_chips: int   = 0
        self._pending_mult:  float = 1.0
        self._hand_name:     str   = ""

        # Round end state: None = still playing | "win" | "loss"
        self.game_over: str | None = None

        # UI buttons (set in setup_game)
        self.play_button:    CustomButton | None = None
        self.discard_button: CustomButton | None = None
        self.shop_button:    CustomButton | None = None
        self.menu_button:    CustomButton | None = None
        self.game_over_buttons: list[CustomButton] = []

    # ------------------------------------------------------------------
    def setup_game(self) -> None:
        """Reset everything and start a fresh round."""
        bg_path = os.path.join(TEX_DIR, "background.png")
        if os.path.exists(bg_path):
            self.bg_texture = arcade.load_texture(bg_path)

        # Reset score and game state
        self.score_chips   = 0
        self.score_mult    = 1.0
        self.round_score   = 0         # accumulated score across all hands
        self.target_score  = TARGET_SCORE
        self.gold          = START_GOLD
        self.hands_left    = START_HANDS
        self.discards_left = START_DISCARDS
        self.is_scoring    = False
        self.game_over     = None
        self.toast_msg     = "Select up to 5 cards to play or discard!"
        if self.run_profile:
            self.toast_msg = (
                f"{self.run_profile.get('deck', 'Run')} | {self.run_profile.get('stake', 'White Stake')}"
                " - Select up to 5 cards to play or discard!"
            )

        # Create a fresh 52-card deck (shuffled automatically)
        self.deck = Deck()

        # Load joker sprites (Phase 01: safe no-op if spritesheet missing)
        self._load_jokers()

        # Deal the opening hand from the real deck
        self.deal_hand()

        # Build control buttons
        self._build_buttons()

    # ------------------------------------------------------------------
    def _build_buttons(self) -> None:
        w, h = 150, 42
        cx   = self.window.width / 2
        self.play_button    = CustomButton(cx - 255, 75, w, h, "PLAY HAND", self.play_hand_action)
        self.discard_button = CustomButton(cx - 85, 75, w, h, "DISCARD", self.discard_action)
        self.shop_button    = CustomButton(cx + 85, 75, w, h, "SHOP", self.open_shop)
        self.menu_button    = CustomButton(cx + 255, 75, w, h, "MAIN MENU", self.return_to_menu)

    # ------------------------------------------------------------------
    def _build_game_over_buttons(self) -> None:
        cx = self.window.width / 2
        self.game_over_buttons = [
            CustomButton(cx - 180, self.window.height / 2 - 95, 170, 42, "SUMMARY", self.open_summary),
            CustomButton(cx, self.window.height / 2 - 95, 170, 42, "RESTART", self.restart_run),
            CustomButton(cx + 180, self.window.height / 2 - 95, 170, 42, "MENU", self.return_to_menu),
        ]

    # ------------------------------------------------------------------
    def _load_jokers(self) -> None:
        """
        Load joker sprites from a spritesheet using PIL for cropping.

        Arcade 3.x removed the x/y/width/height kwargs from load_texture.
        We crop sub-regions using PIL directly, then wrap them in arcade.Texture.

        Phase 01: silently skips if the file is missing or PIL fails.
        Phase 02: replace with a proper Joker data model.
        """
        self.active_jokers.clear()
        joker_path = os.path.join(TEX_DIR, "joker_sprites.png")
        if not os.path.exists(joker_path):
            return

        try:
            from PIL import Image as PILImage
            img     = PILImage.open(joker_path).convert("RGBA")
            card_w  = img.width  // 3
            card_h  = img.height // 2

            # Spritesheet layout: 3 columns × 2 rows
            # We read row 1 (second row): Col 2 = Flame, Col 1 = Cyborg
            crops = [
                img.crop((2 * card_w, card_h, 3 * card_w, 2 * card_h)),  # Flame
                img.crop((    card_w, card_h, 2 * card_w, 2 * card_h)),  # Cyborg
            ]

            for i, crop in enumerate(crops):
                tex = arcade.Texture(image=crop)
                j   = arcade.Sprite(scale=0.7)
                j.texture  = tex
                j.center_x = self.window.width / 2 - 80 + i * 160
                j.center_y = self.window.height - 110
                self.active_jokers.append(j)

        except Exception as exc:
            # Non-fatal: joker visuals are optional in Phase 01
            print(f"[Joker] Could not load sprites: {exc}")

    # ------------------------------------------------------------------
    def deal_hand(self) -> None:
        """
        Draw HAND_SIZE cards from the real deck and place them in the hand.

        Cards fly in from off-screen right (deal animation via lerp in
        GamePlayCard.update).  The deck auto-reshuffles if it runs low.
        """
        self.hand_cards.clear()
        start_x = self.window.width / 2 - 320
        spacing  = 90

        # Draw from the real deck; falls back to random if deck is None
        card_datas = self.deck.draw(HAND_SIZE) if self.deck else []

        for i, card_data in enumerate(card_datas):
            card = GamePlayCard(
                card_data.image_path,
                card_data.suit,
                card_data.rank,
                card_data.value,
                scale=CARD_SCALE,
            )
            # Start off-screen right for the deal animation
            card.center_x = self.window.width + 100
            card.center_y = 200
            card.target_x = start_x + i * spacing
            card.target_y = 220
            self.hand_cards.append(card)

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    def return_to_menu(self) -> None:
        self.window.show_view(self.window.main_menu_view)

    def open_shop(self) -> None:
        self.window.show_view(self.window.shop_view)

    def restart_run(self) -> None:
        self.setup_game()

    def open_summary(self) -> None:
        result_label = "BLIND DEFEATED" if self.game_over == "win" else "RUN OVER"
        if self.window.run_summary_view:
            self.window.run_summary_view.configure(
                result_label=result_label,
                score=self.round_score,
                hands_played=max(0, START_HANDS - self.hands_left),
                gold=self.gold,
                best_hand=self._hand_name or "High Card",
                deck_name=self.run_profile.get("deck", "Red Deck"),
                stake_name=self.run_profile.get("stake", "White Stake"),
            )
            self.window.show_view(self.window.run_summary_view)

    def play_hand_action(self) -> None:
        if self.is_scoring:
            return
        if self.game_over:          # block input after round ends
            return
        selected = [c for c in self.hand_cards if c.is_selected]
        if not selected:
            self.toast_msg = "Choose at least 1 card to play!"
            return
        if len(selected) > MAX_SELECTED:
            self.toast_msg = f"You can only play up to {MAX_SELECTED} cards!"
            return
        if self.hands_left <= 0:
            self.toast_msg = "No hands left!"
            return

        self.hands_left  -= 1
        self.is_scoring   = True
        self.scoring_stage = 0
        self.anim_timer   = 0.0

        # Evaluate the hand and pre-compute the score for this hand play.
        # The animation stages in on_update will DISPLAY this result step-by-step,
        # then apply it to round_score at the end of Stage 1.
        result = evaluate(selected)                           # detect hand type
        chips, mult = calculate_score(result, selected)       # add card values
        self._pending_chips = chips
        self._pending_mult  = mult
        self._hand_name     = result.hand_name
        self.score_chips    = chips   # show in panel immediately
        self.score_mult     = mult
        self.toast_msg      = f"{result.hand_name}!"

    def discard_action(self) -> None:
        if self.is_scoring:
            return
        selected = [c for c in self.hand_cards if c.is_selected]
        if not selected:
            self.toast_msg = "Choose at least 1 card to discard!"
            return
        if len(selected) > MAX_SELECTED:
            self.toast_msg = f"You can only discard up to {MAX_SELECTED} cards!"
            return
        if self.discards_left <= 0:
            self.toast_msg = "No discards left!"
            return

        self.discards_left -= 1
        self.toast_msg      = "Discarding and drawing..."

        for card in selected:
            card.target_y     = self.window.height + 150
            card.target_scale = 0.1

        # Arcade 3.x: use arcade.clock.schedule_once instead of arcade.schedule
        arcade.clock.schedule_once(self._replace_discarded, 0.45)

    # ------------------------------------------------------------------
    def _replace_discarded(self, delta_time: float) -> None:
        """
        After playing or discarding, refill the hand back to HAND_SIZE.

        Keeps non-selected cards in place, draws replacements from self.deck.
        Called via arcade.clock.schedule_once() so the sweep animation
        has time to play out first.
        """
        remaining = [c for c in self.hand_cards if not c.is_selected]

        # How many replacement cards do we need?
        n_needed  = HAND_SIZE - len(remaining)
        new_draws = self.deck.draw(n_needed) if (self.deck and n_needed > 0) else []

        new_cards = arcade.SpriteList()
        start_x   = self.window.width / 2 - 320
        spacing   = 90
        draw_iter = iter(new_draws)

        for i in range(HAND_SIZE):
            if i < len(remaining):
                # Keep an existing card, just reposition it
                card = remaining[i]
                card.target_x    = start_x + i * spacing
                card.is_selected = False
                new_cards.append(card)
            else:
                # Slot needs a new card drawn from the deck
                card_data = next(draw_iter, None)
                if card_data is None:
                    break   # deck exhausted (shouldn't happen with 52 cards)
                card = GamePlayCard(
                    card_data.image_path,
                    card_data.suit,
                    card_data.rank,
                    card_data.value,
                    scale=CARD_SCALE,
                )
                card.center_x = -100        # fly in from the left
                card.center_y = 200
                card.target_x = start_x + i * spacing
                card.target_y = 220
                new_cards.append(card)

        self.hand_cards = new_cards
        self.toast_msg  = "Select up to 5 cards to play or discard!"

    # ------------------------------------------------------------------
    def on_draw(self) -> None:
        self.clear()

        # 1. Background ----------------------------------------------
        draw_background(self.window.width, self.window.height)
        if self.bg_texture:
            arcade.draw_texture_rect(
                self.bg_texture,
                arcade.LRBT(0, self.window.width, 0, self.window.height),
            )

        # Dark overlay for readability
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
            ),
            (10, 10, 20, 200),
        )

        # 2. Active jokers ------------------------------------------
        self.active_jokers.draw()
        arcade.draw_text(
            "JOKERS",
            self.window.width / 2,
            self.window.height - 40,
            NEON_PINK,
            14,
            anchor_x="center",
            bold=True,
        )

        # 3. Side panels --------------------------------------------
        self._draw_score_panel()
        self._draw_stats_panel()

        # 4. Toast message ------------------------------------------
        arcade.draw_text(
            self.toast_msg,
            self.window.width / 2,
            140,
            NEON_CYAN,
            14,
            anchor_x="center",
            bold=True,
        )

        # 5. Hand cards ---------------------------------------------
        self.hand_cards.draw()

        # 6. Control buttons ----------------------------------------
        if self.play_button:
            self.play_button.draw()
        if self.discard_button:
            self.discard_button.draw()
        if self.shop_button:
            self.shop_button.draw()
        if self.menu_button:
            self.menu_button.draw()

        # 7. Game-over overlay (drawn last so it's on top of everything)
        if self.game_over:
            if not self.game_over_buttons:
                self._build_game_over_buttons()
            self._draw_game_over_overlay()

    # ------------------------------------------------------------------
    def _draw_score_panel(self) -> None:
        """
        Left panel: round target, last-hand Chips × Mult, cumulative round score.
        """
        panel_y = self.window.height / 2 + 50
        x = 160

        arcade.draw_rect_filled(
            arcade.rect.XYWH(x, panel_y, 220, 220), (20, 15, 35, 230)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(x, panel_y, 220, 220), NEON_PINK, 2
        )

        arcade.draw_text("ROUND TARGET", x, panel_y + 80, LIGHT_GRAY, 11, anchor_x="center", bold=True)
        arcade.draw_text(f"{self.target_score}", x, panel_y + 55, GOLD, 20, anchor_x="center", bold=True)

        arcade.draw_text("LAST HAND", x, panel_y + 15, LIGHT_GRAY, 11, anchor_x="center", bold=True)

        # Chips box (last hand's chip value)
        arcade.draw_rect_filled(arcade.rect.XYWH(x - 50, panel_y - 25, 90, 36), (10, 50, 150))
        arcade.draw_text(f"{self.score_chips}", x - 50, panel_y - 30, arcade.color.WHITE, 14, anchor_x="center", bold=True)

        arcade.draw_text("X", x, panel_y - 30, NEON_PINK, 16, anchor_x="center", bold=True)

        # Mult box (last hand's multiplier)
        arcade.draw_rect_filled(arcade.rect.XYWH(x + 50, panel_y - 25, 90, 36), (150, 10, 50))
        arcade.draw_text(f"{self.score_mult:.0f}", x + 50, panel_y - 30, arcade.color.WHITE, 14, anchor_x="center", bold=True)

        # Cumulative round score (this is what the win condition checks)
        arcade.draw_text(f"Score: {self.round_score}", x, panel_y - 75, NEON_CYAN, 18, anchor_x="center", bold=True)

    # ------------------------------------------------------------------
    def _draw_stats_panel(self) -> None:
        """Right panel: hands / discards / gold."""
        panel_y  = self.window.height / 2 + 50
        stats_x  = self.window.width - 160

        arcade.draw_rect_filled(
            arcade.rect.XYWH(stats_x, panel_y, 220, 220), (20, 15, 35, 230)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(stats_x, panel_y, 220, 220), NEON_CYAN, 2
        )

        arcade.draw_text("ROUND STATS", stats_x, panel_y + 80, LIGHT_GRAY, 12, anchor_x="center", bold=True)
        arcade.draw_text(f"Hands Left: {self.hands_left}",     stats_x - 80, panel_y + 40, arcade.color.WHITE, 14, anchor_y="center", bold=True)
        arcade.draw_text(f"Discards Left: {self.discards_left}", stats_x - 80, panel_y,     arcade.color.WHITE, 14, anchor_y="center", bold=True)
        arcade.draw_text(f"Gold: ${self.gold}",                stats_x - 80, panel_y - 40, GOLD,               14, anchor_y="center", bold=True)

    # ------------------------------------------------------------------
    def on_update(self, delta_time: float) -> None:
        self.time_elapsed += delta_time
        self.hand_cards.update()

        if not self.is_scoring:
            return

        self.anim_timer += delta_time
        selected = [c for c in self.hand_cards if c.is_selected]

        # Stage 0: move selected cards to scoring zone ---------------
        if self.scoring_stage == 0:
            self.toast_msg = "Evaluating Cards..."
            for idx, card in enumerate(selected):
                card.target_x     = self.window.width / 2 - 100 + idx * 55
                card.target_y     = 360
                card.target_scale = 0.65
            if self.anim_timer > 0.8:
                self.scoring_stage = 1
                self.anim_timer    = 0.0

        # Stage 1: pulse each scored card, then commit the hand score ----------
        elif self.scoring_stage == 1:
            self.toast_msg = f"{self._hand_name}!  {self._pending_chips} × {self._pending_mult:.0f}"
            card_index = int(self.anim_timer // 0.25)
            if card_index < len(selected):
                # Visually pulse each card in sequence
                cur = selected[card_index]
                cur.target_scale = 0.75
            else:
                # All cards pulsed — commit score to the running round total
                hand_points      = final_score(self._pending_chips, self._pending_mult)
                self.round_score += hand_points
                # Update display values so the panel reflects the current hand
                self.score_chips  = self._pending_chips
                self.score_mult   = self._pending_mult
                self.scoring_stage = 2
                self.anim_timer   = 0.0

        # Stage 2: joker multiplier triggers ------------------------
        elif self.scoring_stage == 2:
            self.toast_msg = "Jokers Triggering!"
            joker_idx = int(self.anim_timer // 0.4)
            if joker_idx < len(self.active_jokers):
                j = self.active_jokers[joker_idx]
                j.scale = (0.8, 0.8)
                if math.isclose(self.anim_timer % 0.4, 0.0, abs_tol=0.05):
                    self.score_mult *= 1.5
            else:
                self.scoring_stage = 3
                self.anim_timer    = 0.0

        # Stage 3: show result, sweep played cards, deal replacements ----------
        elif self.scoring_stage == 3:
            for j in self.active_jokers:
                j.scale = (0.7, 0.7)
            self.toast_msg = f"Round Score: {self.round_score} / {self.target_score}"

            if self.anim_timer > 1.2:
                # Check win/loss using the CUMULATIVE round_score
                if self.round_score >= self.target_score:
                    self.toast_msg = "BLIND DEFEATED!"
                    self.game_over = "win"
                elif self.hands_left <= 0:
                    self.toast_msg = "GAME OVER!"
                    self.game_over = "loss"
                else:
                    self.toast_msg = "Next Hand!"

                # Fly played cards off-screen
                for card in selected:
                    card.target_y     = self.window.height + 150
                    card.target_scale = 0.1

                self.is_scoring = False
                if not self.game_over:
                    arcade.clock.schedule_once(self._replace_discarded, 0.5)
                else:
                    self._build_game_over_buttons()

    # ------------------------------------------------------------------
    def _check_win_loss(self) -> None:
        """
        Evaluate whether the round is won or lost and set self.game_over.

        Called at the end of Stage 3 (after score is tallied).

        Rules:
          WIN  → total score >= self.target_score
          LOSS → hands_left == 0 AND score < target

        TODO (optional refactor): move the win/loss check from on_update
        Stage 3 into this dedicated method to keep on_update clean.
        """
        total = int(self.score_chips * self.score_mult)
        if total >= self.target_score:
            self.game_over = "win"
        elif self.hands_left <= 0:
            self.game_over = "loss"

    # ------------------------------------------------------------------
    def _draw_game_over_overlay(self) -> None:
        """
        Draw a semi-transparent overlay when the round has ended.

        Called from on_draw() only when self.game_over is not None.

        Shows:
          WIN  → "BLIND DEFEATED!" in gold
          LOSS → "GAME OVER" in red
          Both → "Press R to Restart  •  M for Menu"
        """
        # Semi-transparent dark overlay
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
            ),
            (0, 0, 0, 180),
        )

        if self.game_over == "win":
            headline = "BLIND DEFEATED!"
            color    = GOLD
        else:
            headline = "GAME OVER"
            color    = (220, 50, 50)

        arcade.draw_text(
            headline,
            self.window.width / 2,
            self.window.height / 2 + 40,
            color,
            font_size=52,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        arcade.draw_text(
            "Use the buttons below to continue",
            self.window.width / 2,
            self.window.height / 2 - 40,
            LIGHT_GRAY,
            font_size=18,
            anchor_x="center",
            anchor_y="center",
        )
        for button in self.game_over_buttons:
            button.draw()

    # ------------------------------------------------------------------
    def on_key_press(self, key: int, modifiers: int) -> None:
        """Handle keyboard shortcuts on the game-over screen."""
        if self.game_over:
            if key == arcade.key.R:
                # Restart: rebuild deck, deal fresh hand, reset score
                self.setup_game()
            elif key == arcade.key.M:
                # Return to main menu
                self.window.show_view(self.window.main_menu_view)

    # ------------------------------------------------------------------
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        if self.is_scoring:
            return

        if self.game_over:
            for button in self.game_over_buttons:
                button.check_hover(x, y)
            return

        if self.play_button:
            self.play_button.check_hover(x, y)
        if self.discard_button:
            self.discard_button.check_hover(x, y)
        if self.shop_button:
            self.shop_button.check_hover(x, y)
        if self.menu_button:
            self.menu_button.check_hover(x, y)

        for card in self.hand_cards:
            # 3.3.3: collides_with_point takes a (x, y) tuple
            if card.collides_with_point((x, y)):
                card.target_scale = CARD_SCALE * 1.12
            else:
                card.target_scale = CARD_SCALE

    # ------------------------------------------------------------------
    def on_mouse_press(
        self, x: float, y: float, button: int, modifiers: int
    ) -> None:
        if self.is_scoring:
            return

        if self.game_over:
            for btn in self.game_over_buttons:
                if btn.is_hovered:
                    btn.on_click()
                    return
            return

        for btn in [self.play_button, self.discard_button, self.shop_button, self.menu_button]:
            if btn and btn.is_hovered:
                btn.on_click()
                return

        # Select / deselect cards (topmost first)
        for card in reversed(self.hand_cards):
            if card.collides_with_point((x, y)):
                card.is_selected = not card.is_selected
                break

    # ------------------------------------------------------------------
    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)
        self._build_buttons()
        if self.game_over:
            self._build_game_over_buttons()

        # Reposition jokers
        for i, j in enumerate(self.active_jokers):
            j.center_x = width / 2 - 80 + i * 160
            j.center_y = height - 110

        # Reposition hand
        start_x = width / 2 - 320
        for i, card in enumerate(self.hand_cards):
            card.target_x = start_x + i * 90
