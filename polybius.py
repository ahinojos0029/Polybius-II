import pygame
import math
import random
import sys
import array
import json
import os
import socket
import threading

# Audio Initialization
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=256)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 640, 480
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("POLYBIUS II - (C) 2026 ARMANDO HINOJOSA")
CLOCK = pygame.time.Clock()

# Safe Font Initialization
try:
    pygame.font.init()
    FONT_SM = pygame.font.SysFont("Courier New", 14)
    FONT_MD = pygame.font.SysFont("Courier New", 18, bold=True)
    FONT_LG = pygame.font.SysFont("Courier New", 26, bold=True)
    FONT_XL = pygame.font.SysFont("Courier New", 36, bold=True)
except:
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
    [(255, 255, 255), (255, 100, 0), (0, 255, 255), (150, 0, 255)] 
]

# Local Socket Multiplayer Server & Lobby State
SOCKET_PORT = 5588
server_running = False
client_socket = None
lobby_slot = 0
is_ready = False
remote_ready = False
lobby_status_text = "PRESS SPACE TO JOIN LOBBY"

lobby_data_lock = threading.Lock()
connected_clients = []

def run_local_socket_server():
    global server_running, connected_clients
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("0.0.0.0", SOCKET_PORT))
        server.listen(2)
        server_running = True
        while server_running:
            conn, addr = server.accept()
            with lobby_data_lock:
                if len(connected_clients) < 2:
                    slot = len(connected_clients) + 1
                    connected_clients.append({"conn": conn, "slot": slot, "ready": False})
                    threading.Thread(target=handle_lobby_client, args=(conn, slot), daemon=True).start()
                else:
                    conn.close()
    except:
        server_running = False

def handle_lobby_client(conn, slot):
    global connected_clients
    try:
        conn.sendall(json.dumps({"slot": slot}).encode() + b"\n")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg_str = data.decode().strip()
            if msg_str == "READY":
                with lobby_data_lock:
                    for c in connected_clients:
                        if c["conn"] == conn:
                            c["ready"] = True
            
            with lobby_data_lock:
                p1_ready = any(c["slot"] == 1 and c["ready"] for c in connected_clients)
                p2_ready = any(c["slot"] == 2 and c["ready"] for c in connected_clients)
                response = json.dumps({"p1_ready": p1_ready, "p2_ready": p2_ready}) + "\n"
            
            for c in connected_clients:
                try:
                    c["conn"].sendall(response.encode())
                except:
                    pass
    except:
        pass
    finally:
        with lobby_data_lock:
            connected_clients = [c for c in connected_clients if c["conn"] != conn]
        conn.close()

server_thread = threading.Thread(target=run_local_socket_server, daemon=True)
server_thread.start()

# Authentic 8-bit Sound Generators
def gen_square_wave(freq, duration, volume=0.2):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    period = sample_rate / max(1, freq)
    for i in range(n_samples):
        val = 32000 if (i % period) < (period / 2) else -32000
        buf.append(int(val * volume * (1.0 - (i / float(n_samples)))))
    return pygame.mixer.Sound(buf)

def gen_laser_chirp(start_freq=900, end_freq=200, duration=0.08, volume=0.25):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    phase = 0.0
    for i in range(n_samples):
        t = i / float(n_samples)
        curr_freq = start_freq + (end_freq - start_freq) * t
        phase += (curr_freq / sample_rate)
        val = 32000 if (phase % 1.0) < 0.5 else -32000
        buf.append(int(val * volume * (1.0 - t)))
    return pygame.mixer.Sound(buf)

def gen_8bit_noise_explosion(duration=0.3, volume=0.35):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        decay = (1.0 - (i / float(n_samples))) ** 2
        buf.append(int(random.choice([28000, -28000]) * volume * decay))
    return pygame.mixer.Sound(buf)

