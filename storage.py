# storage.py
import json
import os
import sys
from pathlib import Path

APP_NAME = "POLYBIUS II"

def get_app_dir() -> Path:
    """Returns standard platform-specific directory for saving configs/scores.

    Windows: %APPDATA%\PolybiusII (or Documents\PolybiusII)
    Linux:   ~/.config/PolybiusII
    macOS:   ~/Library/Application Support/PolybiusII
    """
    home = Path.home()
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")
        if app_data:
            base_dir = Path(app_data)
        else:
            base_dir = home / "Documents"
    elif sys.platform == "darwin":
        base_dir = home / "Library" / "Application Support"
    else:
        base_dir = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))

    target_dir = base_dir / APP_NAME
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

# Use the new directory for our save files
APP_DIR = get_app_dir()
SETTINGS_FILE = APP_DIR / "settings.json"
LEADERBOARD_FILE = APP_DIR / "leaderboard.json"

DEFAULT_SETTINGS = {
    "invert_x": False,
    "invert_y": False,
    "master_volume": 0.8,
    "screen_shake_enabled": True,
    "discord_rpc_enabled": True,
    "colorblind_mode": False,
    "overdrive_unlocked": False
}

DEFAULT_LEADERBOARD = [
    ["DSK", 50000],
    ["AJS", 40000],
    ["ASM", 30000],
    ["KLF", 20000],
    ["IPO", 10000]
]

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for key, val in DEFAULT_SETTINGS.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_leaderboard():
    if LEADERBOARD_FILE.exists():
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_LEADERBOARD.copy()
    return DEFAULT_LEADERBOARD.copy()

def save_leaderboard(board):
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(board, f, indent=4)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")