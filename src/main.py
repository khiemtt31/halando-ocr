"""
main.py
-------
Entry point for Halando.
All logic lives in the modules under src/:

    constants.py          – colours, paths, tuning values
    window.py             – HalandoWindow (top-level arcade.Window)
    ui/button.py          – CustomButton
    ui/balatro_theme.py   – shared Balatro-style drawing helpers
    sprites/
        floating_card.py  – FloatingCard  (menu decoration)
        gameplay_card.py  – GamePlayCard  (hand card)
    views/
        main_menu_view.py  – MainMenuView
        run_setup_view.py  – RunSetupView
        collection_view.py – CollectionView
        options_view.py    – OptionsView
        shop_view.py       – ShopView
        run_summary_view.py – RunSummaryView
        gameplay_view.py   – GamePlayView

Run with:
    python src/main.py
"""

import arcade
from window import HalandoWindow


def main() -> None:
    window = HalandoWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
