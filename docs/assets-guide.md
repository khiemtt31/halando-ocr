# Balatro Replication: Asset Guide & Resources

This document outlines the assets that have been retrieved and generated for the local workspace, detailing their file locations, formats, dimensions, and instructions on how to load and use them in python.

---

## 1. Directory Structure

The assets have been structured inside the `src/assets/` directory as follows:

```
halando/
└── src/
    └── assets/
        ├── cards/                  # Standard playing card sprites (Kenney CC0 Pack)
        │   ├── PNG/
        │   │   ├── Cards (small)/  # 52 x 70 pixels cards
        │   │   ├── Cards (medium)/ # 81 x 117 pixels cards
        │   │   └── Cards (large)/  # 120 x 176 pixels cards
        │   └── Tilesheet/          # Packed card sprite sheets
        │
        ├── ui/
        │   └── logo.png            # Custom "Halando" pixel art game logo (512x512)
        │
        └── textures/
            ├── background.png      # Wavy psychedelic vaporwave background texture (512x512)
            └── joker_sprites.png   # 6 custom retro Joker card designs (512x512)
```

---

## 2. Included Assets & Specifications

### Standard Playing Cards
*   **Source**: [Kenney's Playing Cards Pack](https://opengameart.org/content/playing-cards-pack)
*   **License**: CC0 (Public Domain - free for commercial and non-commercial use, no attribution required).
*   **Files**:
    *   Individual cards are located in [PNG/Cards (large)](file:///Users/trongkhiem/Developer/workspace/halando/src/assets/cards/PNG/Cards%20(large)), [PNG/Cards (medium)](file:///Users/trongkhiem/Developer/workspace/halando/src/assets/cards/PNG/Cards%20(medium)), and [PNG/Cards (small)](file:///Users/trongkhiem/Developer/workspace/halando/src/assets/cards/PNG/Cards%20(small)).
    *   They are named using the pattern `card[Suit][Value].png` (e.g., `cardSpadesA.png` for Ace of Spades, `cardHearts10.png` for 10 of Hearts).
    *   **Suits**: `Clubs`, `Diamonds`, `Hearts`, `Spades`.
    *   **Values**: `2`-`10`, `J`, `Q`, `K`, `A`.
    *   **Special Cards**: `cardBack_blue1.png` - `cardBack_red5.png` (various card backs), and jokers (`cardJoker.png`).

### Custom Game UI & Textures
*   **Logo (`src/assets/ui/logo.png`)**:
    *   Custom-generated pixel art title card containing the word "HALANDO" with a jester hat and playing cards. Great for the Main Menu screen.
*   **Background (`src/assets/textures/background.png`)**:
    *   A high-quality neon purple/pink/blue wavy cyberpunk gradient background, designed to simulate Balatro's wavy backdrop out of the box.
*   **Jokers (`src/assets/textures/joker_sprites.png`)**:
    *   A grid of 6 unique, highly detailed custom Joker designs (Classic Jester, Cyborg, Flame Elemental, Pharaoh, Astronaut, and Shadow Wraith) ready to be cropped/split for individual Joker cards.

---

## 3. How to Load Assets in Python

Below are examples of how to load these assets using the recommended engines.

### Option A: Loading Assets in Arcade

Arcade provides a clean class-based sprite loader:

```python
import arcade
import os

# Base paths
ASSETS_DIR = os.path.join("src", "assets")
CARDS_DIR = os.path.join(ASSETS_DIR, "cards", "PNG", "Cards (large)")
TEX_DIR = os.path.join(ASSETS_DIR, "textures")
UI_DIR = os.path.join(ASSETS_DIR, "ui")

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Halando - Balatro Clone")
        
        # Load Background
        self.background = arcade.load_texture(os.path.join(TEX_DIR, "background.png"))
        
        # Load Logo
        self.logo = arcade.load_texture(os.path.join(UI_DIR, "logo.png"))
        
        # Load a card (e.g. Ace of Spades)
        self.ace_of_spades = arcade.Sprite(
            os.path.join(CARDS_DIR, "cardSpadesA.png"),
            scale=1.0
        )
        self.ace_of_spades.center_x = 400
        self.ace_of_spades.center_y = 300

    def on_draw(self):
        self.clear()
        
        # Draw background stretched to fit window
        arcade.draw_lrwh_rectangle_textured(
            0, 0, self.width, self.height, self.background
        )
        
        # Draw Logo
        self.logo.draw_scaled(400, 500, scale=0.5)
        
        # Draw card
        self.ace_of_spades.draw()

if __name__ == "__main__":
    window = GameWindow()
    arcade.run()
```

### Option B: Loading Assets in Pygame-CE

Pygame-CE handles image loading and transparency natively using surfaces:

```python
import pygame
import os
import sys

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.SCALED)
pygame.display.set_caption("Halando - Balatro Clone")

# Base paths
ASSETS_DIR = os.path.join("src", "assets")
CARDS_DIR = os.path.join(ASSETS_DIR, "cards", "PNG", "Cards (large)")
TEX_DIR = os.path.join(ASSETS_DIR, "textures")
UI_DIR = os.path.join(ASSETS_DIR, "ui")

# Load textures and optimize transparency format
background = pygame.image.load(os.path.join(TEX_DIR, "background.png")).convert()
# Stretch background to screen resolution
background = pygame.transform.scale(background, (800, 600))

logo = pygame.image.load(os.path.join(UI_DIR, "logo.png")).convert_alpha()
logo = pygame.transform.scale(logo, (256, 256))

ace_spades = pygame.image.load(os.path.join(CARDS_DIR, "cardSpadesA.png")).convert_alpha()

# Game Loop
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
    # Draw Background
    screen.blit(background, (0, 0))
    
    # Draw Logo and Card
    screen.blit(logo, (272, 50))
    screen.blit(ace_spades, (340, 350))
    
    pygame.display.flip()
    clock.tick(60)
```

---

## 4. Extracting Individual Jokers (Splitting Spritesheets)

Since the 6 Custom Jokers are packed into `src/assets/textures/joker_sprites.png`, you can easily crop them out at runtime. The spritesheet contains 2 rows and 3 columns of card shapes.

### Cropping Sprites in Pygame
```python
def load_joker_spritesheet(sheet_path):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    
    # Dimensions of each card (sheet is 512x512 divided into 3x2 grid)
    # Each card is roughly 170 width x 256 height
    card_w = 512 // 3
    card_h = 512 // 2
    
    jokers = []
    for row in range(2):
        for col in range(3):
            rect = pygame.Rect(col * card_w, row * card_h, card_w, card_h)
            joker_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            joker_surf.blit(sheet, (0, 0), rect)
            jokers.append(joker_surf)
            
    return jokers  # Returns list of 6 individual Joker surfaces
```
