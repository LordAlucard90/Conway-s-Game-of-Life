from .Controllers import GrowthMediumCTRL
from .Views import GameLayout
from kivy.app import App


class Game(App):
    """ Game build and manage the GameOfLife """
    def build(self):
        return GameLayout(GrowthMediumCTRL())