def gen_stage_clear_jingle(volume=0.3):
    sample_rate = 22050
    duration = 0.6
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    notes = [440, 554, 659, 880]
    chunk = n_samples // len(notes)
    for i in range(n_samples):
        freq = notes[min(len(notes) - 1, i // chunk)]
        period = sample_rate / max(1, freq)
        val = 32000 if (i % period) < (period / 2) else -32000
        decay = 1.0 - (i / float(n_samples))
        buf.append(int(val * volume * decay))
    return pygame.mixer.Sound(buf)

def gen_powerup_sound(volume=0.25):
    sample_rate = 22050
    duration = 0.25
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        freq = 300 + (i * 3.0)
        period = sample_rate / max(1, freq)
        val = 32000 if (i % period) < (period / 2) else -32000
        decay = 1.0 - (i / float(n_samples))
        buf.append(int(val * volume * decay))
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

SCORE_FILE = "polybius_ii_scores.json"

def load_leaderboard():
    default_board = [
        ["LOC", 15000],
        ["SIN", 12000],
        ["NEO", 8500],
        ["SYN", 5000],
        ["SYS", 2500]
    ]
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except:
            pass
    return default_board

def save_leaderboard(board):
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump(board, f)
    except:
        pass

# Game States
STATE_WARNING = -1
STATE_MAIN_MENU = 0
STATE_CAMPAIGN_MENU = 1
STATE_MULTIPLAYER_LOBBY = 2
STATE_OPTIONS = 3
STATE_LEADERBOARD = 4
STATE_PLAYING = 5
STATE_TRANSITION = 6
STATE_GAMEOVER = 7
STATE_ENTER_NAME = 8
current_state = STATE_WARNING

menu_selection = 0
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
SUBLIMINALS = ["CONSUME MORE", "DO NOT LOOK AWAY", "YOUR EYES HURT", "ACCEPT THE SIGNAL", "YOU CANNOT WIN", "MINDLESS", "ABSOLUTE CONTROL", "REPLACE THE THOUGHT"]

def reset_game(starting_level=1):
    global lives, score, level, level_kills, multiplier, multiplier_streak, player_angle, player_velocity, player_distance, player_dist_velocity, bullets, obstacles, powerups, frame_count, invincible_timer, rapid_fire_timer, shotgun_active
    lives, score, level, level_kills, multiplier, multiplier_streak = 9, 0, starting_level, 0, 1, 0
    player_angle, player_velocity, player_distance, player_dist_velocity = 0.0, 0.0, 180, 0.0
    invincible_timer, rapid_fire_timer, shotgun_active, frame_count = 0, 0, False, 0
    bullets.clear()
    obstacles.clear()
    powerups.clear()

def spawn_obstacle():
    angle = random.uniform(0, math.pi * 2)
    speed_mult = 2.0 if options_overdrive else 1.0
    speed = (random.uniform(1.2, 2.2) + (multiplier * 0.1) + (level * 0.15)) * 0.35 * speed_mult
    obstacles.append({"angle": angle, "dist": 5, "speed": speed, "sides": random.choice([3, 4, 5, 6])})

def spawn_powerup(angle, dist):
    stress_rarity_penalty = (multiplier - 1) * 0.05
    stage_rarity_penalty = (level - 1) * 0.03
    roll = random.random() + stress_rarity_penalty + stage_rarity_penalty
    if roll < 0.03:
        ptype = 'F'
    elif roll < 0.12:
        ptype = 'S' 
    elif roll < 0.35:
        ptype = 'H'
    else:
        ptype = 'R'
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
    
    if current_state == STATE_MULTIPLAYER_LOBBY and client_socket:
        try:
            client_socket.setblocking(False)
            data = client_socket.recv(1024)
            if data:
                lines = data.decode().strip().split("\n")
                for line in lines:
                    if line:
                        parsed = json.loads(line)
                        if "slot" in parsed:
                            lobby_slot = parsed["slot"]
                            lobby_status_text = f"ASSIGNED SLOT: P{lobby_slot}"
                        if "p1_ready" in parsed and "p2_ready" in parsed:
                            p1_r = parsed["p1_ready"]
                            p2_r = parsed["p2_ready"]
                            remote_ready = p2_r if lobby_slot == 1 else p1_r
                            if p1_r and p2_r:
                                reset_game(1)
                                current_state = STATE_PLAYING
        except:
            pass

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if current_state == STATE_PLAYING:
                    current_state = STATE_MAIN_MENU
                    menu_selection = 0
                elif current_state in (STATE_CAMPAIGN_MENU, STATE_MULTIPLAYER_LOBBY, STATE_OPTIONS, STATE_LEADERBOARD):
                    if current_state == STATE_MULTIPLAYER_LOBBY and client_socket:
                        try:
                            client_socket.close()
                        except:
                            pass
                        client_socket = None
                    current_state = STATE_MAIN_MENU
                    menu_selection = 0
                else:
                    running = False
            
            elif current_state == STATE_WARNING:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    current_state = STATE_MAIN_MENU

            elif current_state == STATE_MAIN_MENU:
                if event.key == pygame.K_UP:
                    menu_selection = (menu_selection - 1) % 4
                elif event.key == pygame.K_DOWN:
                    menu_selection = (menu_selection + 1) % 4
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if menu_selection == 0:
                        reset_game(1)
                        current_state = STATE_PLAYING
                    elif menu_selection == 1:
                        current_state = STATE_CAMPAIGN_MENU
                    elif menu_selection == 2:
                        is_ready = False
                        remote_ready = False
                        lobby_slot = 0
                        lobby_status_text = "CONNECTING TO LOBBY..."
                        try:
                            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            client_socket.connect(("127.0.0.1", SOCKET_PORT))
                            lobby_status_text = "CONNECTED. WAITING FOR SLOT..."
                        except:
                            lobby_status_text = "SERVER OFFLINE. START ANOTHER WINDOW."
                        current_state = STATE_MULTIPLAYER_LOBBY
                    elif menu_selection == 3:
                        secret_typed_buffer = ""
                        current_state = STATE_OPTIONS
            
            elif current_state == STATE_CAMPAIGN_MENU:
                if event.key == pygame.K_LEFT:
                    campaign_level_selected = max(1, campaign_level_selected - 1)
                elif event.key == pygame.K_RIGHT:
                    campaign_level_selected = min(10, campaign_level_selected + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    reset_game(campaign_level_selected)
                    current_state = STATE_PLAYING
            
            elif current_state == STATE_MULTIPLAYER_LOBBY:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE) and client_socket and not is_ready:
                    is_ready = True
                    try:
                        client_socket.sendall(b"READY\n")
                    except:
                        pass

            elif current_state == STATE_OPTIONS:
                if event.key == pygame.K_l:
                    current_state = STATE_LEADERBOARD
                elif overdrive_unlocked and (event.key == pygame.K_UP or event.key == pygame.K_DOWN):
                    options_overdrive = not options_overdrive
                elif not overdrive_unlocked and event.unicode.isalpha():
                    secret_typed_buffer += event.unicode.lower()
                    if "sinnes" in secret_typed_buffer:
                        overdrive_unlocked = True
                        secret_typed_buffer = ""
            
            elif current_state == STATE_LEADERBOARD:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    current_state = STATE_OPTIONS
            
            elif current_state == STATE_PLAYING:
                if event.key == pygame.K_SPACE and shoot_cooldown <= 0:
                    CHAN_SFX.play(SND_LASER)
                    if shotgun_active:
                        for offset in [-0.15, 0.0, 0.15]:
                            bullets.append({"angle": player_angle + offset, "dist": player_distance})
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

    if shoot_cooldown > 0:
        shoot_cooldown -= max(1, round(dt))
    if rapid_fire_timer > 0:
        rapid_fire_timer -= max(1, round(dt))

    # Render target surface (maintains 640x480 aspect ratio internally)
    canvas = pygame.Surface((WIDTH, HEIGHT))

    if current_state == STATE_WARNING:
        canvas.fill(BLACK)
        draw_text(canvas, "WARNING: PHOTOSENSITIVE SEIZURES", WIDTH // 2, 80, RED_TEXT, FONT_LG, center=True)
        draw_text(canvas, "A small percentage of people may experience seizures", WIDTH // 2, 150, WHITE, FONT_SM, center=True)
        draw_text(canvas, "when exposed to certain visual images, including flashing", WIDTH // 2, 175, WHITE, FONT_SM, center=True)
        draw_text(canvas, "lights or patterns that may appear in video games.", WIDTH // 2, 200, WHITE, FONT_SM, center=True)
        draw_text(canvas, "By proceeding, you accept all health risks.", WIDTH // 2, 260, AMBER, FONT_SM, center=True)
        if (frame_count // 30) % 2 == 0:
            draw_text(canvas, "PRESS SPACE OR ENTER TO CONTINUE", WIDTH // 2, 360, GREEN, FONT_MD, center=True)

    elif current_state == STATE_MAIN_MENU:
        canvas.fill(BLACK)
        draw_text(canvas, "POLYBIUS II", WIDTH // 2, 80, CYAN, FONT_XL, center=True)
        
        options = ["1. ARCADE QUICK RUN", "2. CAMPAIGN SELECTOR", "3. ONLINE MULTIPLAYER LOBBY", "4. OPTIONS & SCORES"]
        for idx, opt in enumerate(options):
            color = GREEN if idx == menu_selection else WHITE
            prefix = "> " if idx == menu_selection else "  "
            draw_text(canvas, prefix + opt, WIDTH // 2 - 140, 200 + (idx * 45), color, FONT_MD)
            
        draw_text(canvas, "USE ARROWS TO NAVIGATE | ENTER TO SELECT | ESC TO QUIT", WIDTH // 2, 430, WHITE, FONT_SM, center=True)

    elif current_state == STATE_CAMPAIGN_MENU:
        canvas.fill(BLACK)
        draw_text(canvas, "CAMPAIGN STAGE SELECT", WIDTH // 2, 80, MAGENTA, FONT_LG, center=True)
        draw_text(canvas, f"SELECTED STAGE: {campaign_level_selected}", WIDTH // 2, 180, WHITE, FONT_XL, center=True)
        draw_text(canvas, "USE LEFT/RIGHT ARROWS TO CHOOSE STAGE", WIDTH // 2, 260, CYAN, FONT_MD, center=True)
        if (frame_count // 30) % 2 == 0:
            draw_text(canvas, "PRESS ENTER TO LAUNCH STAGE", WIDTH // 2, 360, GREEN, FONT_MD, center=True)
        draw_text(canvas, "PRESS ESC TO RETURN", WIDTH // 2, 420, AMBER, FONT_SM, center=True)

    elif current_state == STATE_MULTIPLAYER_LOBBY:
        canvas.fill(BLACK)
        draw_text(canvas, "ONLINE MULTIPLAYER LOBBY", WIDTH // 2, 50, CYAN, FONT_LG, center=True)
        draw_text(canvas, lobby_status_text, WIDTH // 2, 110, WHITE, FONT_MD, center=True)
        
        p1_status_str = "PLAYER 1: READY" if (is_ready if lobby_slot == 1 else remote_ready) else "PLAYER 1: WAITING..."
        p2_status_str = "PLAYER 2: READY" if (is_ready if lobby_slot == 2 else remote_ready) else "PLAYER 2: WAITING..."
        
        draw_text(canvas, p1_status_str, WIDTH // 2, 180, GREEN if "READY" in p1_status_str else AMBER, FONT_MD, center=True)
        draw_text(canvas, p2_status_str, WIDTH // 2, 220, GREEN if "READY" in p2_status_str else AMBER, FONT_MD, center=True)
        
        if lobby_slot != 0 and not is_ready:
            if (frame_count // 30) % 2 == 0:
                draw_text(canvas, "PRESS SPACE TO READY UP", WIDTH // 2, 310, CYAN, FONT_MD, center=True)
        elif is_ready:
            draw_text(canvas, "READY LOCKED. WAITING FOR OTHER PLAYER...", WIDTH // 2, 310, WHITE, FONT_SM, center=True)

        draw_text(canvas, "PRESS ESC TO ABORT & RETURN", WIDTH // 2, 420, WHITE, FONT_SM, center=True)

    elif current_state == STATE_OPTIONS:
        canvas.fill(BLACK)
        draw_text(canvas, "OPTIONS & SETTINGS", WIDTH // 2, 80, AMBER, FONT_LG, center=True)
        
        if overdrive_unlocked:
            od_status = "ENABLED" if options_overdrive else "DISABLED"
            od_color = GREEN if options_overdrive else WHITE
            draw_text(canvas, f"OVERDRIVE MODE: {od_status}", WIDTH // 2 - 160, 180, od_color, FONT_MD)
            draw_text(canvas, "PRESS UP/DOWN TO TOGGLE OVERDRIVE", WIDTH // 2, 240, CYAN, FONT_SM, center=True)
        else:
            draw_text(canvas, "TYPE THE SECRET PASSWORD TO UNLOCK MODIFIERS", WIDTH // 2, 180, WHITE, FONT_SM, center=True)

        draw_text(canvas, "PRESS L TO VIEW LEADERBOARDS", WIDTH // 2, 300, MAGENTA, FONT_MD, center=True)
        draw_text(canvas, "PRESS ESC TO RETURN TO MENU", WIDTH // 2, 380, WHITE, FONT_SM, center=True)

    elif current_state == STATE_LEADERBOARD:
        canvas.fill(BLACK)
        draw_text(canvas, "GLOBAL LEADERBOARD", WIDTH // 2, 50, AMBER, FONT_LG, center=True)
        
        for idx, entry in enumerate(leaderboard):
            line_str = f"{idx+1}. {entry[0]}  ---  {entry[1]:06d}"
            draw_text(canvas, line_str, WIDTH // 2, 120 + (idx * 35), WHITE, FONT_MD, center=True)

        if (frame_count // 30) % 2 == 0:
            draw_text(canvas, "PRESS ENTER TO RETURN", WIDTH // 2, 380, GREEN, FONT_MD, center=True)

    elif current_state == STATE_TRANSITION:
        transition_timer -= dt
        canvas.fill(BLACK)
        draw_text(canvas, f"STAGE {level} READY", WIDTH // 2, HEIGHT // 2 - 20, WHITE, FONT_XL, center=True)
        
        if transition_timer <= 0:
            current_state = STATE_PLAYING

    elif current_state == STATE_PLAYING:
        beat_interval = max(6, 30 - (multiplier * 3))
        if frame_count % beat_interval == 0 and not CHAN_HUM.get_busy():
            stress_freq = 55 + (multiplier * 12)
            dynamic_hum = gen_square_wave(stress_freq, 0.15 + (0.02 * multiplier), 0.08)
            CHAN_HUM.play(dynamic_hum)

        keys = pygame.key.get_pressed()
        
        is_static = not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s])
        camping_penalty = 1.4 if is_static else 1.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]: player_velocity -= 0.010 * dt
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: player_velocity += 0.010 * dt
        else: player_velocity *= (0.80 ** dt)
            
        player_velocity = max(-0.12, min(0.12, player_velocity))
        player_angle += player_velocity * dt

        if keys[pygame.K_UP] or keys[pygame.K_w]: player_dist_velocity -= 0.350 * dt
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: player_dist_velocity += 0.350 * dt
        else: player_dist_velocity *= (0.85 ** dt)

        player_dist_velocity = max(-2.50, min(2.50, player_dist_velocity))
        player_distance += player_dist_velocity * dt
        player_distance = max(100, min(280, player_distance))

        if invincible_timer > 0: invincible_timer -= dt
        spawn_rate = max(4, (36 - (multiplier * 2) - (level * 2)))
        if frame_count % spawn_rate == 0:
            spawn_obstacle()

        canvas.fill((40, 0, 40) if strobe_flash else BLACK)
        strobe_flash = False

        active_palette = LEVEL_PALETTES[(level - 1) % len(LEVEL_PALETTES)]

        # TUNNEL RINGS
        cx, cy = WIDTH // 2, HEIGHT // 2
        max_radius = 400
        pulse = math.sin(frame_count * (0.08 + level * 0.01)) * (20 + level * 2)
        spin_speed = (0.02 + (multiplier * 0.008) + (level * 0.005)) * (-1 if multiplier >= 4 else 1)
        sides = 8 if level < 3 else (6 if level < 5 else 10)

        # Ramped up tunnel speed factoring in both stage progression and stress multiplier
        tunnel_speed = 8.5 + (level * 0.6) + (multiplier * 1.5)

        for i in range(45):
            radius = ((frame_count * tunnel_speed + i * 14) % max_radius) + 2 + pulse
            if radius <= 0: continue
            color = active_palette[(i + (frame_count // 5)) % len(active_palette)]
            
            points = []
            for j in range(sides):
                angle = (frame_count * spin_speed) + (j * (2 * math.pi / sides))
                points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
            pygame.draw.polygon(canvas, color, points, width=2)

        if level >= 5:
            for i in range(15):
                radius = ((frame_count * (tunnel_speed * 0.7) + i * 25) % max_radius) + 10
                sq_spin = -spin_speed * 1.5
                color = active_palette[(i + 2) % len(active_palette)]
                
                pts = []
                for j in range(4):
                    angle = (frame_count * sq_spin) + (j * (math.pi / 2) + math.pi/4)
                    pts.append((cx + math.cos(angle) * radius * 1.2, cy + math.sin(angle) * radius * 1.2))
                pygame.draw.polygon(canvas, color, pts, width=2)

        if level >= 10:
            for i in range(12):
                radius = max_radius - ((frame_count * (tunnel_speed * 0.85) + i * 30) % max_radius)
                if radius <= 0: continue
                color = active_palette[(i + 4) % len(active_palette)]
                pygame.draw.circle(canvas, color, (cx, cy), int(radius), width=2)

        for b in bullets[:]:
            b["dist"] -= 12 * dt
            bx, by = cx + math.cos(b["angle"]) * b["dist"], cy + math.sin(b["angle"]) * b["dist"]
            bx_end, by_end = cx + math.cos(b["angle"]) * (b["dist"] + 14), cy + math.sin(b["angle"]) * (b["dist"] + 14)
            pygame.draw.line(canvas, WHITE, (bx, by), (bx_end, by_end), 2)
            if b["dist"] <= 0: bullets.remove(b)

        for p in powerups[:]:
            p["dist"] += p["speed"] * dt
            px_p = cx + math.cos(p["angle"]) * p["dist"]
            py_p = cy + math.sin(p["angle"]) * p["dist"]
            
            if p["type"] == 'F': p_color = MAGENTA
            elif p["type"] == 'S': p_color = CYAN
            elif p["type"] == 'H': p_color = GREEN
            else: p_color = AMBER
                
            if (frame_count // 10) % 2 == 0:
                draw_text(canvas, p["type"], int(px_p - 6), int(py_p - 6), p_color, FONT_MD)

            angle_diff_p = (player_angle - p["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(p["dist"] - player_distance) < 20 and abs(angle_diff_p) < 0.35:
                if p["type"] == 'F': lives = 9
                elif p["type"] == 'S': shotgun_active = True 
                elif p["type"] == 'H': lives += 1
                elif p["type"] == 'R': rapid_fire_timer = 300 
                CHAN_SFX.play(SND_POWERUP)
                powerups.remove(p)
            elif p["dist"] > 400:
                powerups.remove(p)

        for obs in obstacles[:]:
            obs["dist"] += obs["speed"] * dt * camping_penalty
            ox, oy = cx + math.cos(obs["angle"]) * obs["dist"], cy + math.sin(obs["angle"]) * obs["dist"]
            obs_color = active_palette[(frame_count // 4) % len(active_palette)]
            
            poly_pts = []
            size = 8 + (obs["dist"] * 0.045)
            rot = frame_count * 0.12
            for k in range(obs["sides"]):
                a = rot + (k * (2 * math.pi / obs["sides"]))
                poly_pts.append((ox + math.cos(a) * size, oy + math.sin(a) * size))
            pygame.draw.polygon(canvas, obs_color, poly_pts, width=2)

        for obs in obstacles[:]:
            for b in bullets[:]:
                angle_diff = (b["angle"] - obs["angle"] + math.pi) % (2 * math.pi) - math.pi
                if abs(b["dist"] - obs["dist"]) < 20 and abs(angle_diff) < 0.35:
                    score += 100 * multiplier * level
                    if score > high_score: high_score = score
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
                    
                    shake_intensity, strobe_flash = 7, True
                    CHAN_SFX.play(SND_HIT)
                    if obs in obstacles: obstacles.remove(obs)
                    if b in bullets: bullets.remove(b)
                    break

            angle_diff_player = (player_angle - obs["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(obs["dist"] - player_distance) < 20 and abs(angle_diff_player) < 0.35 and invincible_timer <= 0:
                lives -= 1
                multiplier, multiplier_streak = 1, 0
                invincible_timer, shake_intensity = 60, 20
                CHAN_EXPLODE.play(SND_EXPLODE)
                if obs in obstacles: obstacles.remove(obs)
                if lives <= 0:
                    gameover_timer = 150
                    current_state = STATE_GAMEOVER

            if obs["dist"] > 400 and obs in obstacles:
                obstacles.remove(obs)

        px, py = cx + math.cos(player_angle) * player_distance, cy + math.sin(player_angle) * player_distance
        if invincible_timer <= 0 or (int(invincible_timer) // 6) % 2 == 0:
            fa = player_angle + math.pi
            p1 = (px + math.cos(fa) * 12, py + math.sin(fa) * 12)
            p2 = (px + math.cos(fa + 2.4) * 10, py + math.sin(fa + 2.4) * 10)
            p3 = (px + math.cos(fa - 2.4) * 10, py + math.sin(fa - 2.4) * 10)
            pygame.draw.polygon(canvas, CYAN, [p1, p2, p3], width=2)

        # Dynamic subliminals scaling frequency and duration with stress/multiplier
        subliminal_interval = max(30, 180 - (multiplier * 20))
        subliminal_duration = min(45, 20 + (multiplier * 3))

        if frame_count % subliminal_interval == 0:
            subliminal_text = random.choice(SUBLIMINALS)
        if (frame_count % subliminal_interval) < subliminal_duration:
            flash_x = WIDTH // 2 + (random.randint(-10, 10) if multiplier >= 5 else 0)
            flash_y = (cy - 20) + (random.randint(-8, 8) if multiplier >= 6 else 0)
            draw_text(canvas, subliminal_text, flash_x, flash_y, MAGENTA, FONT_LG, center=True)

        draw_text(canvas, f"SCORE: {score:06d}", 20, 15, AMBER, FONT_MD)
        draw_text(canvas, f"HI-SCORE: {high_score:06d}", 20, 35, WHITE, FONT_SM)
        draw_text(canvas, f"STAGE: {level}", 20, 55, CYAN, FONT_MD)
        
        stress_color = RED_TEXT if (multiplier >= 4 and (frame_count // 12) % 2 == 0) else GREEN
        draw_text(canvas, f"STRESS: {multiplier}X", 20, 75, stress_color, FONT_MD)
        
        if rapid_fire_timer > 0:
            draw_text(canvas, "RAPID FIRE", 20, 100, AMBER, FONT_SM)
        if shotgun_active:
            draw_text(canvas, "SPREAD SHOT", 20, 118, CYAN, FONT_SM)

        for i in range(min(lives, 12)):
            pygame.draw.circle(canvas, RED_TEXT, (WIDTH - 30 - (i * 15), 25), 5)

    elif current_state == STATE_GAMEOVER:
        gameover_timer -= dt
        canvas.fill(BLACK)
        draw_text(canvas, "MISSION TERMINATED", WIDTH // 2, 120, RED_TEXT, FONT_XL, center=True)
        draw_text(canvas, f"FINAL SCORE: {score:06d}", WIDTH // 2, 200, AMBER, FONT_LG, center=True)
        draw_text(canvas, f"HIGH SCORE:  {high_score:06d}", WIDTH // 2, 235, WHITE, FONT_LG, center=True)
        
        if (frame_count // 30) % 2 == 0:
            draw_text(canvas, "PRESS ENTER TO CONTINUE", WIDTH // 2, 320, BLUE_TEXT, FONT_MD, center=True)

        if gameover_timer <= 0:
            if check_high_score(score):
                current_state = STATE_ENTER_NAME
            else:
                current_state = STATE_MAIN_MENU
                menu_selection = 0

    elif current_state == STATE_ENTER_NAME:
        canvas.fill(BLACK)
        draw_text(canvas, "NEW HIGH SCORE!", WIDTH // 2, 80, AMBER, FONT_XL, center=True)
        draw_text(canvas, "ENTER YOUR INITIALS", WIDTH // 2, 150, WHITE, FONT_MD, center=True)

        start_x = WIDTH // 2 - 60
        for i, char in enumerate(player_name_chars):
            box_color = GREEN if i == name_cursor_idx else WHITE
            pygame.draw.rect(canvas, box_color, (start_x + (i * 45), 210, 36, 45), 2)
            draw_text(canvas, char, start_x + (i * 45) + 12, 218, box_color, FONT_LG)

        if (frame_count // 30) % 2 == 0:
            draw_text(canvas, "USE ARROWS & ENTER TO SUBMIT", WIDTH // 2, 320, CYAN, FONT_SM, center=True)

    # Correct aspect ratio scaling with letterboxing/pillarboxing
    SCREEN.fill(BLACK)
    win_w, win_h = SCREEN.get_size()
    
    scale = min(win_w / WIDTH, win_h / HEIGHT)
    scaled_w = int(WIDTH * scale)
    scaled_h = int(HEIGHT * scale)
    offset_x = (win_w - scaled_w) // 2
    offset_y = (win_h - scaled_h) // 2

    rx = random.randint(-int(shake_intensity), int(shake_intensity)) if shake_intensity > 0 else 0
    ry = random.randint(-int(shake_intensity), int(shake_intensity)) if shake_intensity > 0 else 0
    if shake_intensity > 0: shake_intensity -= dt

    if multiplier >= 5:
        scaled_down = pygame.transform.smoothscale(canvas, (WIDTH // 2, HEIGHT // 2))
        processed_canvas = pygame.transform.smoothscale(scaled_down, (WIDTH, HEIGHT))
    else:
        processed_canvas = canvas

    scaled_surf = pygame.transform.smoothscale(processed_canvas, (scaled_w, scaled_h))
    SCREEN.blit(scaled_surf, (offset_x + rx, offset_y + ry))

    pygame.display.flip()

server_running = False
if client_socket:
    try:
        client_socket.close()
    except:
        pass
pygame.quit()
sys.exit()