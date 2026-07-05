# Balatro Replication: Overview

Welcome to the project documentation for replicating the award-winning roguelike deck builder **Balatro**. This document serves as the high-level roadmap, detailing the core concept, technology choices, functional user stories, and non-functional requirements.

---

## 1. Core Concept
The game is a 2D roguelike poker deck builder where the player attempts to score enough chips to beat target score thresholds called **Blinds**.
- **The Core Loop**: Play poker hands -> score points -> earn cash -> buy Jokers/Upgrades from the Shop -> beat harder Blinds.
- **Synergistic Depth**: The magic of the game lies in cascading mechanics: Jokers modify score calculations, Tarot cards modify standard cards (changing suits, adding bonuses), and Planet cards level up the base scores of specific poker hands.

---

## 2. Technology Stack & Rationale
To make the developer experience smooth, extensible, and high-performance:
- **Programming Language**: **Python 3.11+**
  - Excellent support for OOP, rapid prototyping, and clean data structures.
- **Graphic/UI Engine**: **Pygame-CE** (Community Edition) or **Arcade**
  - *Recommendation*: **Arcade**. It features modern OpenGL-accelerated sprite rendering, simple OOP design, built-in support for vector drawing, shaders, and cleaner keyboard/mouse event mapping than standard Pygame.
- **Database**: **SQLite** (via Python's standard `sqlite3` module)
  - Perfect for a local game: zero-config, single-file database to persist profile statistics, high scores, and card unlock progression.
- **Packaging/Distribution**: **PyInstaller**
  - Bundle the Python application and assets into a single executable for Mac/Windows.

---

## 3. Functional Requirements (User Stories)

### Run & Round Progression
- **US-1**: *As a player, I want to start a run by choosing a Deck (e.g., Red Deck, Blue Deck) that gives me unique starting conditions.*
- **US-2**: *As a player, I want to progress through a series of "Antes" (1 to 8+), where each Ante consists of three Blinds: Small Blind, Big Blind, and Boss Blind.*
- **US-3**: *As a player, I want the option to "Skip" the Small or Big Blind to receive a unique Tag reward immediately, at the cost of missing the shop phase.*
- **US-4**: *As a player, I want to face Boss Blinds that impose unique negative rules (e.g., "Hearts are debuffed", "Must play exactly 5 cards", "No discards").*

### Gameplay Mechanics
- **US-5**: *As a player, I want to select up to 5 cards from my hand and "Play" them, scoring chips based on the poker hand type evaluated.*
- **US-6**: *As a player, I want to select up to 5 cards from my hand and "Discard" them to draw replacement cards from my remaining deck.*
- **US-7**: *As a player, I want to see the score calculated step-by-step: summing card values, applying card modifications, and then triggering Joker multipliers from left to right.*
- **US-8**: *As a player, I want to carry a limited inventory of Jokers (default: 5) and Consumables (default: 2 Tarots/Planets/Spectrals).*

### Shop & Meta-Progression
- **US-9**: *As a player, I want to visit a Shop after winning a Blind, where I can spend gold on random Jokers, single Tarot/Planet cards, permanent Vouchers, or Booster Packs.*
- **US-10**: *As a player, I want to view my "Collection" from the main menu, showing which Jokers I have discovered and unlocked.*
- **US-11**: *As a player, I want the game to save my run progress automatically, allowing me to resume an active run if I close the game.*

---

## 4. Non-Functional Requirements

### Visual & Interactive Feel ("Juice")
- **NFR-1 (Frame Rate)**: Render smoothly at a locked 60 FPS. Frame pacing should be solid to avoid stuttering during UI movements.
- **NFR-2 (Physics & Animation)**: Implement card physics (hover expansions, floating animations, card shuffling arcs, and drag-and-drop elasticity).
- **NFR-3 (Visual Juice)**: Screenshake on large point scores, particle effects when cards are scored or destroyed, and dynamic zoom-ins on triggering Jokers.

### Extensibility & Code Quality
- **NFR-4 (Modular Joker System)**: The system must allow developers to implement a new Joker with less than 20 lines of declarative Python code. Adding new card designs or suits should not require modification of the core rendering loop.
- **NFR-5 (Robust Test Coverage)**: The scoring engine and hand evaluator must be 100% decoupled from the UI, allowing pure unit testing of all poker hands, scoring scenarios, and card modifiers.

### Performance & Persistence
- **NFR-6 (Data Integrity)**: The SQLite database must use transactional writes to prevent profile corruption if the application exits unexpectedly.
- **NFR-7 (Resource Footprint)**: Memory usage must be capped under 200MB, ensuring the game runs smoothly even on older low-spec laptops.
