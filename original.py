import array
import json
import math
import os
import random
import sys
import time
from pathlib import Path
import pygame

# --- PLATFORM-SPECIFIC CONFIG & DATA DIRECTORIES ---
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


# Paths
SAVE_DIR = get_app_dir()
SETTINGS_FILE = SAVE_DIR / "polybius_settings.json"
SCORE_FILE = SAVE_DIR / "polybius_ii_scores.json"

# --- SETTINGS MANAGEMENT ---
settings = {
    "invert_x": False,
    "invert_y": False,
    "master_volume": 0.8,
    "screen_shake_enabled": True,
    "discord_rpc_enabled": True,
}


def load_settings():
  global settings
  if SETTINGS_FILE.exists():
    try:
      with open(SETTINGS_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict):
          settings.update(data)
    except Exception:
      pass


def save_settings():
  try:
    with open(SETTINGS_FILE, "w") as f:
      json.dump(settings, f, indent=4)
  except Exception:
    pass


load_settings()

# --- DISCORD RICH PRESENCE SETUP ---
rpc_connected = False
RPC = None
rpc_start_time = time.time()

if settings.get("discord_rpc_enabled", True):
  try:
    from pypresence import Presence

    CLIENT_ID = "1529672643945431090"
    RPC = Presence(CLIENT_ID)
    RPC.connect()
    rpc_connected = True
  except Exception:
    rpc_connected = False
    RPC = None


def update_discord_status(details_text, state_text=""):
  if rpc_connected and settings.get("discord_rpc_enabled", True):
    try:
      RPC.update(
          details=details_text,
          state=state_text if state_text else None,
          start=rpc_start_time,
          large_image="polybius_logo",
          large_text="POLYBIUS II",
      )
    except Exception:
      pass


# Audio Initialization
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=256)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 640, 480
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("POLYBIUS II - (C) 2026 ARMANDO HINOJOSA")
CLOCK = pygame.time.Clock()

# Safe Font Initialization
try:
  pygame.font.init()
  FONT_SM = pygame.font.SysFont("Courier New", 14)
  FONT_MD = pygame.font.SysFont("Courier New", 18, bold=True)
  FONT_LG = pygame.font.SysFont("Courier New", 26, bold=True)
  FONT_XL = pygame.font.SysFont("Courier New", 36, bold=True)
except Exception:
  FONT_SM = FONT_MD = FONT_LG = FONT_XL = None


def draw_text(surface, text, x, y, color, font=FONT_MD, center=False):
  if font is None:
    return
  surf = font.render(str(text), True, color)
  rect = surf.get_rect()
  if center:
    rect.center = (x, y)
  else:
    rect.topleft = (x, y)
  surface.blit(surf, rect)


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
AMBER = (255, 170, 0)
GREEN = (0, 255, 120)
RED_TEXT = (220, 50, 20)
BLUE_TEXT = (25, 75, 220)

LEVEL_PALETTES = [
    [CYAN, MAGENTA, AMBER, GREEN, WHITE],
    [(255, 50, 50), (255, 255, 0), (255, 0, 255), WHITE],
    [(0, 255, 120), (0, 100, 255), (200, 0, 255), CYAN],
    [(255, 255, 255), (255, 100, 0), (0, 255, 255), (150, 0, 255)],
]


# Sound Generators
def gen_square_wave(freq, duration, volume=0.2):
  vol = volume * settings["master_volume"]
  sample_rate = 22050
  n_samples = int(sample_rate * duration)
  buf = array.array("h")
  period = sample_rate / max(1, freq)
  for i in range(n_samples):
    val = 32000 if (i % period) < (period / 2) else -32000
    buf.append(int(val * vol * (1.0 - (i / float(n_samples)))))
  return pygame.mixer.Sound(buf)


def gen_laser_chirp(start_freq=900, end_freq=200, duration=0.08, volume=0.25):
  vol = volume * settings["master_volume"]
  sample_rate = 22050
  n_samples = int(sample_rate * duration)
  buf = array.array("h")
  phase = 0.0
  for i in range(n_samples):
    t = i / float(n_samples)
    curr_freq = start_freq + (end_freq - start_freq) * t
    phase += curr_freq / sample_rate
    val = 32000 if (phase % 1.0) < 0.5 else -32000
    buf.append(int(val * vol * (1.0 - t)))
  return pygame.mixer.Sound(buf)


def gen_8bit_noise_explosion(duration=0.3, volume=0.35):
  vol = volume * settings["master_volume"]
  sample_rate = 22050
  n_samples = int(sample_rate * duration)
  buf = array.array("h")
  for i in range(n_samples):
    decay = (1.0 - (i / float(n_samples))) ** 2
    buf.append(int(random.choice([28000, -28000]) * vol * decay))
  return pygame.mixer.Sound(buf)


