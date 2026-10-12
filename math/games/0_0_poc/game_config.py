"""SkyJump GameConfig. Garden 5x3 lines/paytable are not published here."""

from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode
from skyjump_resolve import CONFIG


def published_sim_counts(debug_batch: bool, production_sims: int, debug_sims: int) -> dict[str, int]:
    """Stake play keys (rgsKey), not canonical snake_case JSON ids."""
    counts: dict[str, int] = {}
    for index, mode in enumerate(
        mode for mode in CONFIG["buyModes"].values() if mode.get("enabled", True)
    ):
        key = mode["rgsKey"]
        if debug_batch:
            counts[key] = debug_sims if index == 0 else 0
        else:
            counts[key] = production_sims
    return counts


class GameConfig(Config):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = CONFIG["meta"]["gameID"]  # TODO: see meta.gameIdRenameTodo
        # PLACEHOLDER: replace poc_studio / provider_number 0 when Stake ACP issues production IDs.
        self.provider_number = 0
        self.provider_name = "poc_studio"
        self.working_name = CONFIG["meta"]["workingTitle"]
        self.game_name = "skyjump"
        self.rtp = float(CONFIG["meta"]["targetRtpLabel"])
        self.construct_paths()

        # Sequential 6-slot SkyJump strip. Not a Garden 5x3 lines game.
        self.num_reels = 6
        self.num_rows = [1] * self.num_reels
        # SDK compatibility placeholder — not used by SkyJump resolver.
        self.win_type = "custom"

        # SDK compatibility placeholders — not used by SkyJump resolver.
        self.paytable = {}
        self.paylines = {}
        self.include_padding = False
        self.special_symbols = {"wild": [], "scatter": [], "multiplier": []}
        self.freespin_triggers = {self.basegame_type: {}, self.freegame_type: {}}
        self.anticipation_triggers = {self.basegame_type: 0, self.freegame_type: 0}
        self.reels = {}
        self.padding_reels = {}
        self.padding_symbol_values = {}

        enabled_modes = [mode for mode in CONFIG["buyModes"].values() if mode.get("enabled", True)]
        self.wincap = max(float(mode["maxWin"]) for mode in enabled_modes)
        self.published_rgs_keys = [mode["rgsKey"] for mode in enabled_modes]

        # Distribution conditions still require these keys for math-sdk quota loops.
        # SDK compatibility placeholder — not used by SkyJump resolver.
        skyjump_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}},
            "mult_values": {self.basegame_type: {1: 1}},
            "force_wincap": False,
            "force_freegame": False,
        }

        self.bet_modes = [
            BetMode(
                # Stake play() / HUD send rgsKey (BASE). Canonical JSON id is base, …
                name=mode["rgsKey"],
                cost=float(mode["costMultiplier"]),
                rtp=self.rtp,
                max_win=float(mode["maxWin"]),
                auto_close_disabled=False,
                is_feature=mode.get("type") == "default",
                is_buybonus=mode.get("type") == "buy",
                distributions=[
                    Distribution(criteria="basegame", quota=1.0, conditions=skyjump_condition),
                ],
            )
            for mode in enabled_modes
        ]
