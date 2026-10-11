from game_override import GameStateOverride
from skyjump_resolve import (
    BOOK_AMOUNT_MULTIPLIER,
    resolve_round,
    round_to_book_events,
    rgs_payout_multiplier,
    tables_for_mode,
)
import random


class GameState(GameStateOverride):
    """SkyJump book writer. Farmer 5x3 draw_board path is not used."""

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim, simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            if not getattr(self, "criteria", None):
                self.criteria = "basegame"
            tables = tables_for_mode(getattr(self, "betmode", "BASE"))
            hill_id = tables["hillId"]
            multiplier_table_id = tables["multiplierTableId"]
            current_mode = self.get_current_betmode()
            if current_mode is not None:
                self.config.wincap = float(current_mode.get_wincap())

            round_result = resolve_round(
                random,
                hill_id=hill_id,
                multiplier_table_id=multiplier_table_id,
                bet=1.0,
                max_win=tables["maxWin"],
                cost_multiplier=tables["costMultiplier"],
            )
            # One event stream, one integer amount. Do not re-emit SDK setWin/finalWin
            # which round(finalWinX, 2) then *100 and disagree with round(finalWinX * 100).
            for event in round_to_book_events(round_result):
                self.book.add_event(event)

            amount = rgs_payout_multiplier(round_result.finalWinX)
            self.win_manager.update_spinwin(round_result.finalWinX)
            self.win_manager.update_gametype_wins(self.gametype)
            self.wincap_triggered = bool(round_result.capped)
            self.final_win = amount / BOOK_AMOUNT_MULTIPLIER
            self.book.payout_multiplier = amount / BOOK_AMOUNT_MULTIPLIER
            self.book.basegame_wins = self.final_win
            self.book.freegame_wins = 0.0
            self.check_repeat()
        self.imprint_wins()

    def run_freespin(self):
        return