def gen_stage_clear_jingle(volume=0.3):
  vol = volume * settings["master_volume"]
  sample_rate = 22050
  duration = 0.6
  n_samples = int(sample_rate * duration)
  buf = array.array("h")
  notes = [440, 554, 659, 880]
  chunk = n_samples // len(notes)
  for i in range(n_samples):
    freq = notes[min(len(notes) - 1, i // chunk)]
    period = sample_rate / max(1, freq)
    val = 32000 if (i % period) < (period / 2) else -32000
    decay = 1.0 - (i / float(n_samples))
    buf.append(int(val * vol * decay))
  return pygame.mixer.Sound(buf)


def gen_powerup_sound(volume=0.25):
  vol = volume * settings["master_volume"]
  sample_rate = 22050
  duration = 0.25
  n_samples = int(sample_rate * duration)
  buf = array.array("h")
  for i in range(n_samples):
    freq = 300 + (i * 3.0)
    period = sample_rate / max(1, freq)
    val = 32000 if (i % period) < (period / 2) else -32000
    decay = 1.0 - (i / float(n_samples))
    buf.append(int(val * vol * decay))
  return pygame.mixer.Sound(buf)


SND_LASER = gen_laser_chirp(850, 180, 0.07, 0.2)
SND_EXPLODE = gen_8bit_noise_explosion(0.35, 0.35)
SND_HIT = gen_laser_chirp(1200, 600, 0.04, 0.2)
SND_STAGE_CLEAR = gen_stage_clear_jingle(0.3)
SND_POWERUP = gen_powerup_sound(0.25)

CHAN_SFX = pygame.mixer.Channel(0)
CHAN_EXPLODE = pygame.mixer.Channel(1)
CHAN_HUM = pygame.mixer.Channel(2)
CHAN_MUSIC = pygame.mixer.Channel(3)


def load_leaderboard():
  default_board = [
      ["LOC", 15000],
      ["SIN", 12000],
      ["NEO", 8500],
      ["SYN", 5000],
      ["SYS", 2500],
  ]
  if SCORE_FILE.exists():
    try:
      with open(SCORE_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
          return data
    except Exception:
      pass
  return default_board


def save_leaderboard(board):
  try:
    with open(SCORE_FILE, "w") as f:
      json.dump(board, f, indent=4)
  except Exception:
    pass


# Game States
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
current_state = STATE_WARNING

menu_selection = 0
options_selection = 0
pause_selection = 0
campaign_level_selected = 1
options_overdrive = False
secret_typed_buffer = ""
overdrive_unlocked = False

leaderboard = load_leaderboard()

player_name_chars = ["A", "A", "A"]
name_cursor_idx = 0

high_score = leaderboard[0][1]
player_angle = 0.0
player_velocity = 0.0
player_distance = 180
player_dist_velocity = 0.0
lives = 9
score = 0
level = 1
level_kills = 0
multiplier = 1
multiplier_streak = 0
invincible_timer = 0
transition_timer = 0
rapid_fire_timer = 0
shotgun_active = False
shoot_cooldown = 0
gameover_timer = 0

bullets = []
obstacles = []
powerups = []
frame_count = 0
shake_intensity = 0
strobe_flash = False
subliminal_text = ""
SUBLIMINALS = [
    "CONSUME MORE",
    "DO NOT LOOK AWAY",
    "YOUR EYES HURT",
    "ACCEPT THE SIGNAL",
    "YOU CANNOT WIN",
    "MINDLESS",
    "ABSOLUTE CONTROL",
    "REPLACE THE THOUGHT",
]


def reset_game(starting_level=1):
  global lives, score, level, level_kills, multiplier, multiplier_streak, player_angle, player_velocity, player_distance, player_dist_velocity, bullets, obstacles, powerups, frame_count, invincible_timer, rapid_fire_timer, shotgun_active
  lives, score, level, level_kills, multiplier, multiplier_streak = (
      9,
      0,
      starting_level,
      0,
      1,
      0,
  )
  player_angle, player_velocity, player_distance, player_dist_velocity = (
      0.0,
      0.0,
      180,
      0.0,
  )
  invincible_timer, rapid_fire_timer, shotgun_active, frame_count = (
      0,
      0,
      False,
      0,
  )
  bullets.clear()
  obstacles.clear()
  powerups.clear()


def spawn_obstacle():
  angle = random.uniform(0, math.pi * 2)
  speed_mult = 2.0 if options_overdrive else 1.0
  speed = (
      (random.uniform(1.2, 2.2) + (multiplier * 0.1) + (level * 0.15))
      * 0.35
      * speed_mult
  )
  obstacles.append(
      {
          "angle": angle,
          "dist": 5,
          "speed": speed,
          "sides": random.choice([3, 4, 5, 6]),
      }
  )


def spawn_powerup(angle, dist):
  stress_rarity_penalty = (multiplier - 1) * 0.05
  stage_rarity_penalty = (level - 1) * 0.03
  roll = random.random() + stress_rarity_penalty + stage_rarity_penalty
  if roll < 0.03:
    ptype = "F"
  elif roll < 0.12:
    ptype = "S"
  elif roll < 0.35:
    ptype = "H"
  else:
    ptype = "R"
  powerups.append({"angle": angle, "dist": dist, "type": ptype, "speed": 0.35})


def check_high_score(final_score):
  if final_score > leaderboard[-1][1]:
    return True
  return False


# Main Loop
running = True
while running:
  dt = CLOCK.tick(60) / 1000.0 * 60.0
  if dt > 3.0:
    dt = 3.0

  frame_count += 1

  # Update Discord RPC
  if frame_count % 60 == 0:
    if current_state in (
        STATE_WARNING,
        STATE_MAIN_MENU,
        STATE_CAMPAIGN_MENU,
        STATE_OPTIONS,
        STATE_LEADERBOARD,
    ):
      update_discord_status("In Arcade Cabinet", "Main Menu")
    elif current_state in (STATE_PLAYING, STATE_TRANSITION):
      update_discord_status(
          f"Stage {level} | Score: {score:06d}", f"Stress: {multiplier}X"
      )
    elif current_state == STATE_PAUSED:
      update_discord_status(f"Stage {level} | PAUSED", f"Score: {score:06d}")
    elif current_state == STATE_GAMEOVER:
      update_discord_status("Mission Terminated", f"Final Score: {score:06d}")

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        if current_state == STATE_PLAYING:
          current_state = STATE_PAUSED
          pause_selection = 0
        elif current_state == STATE_PAUSED:
          current_state = STATE_PLAYING
        elif current_state in (
            STATE_CAMPAIGN_MENU,
            STATE_OPTIONS,
            STATE_LEADERBOARD,
        ):
          current_state = STATE_MAIN_MENU
          menu_selection = 0
        else:
          running = False

      elif current_state == STATE_PAUSED:
        pause_options_count = 5 if overdrive_unlocked else 4
        if event.key == pygame.K_UP:
          pause_selection = (pause_selection - 1) % pause_options_count
        elif event.key == pygame.K_DOWN:
          pause_selection = (pause_selection + 1) % pause_options_count
        elif event.key in (
            pygame.K_LEFT,
            pygame.K_RIGHT,
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
          if pause_selection == 0:
            current_state = STATE_PLAYING
          elif pause_selection == 1:
            if event.key == pygame.K_LEFT:
              settings["master_volume"] = max(
                  0.0, round(settings["master_volume"] - 0.1, 1)
              )
            else:
              settings["master_volume"] = min(
                  1.0, round(settings["master_volume"] + 0.1, 1)
              )
            save_settings()
          elif pause_selection == 2:
            settings["invert_x"] = not settings["invert_x"]
            save_settings()
          elif pause_selection == 3:
            settings["invert_y"] = not settings["invert_y"]
            save_settings()
          elif pause_selection == 4 and overdrive_unlocked:
            options_overdrive = not options_overdrive
            save_settings()
        elif event.key == pygame.K_q:
          current_state = STATE_MAIN_MENU
          menu_selection = 0

      elif current_state == STATE_WARNING:
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
          current_state = STATE_MAIN_MENU

      elif current_state == STATE_MAIN_MENU:
        if event.key == pygame.K_UP:
          menu_selection = (menu_selection - 1) % 3
        elif event.key == pygame.K_DOWN:
          menu_selection = (menu_selection + 1) % 3
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
          if menu_selection == 0:
            reset_game(1)
            transition_timer = 120
            current_state = STATE_TRANSITION
          elif menu_selection == 1:
            current_state = STATE_CAMPAIGN_MENU
          elif menu_selection == 2:
            secret_typed_buffer = ""
            current_state = STATE_OPTIONS

      elif current_state == STATE_CAMPAIGN_MENU:
        if event.key == pygame.K_LEFT:
          campaign_level_selected = max(1, campaign_level_selected - 1)
        elif event.key == pygame.K_RIGHT:
          campaign_level_selected = min(10, campaign_level_selected + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
          reset_game(campaign_level_selected)
          transition_timer = 120
          current_state = STATE_TRANSITION

      elif current_state == STATE_OPTIONS:
        options_count = 6 if overdrive_unlocked else 5
        if event.key == pygame.K_UP:
          options_selection = (options_selection - 1) % options_count
        elif event.key == pygame.K_DOWN:
          options_selection = (options_selection + 1) % options_count
        elif event.key in (
            pygame.K_LEFT,
            pygame.K_RIGHT,
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
          if options_selection == 0:
            settings["invert_x"] = not settings["invert_x"]
          elif options_selection == 1:
            settings["invert_y"] = not settings["invert_y"]
          elif options_selection == 2:
            if event.key == pygame.K_LEFT:
              settings["master_volume"] = max(
                  0.0, round(settings["master_volume"] - 0.1, 1)
              )
            else:
              settings["master_volume"] = min(
                  1.0, round(settings["master_volume"] + 0.1, 1)
              )
          elif options_selection == 3:
            settings["screen_shake_enabled"] = not settings[
                "screen_shake_enabled"
            ]
          elif options_selection == 4:
            settings["discord_rpc_enabled"] = not settings[
                "discord_rpc_enabled"
            ]
            if not settings["discord_rpc_enabled"] and rpc_connected:
              RPC.clear()
          elif options_selection == 5 and overdrive_unlocked:
            options_overdrive = not options_overdrive
          save_settings()
        elif event.key == pygame.K_l:
          current_state = STATE_LEADERBOARD
        elif not overdrive_unlocked and event.unicode.isalpha():
          secret_typed_buffer += event.unicode.lower()
          if "sinnes" in secret_typed_buffer:
            overdrive_unlocked = True
            secret_typed_buffer = ""

      elif current_state == STATE_LEADERBOARD:
        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
          current_state = STATE_OPTIONS

      elif current_state == STATE_PLAYING:
        if event.key == pygame.K_SPACE and shoot_cooldown <= 0:
          CHAN_SFX.play(SND_LASER)
          if shotgun_active:
            for offset in [-0.15, 0.0, 0.15]:
              bullets.append(
                  {"angle": player_angle + offset, "dist": player_distance}
              )
          else:
            bullets.append({"angle": player_angle, "dist": player_distance})
          shoot_cooldown = 8 if rapid_fire_timer > 0 else 16

      elif current_state == STATE_ENTER_NAME:
        if event.key == pygame.K_UP:
          curr_char_code = ord(player_name_chars[name_cursor_idx])
          curr_char_code = 65 if curr_char_code >= 90 else curr_char_code + 1
          player_name_chars[name_cursor_idx] = chr(curr_char_code)
        elif event.key == pygame.K_DOWN:
          curr_char_code = ord(player_name_chars[name_cursor_idx])
          curr_char_code = 90 if curr_char_code <= 65 else curr_char_code - 1
          player_name_chars[name_cursor_idx] = chr(curr_char_code)
        elif event.key == pygame.K_LEFT:
          name_cursor_idx = max(0, name_cursor_idx - 1)
        elif event.key == pygame.K_RIGHT:
          name_cursor_idx = min(2, name_cursor_idx + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
          new_name = "".join(player_name_chars)
          leaderboard.append([new_name, score])
          leaderboard.sort(key=lambda x: x[1], reverse=True)
          leaderboard.pop()
          save_leaderboard(leaderboard)
          high_score = leaderboard[0][1]
          current_state = STATE_MAIN_MENU
          menu_selection = 0

  if current_state == STATE_PLAYING:
    if shoot_cooldown > 0:
      shoot_cooldown -= max(1, round(dt))
    if rapid_fire_timer > 0:
      rapid_fire_timer -= max(1, round(dt))

  canvas = pygame.Surface((WIDTH, HEIGHT))

  if current_state == STATE_WARNING:
    canvas.fill(BLACK)
    draw_text(
        canvas,
        "WARNING: PHOTOSENSITIVE SEIZURES",
        WIDTH // 2,
        80,
        RED_TEXT,
        FONT_LG,
        center=True,
    )
    draw_text(
        canvas,
        "A small percentage of people may experience seizures",
        WIDTH // 2,
        150,
        WHITE,
        FONT_SM,
        center=True,
    )
    draw_text(
        canvas,
        "when exposed to certain visual images, including flashing",
        WIDTH // 2,
        175,
        WHITE,
        FONT_SM,
        center=True,
    )
    draw_text(
        canvas,
        "lights or patterns that may appear in video games.",
        WIDTH // 2,
        200,
        WHITE,
        FONT_SM,
        center=True,
    )
    draw_text(
        canvas,
        "By proceeding, you accept all health risks.",
        WIDTH // 2,
        260,
        AMBER,
        FONT_SM,
        center=True,
    )
    if (frame_count // 30) % 2 == 0:
      draw_text(
          canvas,
          "PRESS SPACE OR ENTER TO CONTINUE",
          WIDTH // 2,
          360,
          GREEN,
          FONT_MD,
          center=True,
      )

  elif current_state == STATE_MAIN_MENU:
    canvas.fill(BLACK)
    draw_text(canvas, "POLYBIUS II", WIDTH // 2, 80, CYAN, FONT_XL, center=True)
    options = [
        "1. ARCADE QUICK RUN",
        "2. CAMPAIGN SELECTOR",
        "3. OPTIONS & SCORES",
    ]
    for idx, opt in enumerate(options):
      color = GREEN if idx == menu_selection else WHITE
      prefix = "> " if idx == menu_selection else "  "
      draw_text(
          canvas, prefix + opt, WIDTH // 2 - 140, 220 + (idx * 45), color, FONT_MD
      )
    draw_text(
        canvas,
        "USE ARROWS TO NAVIGATE | ENTER TO SELECT | ESC TO QUIT",
        WIDTH // 2,
        430,
        WHITE,
        FONT_SM,
        center=True,
    )

  elif current_state == STATE_CAMPAIGN_MENU:
    canvas.fill(BLACK)
    draw_text(
        canvas,
        "CAMPAIGN STAGE SELECT",
        WIDTH // 2,
        80,
        MAGENTA,
        FONT_LG,
        center=True,
    )
    draw_text(
        canvas,
        f"SELECTED STAGE: {campaign_level_selected}",
        WIDTH // 2,
        180,
        WHITE,
        FONT_XL,
        center=True,
    )
    draw_text(
        canvas,
        "USE LEFT/RIGHT ARROWS TO CHOOSE STAGE",
        WIDTH // 2,
        260,
        CYAN,
        FONT_MD,
        center=True,
    )
    if (frame_count // 30) % 2 == 0:
      draw_text(
          canvas,
          "PRESS ENTER TO LAUNCH STAGE",
          WIDTH // 2,
          360,
          GREEN,
          FONT_MD,
          center=True,
      )
    draw_text(
        canvas, "PRESS ESC TO RETURN", WIDTH // 2, 420, AMBER, FONT_SM, center=True
    )

  elif current_state == STATE_OPTIONS:
    canvas.fill(BLACK)
    draw_text(
        canvas, "SYSTEM CONFIGURATION", WIDTH // 2, 40, AMBER, FONT_LG, center=True
    )

    opts = [
        ("INVERT HORIZONTAL (X)", "ON" if settings["invert_x"] else "OFF"),
        ("INVERT VERTICAL (Y)", "ON" if settings["invert_y"] else "OFF"),
        (
            "STRESS VOLUME",
            f"{int(settings['master_volume'] * 100)}%"
            if settings["master_volume"] > 0
            else "MUTED",
        ),
        (
            "SCREEN SHAKE",
            "ENABLED" if settings["screen_shake_enabled"] else "DISABLED",
        ),
        (
            "DISCORD RICH PRESENCE",
            "ENABLED" if settings["discord_rpc_enabled"] else "DISABLED",
        ),
    ]

    if overdrive_unlocked:
      opts.append(
          ("OVERDRIVE MODE", "ENABLED" if options_overdrive else "DISABLED")
      )

    for idx, (label, val) in enumerate(opts):
      color = GREEN if idx == options_selection else WHITE
      prefix = "> " if idx == options_selection else "  "
      draw_text(
          canvas, f"{prefix}{label}: {val}", 80, 110 + (idx * 38), color, FONT_MD
      )

    if not overdrive_unlocked:
      draw_text(
          canvas,
          "TYPE SECRET PASSWORD FOR MORE SETTINGS",
          WIDTH // 2,
          360,
          CYAN,
          FONT_SM,
          center=True,
      )

    draw_text(
        canvas,
        "ARROWS: NAVIGATE/ADJUST | L: LEADERBOARDS | ESC: SAVE & RETURN",
        WIDTH // 2,
        430,
        WHITE,
        FONT_SM,
        center=True,
    )

  elif current_state == STATE_LEADERBOARD:
    canvas.fill(BLACK)
    draw_text(
        canvas, "GLOBAL LEADERBOARD", WIDTH // 2, 50, AMBER, FONT_LG, center=True
    )
    for idx, entry in enumerate(leaderboard):
      line_str = f"{idx+1}. {entry[0]}  ---  {entry[1]:06d}"
      draw_text(
          canvas,
          line_str,
          WIDTH // 2,
          120 + (idx * 35),
          WHITE,
          FONT_MD,
          center=True,
      )
    if (frame_count // 30) % 2 == 0:
      draw_text(
          canvas,
          "PRESS ENTER TO RETURN",
          WIDTH // 2,
          380,
          GREEN,
          FONT_MD,
          center=True,
      )

  elif current_state == STATE_TRANSITION:
    transition_timer -= dt
    canvas.fill(BLACK)

    cx, cy = WIDTH // 2, HEIGHT // 2
    max_radius = 400
    spin_speed = 0.05
    active_palette = LEVEL_PALETTES[(level - 1) % len(LEVEL_PALETTES)]
    for i in range(20):
      radius = ((frame_count * 6.0 + i * 18) % max_radius) + 2
      color = active_palette[i % len(active_palette)]
      points = []
      for j in range(6):
        angle = (frame_count * spin_speed) + (j * (2 * math.pi / 6))
        points.append(
            (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
        )
      pygame.draw.polygon(canvas, color, points, width=1)

    draw_text(
        canvas,
        f"STAGE {level} READY",
        WIDTH // 2,
        HEIGHT // 2 - 20,
        CYAN,
        FONT_XL,
        center=True,
    )
    if (frame_count // 20) % 2 == 0:
      draw_text(
          canvas,
          "PREPARE YOURSELF",
          WIDTH // 2,
          HEIGHT // 2 + 30,
          AMBER,
          FONT_MD,
          center=True,
      )

    if transition_timer <= 0:
      current_state = STATE_PLAYING

  elif current_state in (STATE_PLAYING, STATE_PAUSED):
    if current_state == STATE_PLAYING:
      beat_interval = max(6, 30 - (multiplier * 3))
      if frame_count % beat_interval == 0 and not CHAN_HUM.get_busy():
        stress_freq = 55 + (multiplier * 12)
        dynamic_hum = gen_square_wave(
            stress_freq, 0.15 + (0.02 * multiplier), 0.08
        )
        CHAN_HUM.play(dynamic_hum)

      keys = pygame.key.get_pressed()

      x_dir = 0
      if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        x_dir += 1
      if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        x_dir -= 1

      y_dir = 0
      if keys[pygame.K_UP] or keys[pygame.K_w]:
        y_dir -= 1
      if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        y_dir += 1

      if settings["invert_x"]:
        x_dir *= -1
      if settings["invert_y"]:
        y_dir *= -1

      is_static = x_dir == 0 and y_dir == 0
      camping_penalty = 1.4 if is_static else 1.0

      if x_dir != 0:
        player_velocity += (x_dir * 0.010) * dt
      else:
        player_velocity *= 0.80**dt

      player_velocity = max(-0.12, min(0.12, player_velocity))
      player_angle += player_velocity * dt

      if y_dir != 0:
        player_dist_velocity += (y_dir * 0.350) * dt
      else:
        player_dist_velocity *= 0.85**dt

      player_dist_velocity = max(-2.50, min(2.50, player_dist_velocity))
      player_distance += player_dist_velocity * dt
      player_distance = max(100, min(280, player_distance))

      if invincible_timer > 0:
        invincible_timer -= dt
      spawn_rate = max(4, (36 - (multiplier * 2) - (level * 2)))
      if frame_count % spawn_rate == 0:
        spawn_obstacle()

    canvas.fill(
        (40, 0, 40) if (strobe_flash and current_state == STATE_PLAYING) else BLACK
    )
    strobe_flash = False

    active_palette = LEVEL_PALETTES[(level - 1) % len(LEVEL_PALETTES)]

    # TUNNEL RINGS
    cx, cy = WIDTH // 2, HEIGHT // 2
    max_radius = 400
    pulse = math.sin(frame_count * (0.08 + level * 0.01)) * (20 + level * 2)
    spin_speed = (0.02 + (multiplier * 0.008) + (level * 0.005)) * (
        -1 if multiplier >= 4 else 1
    )
    sides = 8 if level < 3 else (6 if level < 5 else 10)
    tunnel_speed = 8.5 + (level * 0.6) + (multiplier * 1.5)

    for i in range(45):
      radius = ((frame_count * tunnel_speed + i * 14) % max_radius) + 2 + pulse
      if radius <= 0:
        continue
      color = active_palette[(i + (frame_count // 5)) % len(active_palette)]
      points = []
      for j in range(sides):
        angle = (frame_count * spin_speed) + (j * (2 * math.pi / sides))
        points.append(
            (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
        )
      pygame.draw.polygon(canvas, color, points, width=2)

    if level >= 5:
      for i in range(15):
        radius = (
            (frame_count * (tunnel_speed * 0.7) + i * 25) % max_radius
        ) + 10
        sq_spin = -spin_speed * 1.5
        color = active_palette[(i + 2) % len(active_palette)]
        pts = []
        for j in range(4):
          angle = (frame_count * sq_spin) + (j * (math.pi / 2) + math.pi / 4)
          pts.append(
              (
                  cx + math.cos(angle) * radius * 1.2,
                  cy + math.sin(angle) * radius * 1.2,
              )
          )
        pygame.draw.polygon(canvas, color, pts, width=2)

    if level >= 10:
      for i in range(12):
        radius = max_radius - (
            (frame_count * (tunnel_speed * 0.85) + i * 30) % max_radius
        )
        if radius <= 0:
          continue
        color = active_palette[(i + 4) % len(active_palette)]
        pygame.draw.circle(canvas, color, (cx, cy), int(radius), width=2)

    for b in bullets[:]:
      if current_state == STATE_PLAYING:
        b["dist"] -= 12 * dt
      bx, by = (
          cx + math.cos(b["angle"]) * b["dist"],
          cy + math.sin(b["angle"]) * b["dist"],
      )
      bx_end, by_end = (
          cx + math.cos(b["angle"]) * (b["dist"] + 14),
          cy + math.sin(b["angle"]) * (b["dist"] + 14),
      )
      pygame.draw.line(canvas, WHITE, (bx, by), (bx_end, by_end), 2)
      if b["dist"] <= 0 and current_state == STATE_PLAYING:
        bullets.remove(b)

    for p in powerups[:]:
      if current_state == STATE_PLAYING:
        p["dist"] += p["speed"] * dt
      px_p = cx + math.cos(p["angle"]) * p["dist"]
      py_p = cy + math.sin(p["angle"]) * p["dist"]
      if p["type"] == "F":
        p_color = MAGENTA
      elif p["type"] == "S":
        p_color = CYAN
      elif p["type"] == "H":
        p_color = GREEN
      else:
        p_color = AMBER
      if (frame_count // 10) % 2 == 0:
        draw_text(
            canvas, p["type"], int(px_p - 6), int(py_p - 6), p_color, FONT_MD
        )
      if current_state == STATE_PLAYING:
        angle_diff_p = (
            player_angle - p["angle"] + math.pi
        ) % (2 * math.pi) - math.pi
        if abs(p["dist"] - player_distance) < 20 and abs(angle_diff_p) < 0.35:
          if p["type"] == "F":
            lives = 9
          elif p["type"] == "S":
            shotgun_active = True
          elif p["type"] == "H":
            lives += 1
          elif p["type"] == "R":
            rapid_fire_timer = 300
          CHAN_SFX.play(SND_POWERUP)
          powerups.remove(p)
        elif p["dist"] > 400:
          powerups.remove(p)

    for obs in obstacles[:]:
      if current_state == STATE_PLAYING:
        obs["dist"] += obs["speed"] * dt * camping_penalty
      ox, oy = (
          cx + math.cos(obs["angle"]) * obs["dist"],
          cy + math.sin(obs["angle"]) * obs["dist"],
      )
      obs_color = active_palette[(frame_count // 4) % len(active_palette)]
      poly_pts = []
      size = 8 + (obs["dist"] * 0.045)
      rot = frame_count * 0.12
      for k in range(obs["sides"]):
        a = rot + (k * (2 * math.pi / obs["sides"]))
        poly_pts.append((ox + math.cos(a) * size, oy + math.sin(a) * size))
      pygame.draw.polygon(canvas, obs_color, poly_pts, width=2)

    if current_state == STATE_PLAYING:
      for obs in obstacles[:]:
        for b in bullets[:]:
          angle_diff = (
              b["angle"] - obs["angle"] + math.pi
          ) % (2 * math.pi) - math.pi
          if abs(b["dist"] - obs["dist"]) < 20 and abs(angle_diff) < 0.35:
            score += 100 * multiplier * level
            if score > high_score:
              high_score = score
            multiplier_streak += 1
            level_kills += 1
            if random.random() < 0.25:
              spawn_powerup(obs["angle"], obs["dist"])
            if level_kills >= 15:
              level += 1
              level_kills = 0
              transition_timer = 120
              shotgun_active = False
              CHAN_MUSIC.play(SND_STAGE_CLEAR)
              current_state = STATE_TRANSITION
            if multiplier_streak % 4 == 0 and multiplier < 8:
              multiplier += 1
            if settings["screen_shake_enabled"]:
              shake_intensity = 7
            strobe_flash = True
            CHAN_SFX.play(SND_HIT)
            if obs in obstacles:
              obstacles.remove(obs)
            if b in bullets:
              bullets.remove(b)
            break

        angle_diff_player = (
            player_angle - obs["angle"] + math.pi
        ) % (2 * math.pi) - math.pi
        if (
            abs(obs["dist"] - player_distance) < 20
            and abs(angle_diff_player) < 0.35
            and invincible_timer <= 0
        ):
          lives -= 1
          multiplier, multiplier_streak = 1, 0
          invincible_timer = 60
          if settings["screen_shake_enabled"]:
            shake_intensity = 20
          CHAN_EXPLODE.play(SND_EXPLODE)
          if obs in obstacles:
            obstacles.remove(obs)
          if lives <= 0:
            gameover_timer = 150
            current_state = STATE_GAMEOVER

        if obs["dist"] > 400 and obs in obstacles:
          obstacles.remove(obs)

    px, py = (
        cx + math.cos(player_angle) * player_distance,
        cy + math.sin(player_angle) * player_distance,
    )
    if invincible_timer <= 0 or (int(invincible_timer) // 6) % 2 == 0:
      fa = player_angle + math.pi
      p1 = (px + math.cos(fa) * 12, py + math.sin(fa) * 12)
      p2 = (px + math.cos(fa + 2.4) * 10, py + math.sin(fa + 2.4) * 10)
      p3 = (px + math.cos(fa - 2.4) * 10, py + math.sin(fa - 2.4) * 10)
      pygame.draw.polygon(canvas, CYAN, [p1, p2, p3], width=2)

    subliminal_interval = max(30, 180 - (multiplier * 20))
    subliminal_duration = min(45, 20 + (multiplier * 3))

    if frame_count % subliminal_interval == 0 and current_state == STATE_PLAYING:
      subliminal_text = random.choice(SUBLIMINALS)
    if (frame_count % subliminal_interval) < subliminal_duration:
      flash_x = WIDTH // 2 + (
          random.randint(-10, 10) if multiplier >= 5 else 0
      )
      flash_y = (cy - 20) + (random.randint(-8, 8) if multiplier >= 6 else 0)
      draw_text(
          canvas, subliminal_text, flash_x, flash_y, MAGENTA, FONT_LG, center=True
      )

    draw_text(canvas, f"SCORE: {score:06d}", 20, 15, AMBER, FONT_MD)
    draw_text(canvas, f"HI-SCORE: {high_score:06d}", 20, 35, WHITE, FONT_SM)
    draw_text(canvas, f"STAGE: {level}", 20, 55, CYAN, FONT_MD)

    stress_color = (
        RED_TEXT if (multiplier >= 4 and (frame_count // 12) % 2 == 0) else GREEN
    )
    draw_text(canvas, f"STRESS: {multiplier}X", 20, 75, stress_color, FONT_MD)

    if rapid_fire_timer > 0:
      draw_text(canvas, "RAPID FIRE", 20, 100, AMBER, FONT_SM)
    if shotgun_active:
      draw_text(canvas, "SPREAD SHOT", 20, 118, CYAN, FONT_SM)

    for i in range(min(lives, 12)):
      pygame.draw.circle(canvas, RED_TEXT, (WIDTH - 30 - (i * 15), 25), 5)

    # RENDER PAUSE MENU OVERLAY
    if current_state == STATE_PAUSED:
      overlay = pygame.Surface((WIDTH, HEIGHT))
      overlay.set_alpha(200)
      overlay.fill(BLACK)
      canvas.blit(overlay, (0, 0))

      draw_text(canvas, "GAME PAUSED", WIDTH // 2, 70, AMBER, FONT_XL, center=True)

      opts = [
          ("RESUME GAME", ""),
          ("MASTER VOLUME", f"{int(settings['master_volume'] * 100)}%"),
          ("INVERT X", "ON" if settings["invert_x"] else "OFF"),
          ("INVERT Y", "ON" if settings["invert_y"] else "OFF"),
      ]
      if overdrive_unlocked:
        opts.append(("OVERDRIVE MODE", "ON" if options_overdrive else "OFF"))

      for idx, (label, val) in enumerate(opts):
        color = GREEN if idx == pause_selection else WHITE
        prefix = "> " if idx == pause_selection else "  "
        text_str = f"{prefix}{label}: {val}" if val else f"{prefix}{label}"
        draw_text(
            canvas,
            text_str,
            WIDTH // 2,
            170 + (idx * 40),
            color,
            FONT_MD,
            center=True,
        )

      draw_text(
          canvas,
          "PRESS [Q] TO ABORT RUN & EXIT TO MENU",
          WIDTH // 2,
          400,
          RED_TEXT,
          FONT_SM,
          center=True,
      )
      draw_text(
          canvas,
          "PRESS ESC TO RESUME",
          WIDTH // 2,
          425,
          CYAN,
          FONT_SM,
          center=True,
      )

  elif current_state == STATE_GAMEOVER:
    gameover_timer -= dt
    canvas.fill(BLACK)
    draw_text(
        canvas,
        "MISSION TERMINATED",
        WIDTH // 2,
        120,
        RED_TEXT,
        FONT_XL,
        center=True,
    )
    draw_text(
        canvas,
        f"FINAL SCORE: {score:06d}",
        WIDTH // 2,
        200,
        AMBER,
        FONT_LG,
        center=True,
    )
    draw_text(
        canvas,
        f"HIGH SCORE:  {high_score:06d}",
        WIDTH // 2,
        235,
        WHITE,
        FONT_LG,
        center=True,
    )
    if (frame_count // 30) % 2 == 0:
      draw_text(
          canvas,
          "PRESS ENTER TO CONTINUE",
          WIDTH // 2,
          320,
          BLUE_TEXT,
          FONT_MD,
          center=True,
      )
    if gameover_timer <= 0:
      if check_high_score(score):
        current_state = STATE_ENTER_NAME
      else:
        current_state = STATE_MAIN_MENU
        menu_selection = 0

  elif current_state == STATE_ENTER_NAME:
    canvas.fill(BLACK)
    draw_text(
        canvas, "NEW HIGH SCORE!", WIDTH // 2, 80, AMBER, FONT_XL, center=True
    )
    draw_text(
        canvas,
        "ENTER YOUR INITIALS",
        WIDTH // 2,
        150,
        WHITE,
        FONT_MD,
        center=True,
    )
    start_x = WIDTH // 2 - 60
    for i, char in enumerate(player_name_chars):
      box_color = GREEN if i == name_cursor_idx else WHITE
      pygame.draw.rect(
          canvas, box_color, (start_x + (i * 45), 210, 36, 45), 2
      )
      draw_text(
          canvas, char, start_x + (i * 45) + 12, 218, box_color, FONT_LG
      )
    if (frame_count // 30) % 2 == 0:
      draw_text(
          canvas,
          "USE ARROWS & ENTER TO SUBMIT",
          WIDTH // 2,
          320,
          CYAN,
          FONT_SM,
          center=True,
      )

  SCREEN.fill(BLACK)
  win_w, win_h = SCREEN.get_size()
  scale = min(win_w / WIDTH, win_h / HEIGHT)
  scaled_w, scaled_h = int(WIDTH * scale), int(HEIGHT * scale)
  offset_x, offset_y = (win_w - scaled_w) // 2, (win_h - scaled_h) // 2

  rx = (
      random.randint(-int(shake_intensity), int(shake_intensity))
      if (shake_intensity > 0 and settings["screen_shake_enabled"])
      else 0
  )
  ry = (
      random.randint(-int(shake_intensity), int(shake_intensity))
      if (shake_intensity > 0 and settings["screen_shake_enabled"])
      else 0
  )
  if shake_intensity > 0 and current_state == STATE_PLAYING:
    shake_intensity -= dt

  if multiplier >= 5:
    scaled_down = pygame.transform.smoothscale(
        canvas, (WIDTH // 2, HEIGHT // 2)
    )
    processed_canvas = pygame.transform.smoothscale(
        scaled_down, (WIDTH, HEIGHT)
    )
  else:
    processed_canvas = canvas

  scaled_surf = pygame.transform.smoothscale(
      processed_canvas, (scaled_w, scaled_h)
  )
  SCREEN.blit(scaled_surf, (offset_x + rx, offset_y + ry))
  pygame.display.flip()

pygame.quit()
sys.exit()