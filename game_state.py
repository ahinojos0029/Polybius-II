# game_state.py
from config import LEVEL_PALETTES
from storage import load_leaderboard, load_settings, save_settings

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
        self.options_category = 0       # 0 = Categories List, 1 = Inside Submenu
        self.active_category_idx = 0     # Index of selected category
        self.options_item_idx = 0        # Index within active category
        self.pause_selection = 0
        self.campaign_level_selected = 1
        self.options_overdrive = False
        self.secret_typed_buffer = ""
        
        # Persistent unlocks
        self.overdrive_unlocked = settings.get("overdrive_unlocked", False)

        # Leaderboard & High Score
        self.leaderboard = load_leaderboard()
        self.player_name_chars = ["A", "A", "A"]
        self.name_cursor_idx = 0
        self.high_score = self.leaderboard[0][1] if self.leaderboard else 0

        # Player stats (HARDENED: Starting lives reduced from 9 to 3)
        self.player_angle = 0.0
        self.player_velocity = 0.0
        self.player_distance = 180
        self.player_dist_velocity = 0.0
        self.lives = 3
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
        self.gun_heat = 0.0
        self.overheated = False

    def unlock_overdrive(self, settings):
        self.overdrive_unlocked = True
        settings["overdrive_unlocked"] = True
        save_settings(settings)

    def reset_game(self, starting_level=1):
        self.lives = 3  # HARDENED: Starts with 3 lives instead of 9
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
        self.gun_heat = 0.0
        self.overheated = False

    def check_high_score(self):
        return self.score > self.leaderboard[-1][1] if self.leaderboard else True