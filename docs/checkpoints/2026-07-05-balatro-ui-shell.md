# Checkpoint: Balatro-style UI Shell

## What I changed
- Switched the project palette from neon vaporwave to a warmer Balatro-like table theme.
- Added shared drawing helpers in `src/ui/balatro_theme.py` for panels, headers, chips, meters, and mock cards.
- Added new navigation screens:
  - `RunSetupView`
  - `CollectionView`
  - `OptionsView`
  - `ShopView`
  - `RunSummaryView`
- Rewired `MainMenuView` so the main buttons open the new screens.
- Extended `GamePlayView` with:
  - a `Shop` button
  - game-over navigation buttons
  - run metadata passed in from setup
  - summary screen handoff
- Updated `HalandoWindow` to create and store all screens up front.

## Why
- The goal was a basic Balatro-style shell, not full game logic.
- Shared helpers keep each screen visually consistent without duplicating a lot of layout code.
- The new screens are intentionally sketch-level, so future gameplay systems can be wired in without replacing the UI structure.
- The existing table logic was kept in place so the project still has a working gameplay path while the shell matures.

## Verification
- Ran a syntax pass with `python3 -m py_compile` over the modified source files.
