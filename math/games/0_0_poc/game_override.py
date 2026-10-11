from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """SkyJump does not assign Garden wild/scatter symbol functions."""

    def reset_book(self):
        super().reset_book()

    def assign_special_sym_function(self):
        # SDK compatibility placeholder — not used by SkyJump resolver.
        self.special_symbol_functions = {}

    def check_repeat(self):
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
                return
