# storage.py
import json
import os
import sys
from pathlib import Path

APP_NAME = "POLYBIUS"


def get_app_dir() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")
        base_dir = Path(app_data) if app_data else home / "Documents"
    elif sys.platform == "darwin":
        base_dir = home / "Library" / "Application Support"
    else:
        base_dir = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))

    target_dir = base_dir / APP_NAME
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


APP_DIR = get_app_dir()
SETTINGS_FILE = APP_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "invert_x": False,
    "invert_y": False,
    "master_volume": 0.8,
    "screen_shake_enabled": True,
    "discord_rpc_enabled": True,
    "colorblind_mode": False,
    "overdrive_unlocked": False,
}

DEFAULT_NORMAL_LEADERBOARD = [
    ["DSK", 50000],
    ["AJS", 40000],
    ["ASM", 30000],
    ["KLF", 20000],
    ["IPO", 10000],
]

DEFAULT_OVERDRIVE_LEADERBOARD = [
    ["OVD", 100000],
    ["STR", 80000],
    ["PWR", 60000],
    ["VEX", 40000],
    ["HEX", 20000],
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


def get_leaderboard_file(is_overdrive: bool) -> Path:
    filename = (
        "leaderboard_overdrive.json" if is_overdrive else "leaderboard_normal.json"
    )
    return APP_DIR / filename


def load_leaderboard(is_overdrive: bool = False):
    lb_file = get_leaderboard_file(is_overdrive)
    default_lb = (
        DEFAULT_OVERDRIVE_LEADERBOARD if is_overdrive else DEFAULT_NORMAL_LEADERBOARD
    )
    if lb_file.exists():
        try:
            with open(lb_file, "r") as f:
                return json.load(f)
        except Exception:
            return default_lb.copy()
    return default_lb.copy()


def save_leaderboard(board, is_overdrive: bool = False):
    lb_file = get_leaderboard_file(is_overdrive)
    try:
        with open(lb_file, "w") as f:
            json.dump(board, f, indent=4)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")
