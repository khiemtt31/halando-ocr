"""
window.py
---------
HalandoWindow – the top-level Arcade Window that owns and switches
between the game's views.
"""

import arcade
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from views.main_menu_view import MainMenuView
from views.gameplay_view  import GamePlayView
from views.run_setup_view import RunSetupView
from views.collection_view import CollectionView
from views.options_view import OptionsView
from views.shop_view import ShopView
from views.run_summary_view import RunSummaryView


class HalandoWindow(arcade.Window):
    """Main application window.  Creates and stores each view."""

    def __init__(self) -> None:
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=True)
        self.main_menu_view: MainMenuView | None = None
        self.game_play_view:  GamePlayView  | None = None
        self.run_setup_view: RunSetupView | None = None
        self.collection_view: CollectionView | None = None
        self.options_view: OptionsView | None = None
        self.shop_view: ShopView | None = None
        self.run_summary_view: RunSummaryView | None = None

    def setup(self) -> None:
        """Create views and show the main menu."""
        self.main_menu_view = MainMenuView(self)
        self.game_play_view  = GamePlayView(self)
        self.run_setup_view = RunSetupView(self)
        self.collection_view = CollectionView(self)
        self.options_view = OptionsView(self)
        self.shop_view = ShopView(self)
        self.run_summary_view = RunSummaryView(self)
        self.show_view(self.main_menu_view)
