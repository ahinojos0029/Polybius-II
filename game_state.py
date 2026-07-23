# game_state.py
from config import LEVEL_PALETTES
from storage import load_leaderboard, save_leaderboard, load_settings, save_settings

# Game State Constants
STATE_WARNING = -1
STATE_MAIN_MENU = 0
STATE_CAMPAIGN_MENU = 1
STATE_OPTIONS = 2
STATE_LEADERBOARD = 3
STATE_PLAYING = 4
STATE_TRANSITION = 5
STATE_GAMEOVER = 6
STATE_ENTER_NAME = 7
STATE_PAUSED = 9


class GameState:
    def __init__(self):
        settings = load_settings()

        self.running = True
        self.current_state = STATE_WARNING

        # Menu selections & Submenu depth
        self.menu_selection = 0
        self.options_category = 0
        self.active_category_idx = 0
        self.options_item_idx = 0
        self.pause_selection = 0
        self.campaign_level_selected = 1
        self.options_overdrive = False
        self.secret_typed_buffer = ""

        # Persistent unlocks
        self.overdrive_unlocked = settings.get("overdrive_unlocked", False)

        # Leaderboards
        self.leaderboard_normal = load_leaderboard(is_overdrive=False)
        self.leaderboard_overdrive = load_leaderboard(is_overdrive=True)
        self.leaderboard_tab = 0  # 0 = Normal, 1 = Overdrive

        self.refresh_active_leaderboard()

        # Player stats
        self.player_angle = 0.0
        self.player_velocity = 0.0
        self.player_distance = 180
        self.player_dist_velocity = 0.0
        self.lives = 3 if self.options_overdrive else 9
        self.score = 0
        self.level = 1
        self.level_kills = 0
        self.multiplier = 1
        self.multiplier_streak = 0

        # Timers & Cooldowns
        self.invincible_timer = 0
        self.transition_timer = 0
        self.rapid_fire_timer = 0
        self.shotgun_active = False
        self.shoot_cooldown = 0
        self.gameover_timer = 0

        # Entities & Engine Flags
        self.bullets = []
        self.obstacles = []
        self.powerups = []
        self.frame_count = 0
        self.shake_intensity = 0
        self.strobe_flash = False
        self.subliminal_text = ""
        self.subliminal_timer = 0.0
        self.next_subliminal_cooldown = 120.0
        self.gun_heat = 0.0
        self.overheated = False

    @property
    def active_leaderboard(self):
        return (
            self.leaderboard_overdrive
            if self.options_overdrive
            else self.leaderboard_normal
        )

    def refresh_active_leaderboard(self):
        board = self.active_leaderboard
        self.high_score = board[0][1] if board else 0

    def unlock_overdrive(self, settings):
        self.overdrive_unlocked = True
        settings["overdrive_unlocked"] = True
        save_settings(settings)

    def reset_game(self, starting_level=1):
        self.refresh_active_leaderboard()
        self.lives = 3 if self.options_overdrive else 9
        self.score = 0
        self.level = starting_level
        self.level_kills = 0
        self.multiplier = 1
        self.multiplier_streak = 0
        self.player_angle = 0.0
        self.player_velocity = 0.0
        self.player_distance = 180
        self.player_dist_velocity = 0.0
        self.invincible_timer = 0
        self.rapid_fire_timer = 0
        self.shotgun_active = False
        self.frame_count = 0
        self.bullets.clear()
        self.obstacles.clear()
        self.powerups.clear()
        self.shake_intensity = 0
        self.subliminal_text = ""
        self.subliminal_timer = 0.0
        self.next_subliminal_cooldown = 120.0
        self.gun_heat = 0.0
        self.overheated = False

    def check_high_score(self):
        board = self.active_leaderboard
        return self.score > board[-1][1] if board else True

    def submit_high_score(self, name_str):
        board = self.active_leaderboard
        board.append([name_str, self.score])
        board.sort(key=lambda x: x[1], reverse=True)
        board.pop()  # Keep top 5
        save_leaderboard(board, is_overdrive=self.options_overdrive)
        self.refresh_active_leaderboard()
