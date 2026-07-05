import arcade
import os
import math

# Window dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Halando - Arcade Environment Verification"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "src", "assets")
CARDS_DIR = os.path.join(ASSETS_DIR, "cards", "PNG", "Cards (large)")
TEX_DIR = os.path.join(ASSETS_DIR, "textures")
UI_DIR = os.path.join(ASSETS_DIR, "ui")

class InteractiveCard(arcade.Sprite):
    def __init__(self, filename, scale=1.0):
        super().__init__(filename, scale)
        self.original_scale = scale
        self.target_scale = scale
        self.is_dragging = False
        self.float_offset = 0.0
        self.float_speed = 3.0
        self.float_amplitude = 5.0
        self.time_accumulator = 0.0

    def update(self):
        # Smooth scaling for hover effects – scale is a plain tuple in 3.x
        if self.scale[0] != self.target_scale:
            new_s = self.scale[0] + (self.target_scale - self.scale[0]) * 0.2
            self.scale = (new_s, new_s)

    def update_animation(self, delta_time):
        self.time_accumulator += delta_time
        # Gentle floating when not dragging
        if not self.is_dragging:
            self.center_y += math.sin(self.time_accumulator * self.float_speed) * (self.float_amplitude * delta_time)


class HalandoVerifyApp(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        
        # Textures
        self.background_texture = None
        self.logo_texture = None
        
        # Sprites
        self.card_list = arcade.SpriteList()
        self.logo_sprite = None
        
        # State variables
        self.time_elapsed = 0.0
        self.held_card = None
        
    def setup(self):
        # Load textures
        self.background_texture = arcade.load_texture(os.path.join(TEX_DIR, "background.png"))
        self.logo_texture = arcade.load_texture(os.path.join(UI_DIR, "logo.png"))
        
        # Set up floating logo sprite
        self.logo_sprite = arcade.Sprite(os.path.join(UI_DIR, "logo.png"), scale=0.6)
        self.logo_sprite.center_x = SCREEN_WIDTH // 2
        self.logo_sprite.center_y = SCREEN_HEIGHT - 180
        
        # Load standard playing cards
        card_files = ["card_spades_A.png", "card_hearts_Q.png", "card_joker_red.png"]
        start_x = SCREEN_WIDTH // 2 - 200
        
        for i, card_file in enumerate(card_files):
            card_path = os.path.join(CARDS_DIR, card_file)
            if os.path.exists(card_path):
                card = InteractiveCard(card_path, scale=1.0)
                card.center_x = start_x + (i * 200)
                card.center_y = 250
                # Give each card a slightly staggered floating phase
                card.time_accumulator = i * 1.5
                self.card_list.append(card)
            else:
                print(f"Warning: Card file not found: {card_path}")

        # Crop and load a custom Joker from the spritesheet (let's get the cyborg joker)
        # joker_sprites.png is 512x512, contains 6 cards (3x2 grid)
        # Cyborg joker is column 1 (index 1), row 0 (index 0)
        joker_sheet_path = os.path.join(TEX_DIR, "joker_sprites.png")
        if os.path.exists(joker_sheet_path):
            card_w = 512 // 3
            card_h = 512 // 2
            # arcade.load_texture(path, x, y, width, height)
            # Row 0, Col 1
            cyborg_joker_tex = arcade.load_texture(joker_sheet_path, x=card_w, y=card_h, width=card_w, height=card_h)
            
            # Create a sprite with the cropped texture
            cyborg_joker = InteractiveCard(joker_sheet_path, scale=0.9)
            cyborg_joker.texture = cyborg_joker_tex
            cyborg_joker.center_x = SCREEN_WIDTH // 2 + 300
            cyborg_joker.center_y = 250
            cyborg_joker.time_accumulator = 4.5
            self.card_list.append(cyborg_joker)
            
    def on_draw(self):
        self.clear()
        
        # 1. Draw psychedelic background (stretched and slightly panned over time)
        bg_scale_x = self.width / self.background_texture.width
        bg_scale_y = self.height / self.background_texture.height
        max_scale = max(bg_scale_x, bg_scale_y) * 1.1
        
        # Calculate slight panning motion
        pan_x = math.sin(self.time_elapsed * 0.5) * 20
        pan_y = math.cos(self.time_elapsed * 0.5) * 20
        
        # draw_scaled removed in Arcade 3.x – use draw_texture_rect instead
        arcade.draw_texture_rect(
            self.background_texture,
            arcade.LRBT(0, self.width, 0, self.height),
        )
        
        # 2. Draw title logo with wobble effects
        # Sprite.draw() removed in Arcade 3.x – use arcade.draw_sprite()
        arcade.draw_sprite(self.logo_sprite)
        
        # 3. Draw cards
        self.card_list.draw()
        
        # 4. Draw instructions UI overlay
        arcade.draw_text(
            "Halando Dev Environment Active! • Drag & drop cards to test input physics.",
            self.width // 2, 35,
            arcade.color.WHITE, 14,
            anchor_x="center"
        )
        
    def on_update(self, delta_time: float):
        self.time_elapsed += delta_time
        
        # Wobble/float logo sprite
        self.logo_sprite.center_y = (SCREEN_HEIGHT - 180) + math.sin(self.time_elapsed * 2.0) * 12
        self.logo_sprite.angle = math.sin(self.time_elapsed * 1.5) * 4.0
        
        # Update cards
        self.card_list.update()
        for card in self.card_list:
            card.update_animation(delta_time)
            
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # Find which card was clicked (from top layer down)
        clicked_sprites = arcade.get_sprites_at_point((x, y), self.card_list)
        
        if clicked_sprites:
            # Grab the top-most sprite
            self.held_card = clicked_sprites[-1]
            self.held_card.is_dragging = True
            # Bring held card to front of rendering list
            self.card_list.remove(self.held_card)
            self.card_list.append(self.held_card)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        if self.held_card:
            self.held_card.is_dragging = False
            self.held_card = None

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        # Update position of card being dragged
        if self.held_card:
            self.held_card.center_x = x
            self.held_card.center_y = y
            
        # Hover effect: scale up cards that the mouse is hovering over
        for card in self.card_list:
            if card != self.held_card:
                if card.collides_with_point((x, y)):
                    card.target_scale = 1.15
                else:
                    card.target_scale = 1.0

    def on_resize(self, width: float, height: float):
        super().on_resize(width, height)
        # Re-center logo on resize
        if self.logo_sprite:
            self.logo_sprite.center_x = width // 2
            self.logo_sprite.center_y = height - 180

def main():
    window = HalandoVerifyApp()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
