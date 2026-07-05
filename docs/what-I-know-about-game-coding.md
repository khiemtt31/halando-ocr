1. Game always run in a loop
while running:
    handle_input()
    update_game()
    render()
2. Metrics are important so must understand: 
- Delta time
- FPS 
- Update and Render
- Event Handling
- Input System

3. Scene / State Management
Balatro has many game states:
Main menu
Shop
Blind selection
Playing hand
Joker animations
Game over
IMPORT: You need a State Machine.

```python
class GameState:
    def update(self):
        pass

class PlayingState(GameState):
    pass

class ShopState(GameState):
    pass
```

3. Sprite Rendering
You must know:
Drawing images
Scaling
Rotation
Layer ordering (z-index)
UI rendering
Sprite sheets
Libraries:
Pygame (best beginner choice)
Arcade (modern alternative)
Balatro is heavily UI/sprite-based.
4. Animation Systems
Balatro feels good because of:
Smooth card movement
Juice effects
Scaling
Tweening
Shake effects
Ease-in/ease-out
You should understand:
Interpolation
Tweening
Animation queues


A huge amount are actually:

* UI variants
* animation frames
* VFX
* joker illustrations
  —not the playing cards themselves.


Example:
card.x += (target_x - card.x) * 0.1
This alone creates smooth motion.

5. Object-Oriented Design
You’ll need many entities:
Card
Deck
Hand
Joker
Blind
Shop
TarotCard
PlanetCard
>> You should know:
Classes
Inheritance
Composition
Encapsulation
Especially composition.

6. Event System / Observer Pattern
Balatro’s jokers react to events:
“When hand scored”
“When discard”
“When card destroyed”
So you need:
Event dispatching
Subscribers/listeners
Observer pattern
Example:
emit("hand_scored")
Then jokers listen:
on_hand_scored()
This is one of the MOST important systems in Balatro.

7. Data-Driven Design
Do NOT hardcode 150 jokers manually.
Use JSON/YAML/dictionaries:
{
  "name": "Half Joker",
  "effect": "+20 mult if hand has <=3 cards"
}
Balatro is heavily data-driven.
This allows:
Easier balancing
Easier content creation
Modding
8. UI Systems
Balatro is basically:
a giant animated UI system
You need:
Buttons
Hover effects
Tooltips
Drag/drop
Card selection
Layout systems
This is harder than beginners expect.

9. Card Game Logic
You need poker-hand evaluation:
Pair
Straight
Flush
Full house
etc.
You should know:
Sorting
Counting frequencies
Algorithms
Combinations
Example:
Counter(ranks)

9. Card Game Logic
You need poker-hand evaluation:
Pair
Straight
Flush
Full house
etc.
You should know:
Sorting
Counting frequencies
Algorithms
Combinations
Example:
Counter(ranks)

12. Audio Feedback
Small sounds matter a LOT:
Card flip
Chip count
Multiplier tick
Button hover
You should know:
Sound playback
Channels
Timing

Inshort: -- just do these first

Card rendering
Drag/drop cards
Poker evaluator
Shop system
Animation system
Event dispatcher
Then combine everything