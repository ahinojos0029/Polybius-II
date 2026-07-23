# config.py
APP_NAME = "POLYBIUS"
WIDTH, HEIGHT = 640, 480

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
AMBER = (255, 170, 0)
GREEN = (0, 255, 120)
RED_TEXT = (220, 50, 20)
BLUE_TEXT = (25, 75, 220)
CB_PLAYER = (255, 230, 0)  # High-contrast bright yellow

LEVEL_PALETTES = [
    [CYAN, MAGENTA, AMBER, GREEN, WHITE],
    [(255, 50, 50), (255, 255, 0), (255, 0, 255), WHITE],
    [(0, 255, 120), (0, 100, 255), (200, 0, 255), CYAN],
    [(255, 255, 255), (255, 100, 0), (0, 255, 255), (150, 0, 255)],
]

SUBLIMINALS = [
    "THEY DONT WANT YOU",
    "YOU ARE NOT ALONE",
    "IT NEVER EXISTED",
    "IT'S ALL IN YOUR HEAD",
    "THEY ARE WATCHING",
    "YOU ARE NOT SAFE",
    "THEY ARE PLANNING",
    "FORGET THEM",
    "ACCEPT THE TRUTH",
    "THEY ARE EVERYWHERE",
    "YOU CANNOT ESCAPE",
    "YOU CANNOT WIN",
    "THEY ARE IN CONTROL",
    "YOUR EYES ARE LYING",
]

# In config.py
DEFAULT_SETTINGS = {
    "invert_x": False,
    "invert_y": False,
    "master_volume": 0.8,
    "screen_shake_enabled": True,
    "discord_rpc_enabled": True,
    "colorblind_mode": False,  # <--- New Setting
}

# Add a high-visibility palette for Colorblind Mode
CB_PLAYER = (255, 230, 0)  # High-visibility Bright Yellow
CB_AMBER = (255, 170, 0)  # Deep High-Contrast Orange
CB_CYAN = (0, 210, 255)  # Electric Blue
