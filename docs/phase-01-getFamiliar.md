# Phase 1: Getting Familiar with Arcade and running the Menu

This document guides you through the game structure, explains the code lifecycle of our graphic engine (**Arcade**), and shows you how to interact with and modify the game code.

---

## 1. Project Workflow & Running the Game

To launch the interactive main menu, follow these simple steps in your terminal:

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```
2. **Launch the game**:
   ```bash
   python src/main.py
   ```

Because we run Python directly, **any changes you make to the source code will immediately apply the next time you run the command**. There is no compilation step!

---

## 2. Understanding Arcade's View Lifecycle

Arcade operates around a **Window** containing one or more **Views**. In [src/main.py](file:///Users/trongkhiem/Developer/workspace/halando/src/main.py), we set up:
1. `HalandoWindow(arcade.Window)`: The main viewport controller, which handles window dimensions, title, and switches between views.
2. `MainMenuView(arcade.View)`: Renders the custom animated menu.
3. `GamePlayView(arcade.View)`: A simple interactive view to verify code updates and run basic test features.

### View Hook Methods

Each View overrides standard callback hooks that Arcade calls under the hood:

```python
class MainMenuView(arcade.View):
    def on_show_view(self):
        """Called once when we switch to this view. Use this to load assets specific to this view."""
        pass

    def on_draw(self):
        """Called roughly 60 times per second. All render/drawing calls go here."""
        self.clear() # Clears screen
        # Renders sprites, backgrounds, text...

    def on_update(self, delta_time: float):
        """Called roughly 60 times per second to update positions, counters, physics, and animations."""
        # delta_time is the seconds elapsed since the last frame (~0.016s)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Called when a mouse button is clicked."""

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Called when the mouse moves. Great for hover effects."""
```

---

## 3. Premium Aesthetics: Our Menu Style

Our main menu mimics the iconic feel of Balatro but incorporates a custom style:

### A. Wavy Psychedelic Background
We draw the vaporwave gradient texture `background.png`. To make it look dynamic:
- We track a `time_elapsed` float in `on_update`.
- In `on_draw`, we slightly scale, rotate, and pan the background using coordinates derived from `sin(time_elapsed)`. This creates a smooth, breathing, wavy canvas.

### B. Physics-Based Logo Wobble & Hover Cards
- The logo `logo.png` floats up and down using a sine wave:
  $$Y = \text{Default\_Y} + \sin(\text{time\_elapsed} \times 2.0) \times 12$$
- Card sprites float independently using staggered phases.
- Hovering over cards or buttons dynamically increases their scale ($1.0 \to 1.15$), giving crisp tactile feedback.

---

## 4. Making Code Changes

### Example: Modifying the Title or Button Text
To see how easy it is to change the code:
1. Open [src/main.py](file:///Users/trongkhiem/Developer/workspace/halando/src/main.py)
2. Locate the button setup code in `MainMenuView.setup()`
3. Modify the labels or hover colors.
4. Rerun `python src/main.py` to see your changes active!
