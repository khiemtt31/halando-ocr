# Balatro Replication: Screen List

This document lists all the interactive views (screens) of the application, detailing their user interface layouts, key elements, actions, and how they drive gameplay progress.

---

## 1. Title & Profile Selection Screen
The entry point of the game, setting the visual tone with wavy psychedelic background shaders.
*   **Key Elements**:
    *   Logo (with physics-based wobbling/floating effect).
    *   Profile Selector: Load existing save profiles or create a new one.
    *   Main Menu Buttons: **Play Run**, **Collection (Unlocks)**, **Options**, **Quit**.
*   **Progress Impact**: Sets the profile context (which unlocks, statistics, and run logs are queried from the SQLite database).

---

## 2. Run Configuration Screen (Deck & Stake Selection)
Allows players to customize their run settings.
*   **Key Elements**:
    *   **Deck List**: Horizontal carousel of unlocked starting decks (e.g., Red Deck: +1 discard; Blue Deck: +1 hand; Yellow Deck: start with +$10).
    *   **Stakes (Difficulty)**: Vertical ladder of difficulty stakes (e.g., White Stake, Red Stake, Gold Stake) unlocking sequentially.
    *   **Start Run Button**: Triggers the deck generation and run state initialization.
*   **Progress Impact**: Generates the player's starting deck structure and sets run multipliers.

---

## 3. Blind Selection Screen (Run Map)
The central transition hub between rounds.
*   **Key Elements**:
    *   **Ante Progression Indicator**: Shows current Ante (e.g., Ante 1/8).
    *   **Blind Trio Display**: 
        1.  *Small Blind*: Target score, reward gold, Tag reward (if skipped).
        2.  *Big Blind*: Higher target score, reward gold, Tag reward (if skipped).
        3.  *Boss Blind*: Highest target score, unique boss challenge rules, reward gold.
    *   **Interactives**:
        *   **Select Blind Button**: Starts the Gameplay Round.
        *   **Skip Blind Button**: Immediately collects the displayed Tag and skips to the Shop.
        *   **View Deck**: Overlay displaying remaining cards in order/grouped by rank.
        *   **Run Statistics**: Money, current hands/discards limits, active vouchers.

---

## 4. Gameplay Round Screen (The Play Table)
The core action interface where card manipulation and scoring occur.

```
+-------------------------------------------------------------------------+
| [Joker 1]  [Joker 2]  [Joker 3]  [Joker 4]  [Joker 5]   [Cons 1] [Cons 2]|
+-------------------------------------------------------------------------+
|  [ Score Panel ]           [ Round Stats ]                              |
|  Chips: 12,450             Hands Left: 3                                |
|  Mult : x14.5              Discards  : 2                                |
|  Target: 25,000            Gold      : $12                              |
+-------------------------------------------------------------------------+
|                                                                         |
|         [Card 1]  [Card 2]  [Card 3]  [Card 4]  [Card 5]  [Card 6]        |
|                                                                         |
+-------------------------------------------------------------------------+
|   [PLAY HAND]                [DISCARD]                 [VIEW DECK]      |
+-------------------------------------------------------------------------+
```

*   **Key Interface Zones**:
    *   **Top Bar (Inventory)**: Active Jokers (can be dragged to rearrange left-to-right calculation order) and Consumables (Tarot/Planet cards).
    *   **Left Pane (Scoring)**: Displays calculated Chips (blue box) and Mult (red box), showing the current hand type (e.g., "Full House - Lv. 2").
    *   **Center Board (The Hand)**: Floating cards dealt to the player. Hovering magnifies them. Clicking/dragging selects cards (up to 5).
    *   **Control Panel**: **Play Hand** and **Discard** buttons.
*   **Progress Impact**: Resolves the direct gameplay loop. Winning grants entry to the Shop; losing triggers the Game Over screen.

---

## 5. Scoring Animation Overlay
An overlay state that locks user inputs during scoring evaluation to provide extreme visual satisfaction.
*   **Animation Sequence**:
    1.  Selected cards fly to the center scoring zone.
    2.  The evaluator identifies the poker hand and triggers the base chip and mult counters (creating sound cues).
    3.  Cards are scored one-by-one from left to right. The card sprite bounces, sparks particles, and adds points to the counters.
    4.  Jokers shake and trigger their effects in left-to-right order, applying multipliers or addition values.
    5.  The final score counts up with fire/glow effects.
    6.  Cards are swept to the discard pile, and new cards are dealt.

---

## 6. Shop Screen
Where players buy items to scale their build.
*   **Key Elements**:
    *   **Card Slots**: 2 random Jokers, Tarots, or Planet cards.
    *   **Voucher Slot**: 1 persistent passive upgrade.
    *   **Booster Packs**: 2 booster packs (e.g., Standard Pack, Arcane Pack). Clicking starts the **Booster Draft Overlay**.
    *   **Reroll Button**: Refreshes card slots, cost increases with each press.
    *   **Sell Area**: Drag inventory items here to recoup gold.
*   **Booster Draft Overlay**: Shows a close-up of cards drawn from a pack. The player chooses 1 (or 2) cards, and the rest disappear.
*   **Progress Impact**: Changes deck structure and passive upgrades.

---

## 7. Game Over / Run Summary Screen
Triggers upon running out of hands before meeting the blind target score, or after beating the final Boss Blind.
*   **Key Elements**:
    *   **Run Results Summary**: Ante reached, rounds played, highest score hand, total gold earned.
    *   **Progression Updates**: Displays cards unlocked or stickers earned on Jokers.
    *   **Action Buttons**: **New Run**, **Main Menu**.
*   **Progress Impact**: Saves run metrics to the SQLite profile database and persists statistics.
