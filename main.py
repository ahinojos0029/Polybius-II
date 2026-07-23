# main.py
import math
import random
import sys
import pygame

from config import BLACK, WIDTH, HEIGHT
from storage import load_settings
from audio import SoundManager, gen_square_wave
from discord_rpc import DiscordManager
from ui import UIRenderer
from entities import spawn_obstacle, spawn_powerup, spawn_fragment

from game_state import (
    GameState, STATE_WARNING, STATE_MAIN_MENU, STATE_CAMPAIGN_MENU,
    STATE_OPTIONS, STATE_LEADERBOARD, STATE_PLAYING, STATE_TRANSITION,
    STATE_GAMEOVER, STATE_ENTER_NAME, STATE_PAUSED
)
from events import handle_events
from render import render_frame

# Initialization
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=256)
pygame.init()
pygame.mixer.init()

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("POLYBIUS - (C) 2026 ARMANDO HINOJOSA")
CLOCK = pygame.time.Clock()

settings = load_settings()
sound_mgr = SoundManager(settings["master_volume"])
ui = UIRenderer()
discord = DiscordManager()
g = GameState()

if settings.get("discord_rpc_enabled", True):
    discord.connect()

# Main Loop
while g.running:
    dt = CLOCK.tick(60) / 1000.0 * 60.0
    if dt > 3.0:
        dt = 3.0

    g.frame_count += 1

    # Discord RPC Sync
    if g.frame_count % 60 == 0:
        if g.current_state in (STATE_WARNING, STATE_MAIN_MENU, STATE_CAMPAIGN_MENU, STATE_OPTIONS, STATE_LEADERBOARD):
            discord.update(settings["discord_rpc_enabled"], "In Arcade Cabinet", "Main Menu")
        elif g.current_state in (STATE_PLAYING, STATE_TRANSITION):
            discord.update(settings["discord_rpc_enabled"], f"Stage {g.level} | Score: {g.score:06d}", f"Stress: {g.multiplier}X")
        elif g.current_state == STATE_PAUSED:
            discord.update(settings["discord_rpc_enabled"], f"Stage {g.level} | PAUSED", f"Score: {g.score:06d}")
        elif g.current_state == STATE_GAMEOVER:
            discord.update(settings["discord_rpc_enabled"], "Mission Terminated", f"Final Score: {g.score:06d}")

    # Handle Events
    handle_events(g, settings, sound_mgr, discord)

    # Gameplay Timers & State Updates
    if g.current_state == STATE_TRANSITION:
        g.transition_timer -= dt
        if g.transition_timer <= 0:
            g.current_state = STATE_PLAYING

    elif g.current_state == STATE_GAMEOVER:
        g.gameover_timer -= dt
        if g.gameover_timer <= 0:
            if g.check_high_score():
                g.current_state = STATE_ENTER_NAME
            else:
                g.current_state = STATE_MAIN_MENU
                g.menu_selection = 0

    elif g.current_state == STATE_PLAYING:
        if g.shoot_cooldown > 0:
            g.shoot_cooldown -= max(1, round(dt))
        if g.rapid_fire_timer > 0:
            g.rapid_fire_timer -= max(1, round(dt))

        # --- Overdrive Gun Heat Cooling (HARDENED: Slower cooling rate) ---
        if g.options_overdrive:
            g.gun_heat = max(0.0, getattr(g, 'gun_heat', 0.0) - 1.0 * dt)
            if getattr(g, 'overheated', False) and g.gun_heat <= 0:
                g.overheated = False

        beat_interval = max(4, 24 - (g.multiplier * 3))
        if g.frame_count % beat_interval == 0 and not sound_mgr.chan_hum.get_busy():
            stress_freq = 55 + (g.multiplier * 14)
            dynamic_hum = gen_square_wave(stress_freq, 0.15 + (0.02 * g.multiplier), 0.08, settings["master_volume"])
            sound_mgr.chan_hum.play(dynamic_hum)

        keys = pygame.key.get_pressed()
        x_dir = (1 if keys[pygame.K_LEFT] or keys[pygame.K_a] else 0) - (1 if keys[pygame.K_RIGHT] or keys[pygame.K_d] else 0)
        y_dir = (1 if keys[pygame.K_DOWN] or keys[pygame.K_s] else 0) - (1 if keys[pygame.K_UP] or keys[pygame.K_w] else 0)

        # --- Player Shooting Input & Overheat Logic ---
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and g.shoot_cooldown <= 0:
            if not (g.options_overdrive and getattr(g, 'overheated', False)):
                cooldown_val = 7 if g.rapid_fire_timer > 0 else 14  # Slightly slower firing cooldown
                g.shoot_cooldown = cooldown_val

                if g.options_overdrive:
                    g.gun_heat = getattr(g, 'gun_heat', 0.0) + 24.0  # HARDENED: Builds heat faster
                    if g.gun_heat >= 100.0:
                        g.gun_heat = 100.0
                        g.overheated = True
                        sound_mgr.chan_sfx.play(sound_mgr.snd_explode)

                if g.shotgun_active:
                    for spread in [-0.2, 0.0, 0.2]:
                        g.bullets.append({"angle": g.player_angle + spread, "dist": g.player_distance})
                else:
                    g.bullets.append({"angle": g.player_angle, "dist": g.player_distance})

        if settings["invert_x"]:
            x_dir *= -1
        if settings["invert_y"]:
            y_dir *= -1

        is_static = x_dir == 0 and y_dir == 0
        camping_penalty = 1.8 if is_static else 1.0  # HARDENED: Camping increases incoming speed by 80%

        if x_dir != 0:
            g.player_velocity += (x_dir * 0.012) * dt
        else:
            g.player_velocity *= 0.82**dt

        g.player_velocity = max(-0.14, min(0.14, g.player_velocity))
        g.player_angle += g.player_velocity * dt

        if y_dir != 0:
            g.player_dist_velocity += (y_dir * 0.40) * dt
        else:
            g.player_dist_velocity *= 0.85**dt

        g.player_dist_velocity = max(-3.0, min(3.0, g.player_dist_velocity))
        g.player_distance += g.player_dist_velocity * dt
        g.player_distance = max(100, min(280, g.player_distance))

        if g.invincible_timer > 0:
            g.invincible_timer -= dt

        # HARDENED: Faster spawn rate scaling (floor lowered from 4 to 2 frames)
        spawn_rate = max(2, (28 - (g.multiplier * 3) - (g.level * 2)))
        if g.frame_count % spawn_rate == 0:
            spawn_obstacle(g.obstacles, g.options_overdrive, g.level, g.multiplier)

        # Bullets movement
        for b in g.bullets[:]:
            b["dist"] -= 14 * dt  # Faster bullet velocity
            if b["dist"] <= 0:
                g.bullets.remove(b)

        # Powerup movement & pickup
        for p in g.powerups[:]:
            p["dist"] += p["speed"] * dt
            angle_diff_p = (g.player_angle - p["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(p["dist"] - g.player_distance) < 15 and abs(angle_diff_p) < 0.25:
                if p["type"] == "F":
                    g.lives = 5  # HARDENED: Full heal gives 5 max
                elif p["type"] == "S":
                    g.shotgun_active = True
                elif p["type"] == "H":
                    g.lives += 1
                elif p["type"] == "R":
                    g.rapid_fire_timer = 200  # Shorter rapid fire duration
                sound_mgr.chan_sfx.play(sound_mgr.snd_powerup)
                g.powerups.remove(p)
            elif p["dist"] > 400:
                g.powerups.remove(p)

        # Obstacles movement & collisions
        for obs in g.obstacles[:]:
            obs["dist"] += obs["speed"] * dt * camping_penalty
            
            for b in g.bullets[:]:
                angle_diff = (b["angle"] - obs["angle"] + math.pi) % (2 * math.pi) - math.pi
                # HARDENED: Tighter bullet-to-obstacle hitboxes
                if abs(b["dist"] - obs["dist"]) < 15 and abs(angle_diff) < 0.25:
                    g.score += 100 * g.multiplier * g.level
                    if g.score > g.high_score:
                        g.high_score = g.score
                    g.multiplier_streak += 1
                    g.level_kills += 1

                    # --- Overdrive Splitting Mechanic ---
                    if g.options_overdrive and not obs.get("is_fragment", False):
                        spawn_fragment(g.obstacles, obs["angle"], obs["dist"], g.level)
                        spawn_fragment(g.obstacles, obs["angle"], obs["dist"], g.level)

                    # Lower powerup drop rate (15% vs 25%)
                    if random.random() < 0.15:
                        spawn_powerup(g.powerups, obs["angle"], obs["dist"], g.level, g.multiplier)
                    
                    # HARDENED: Requires 25 kills per level (up from 15)
                    if g.level_kills >= 25:
                        g.level += 1
                        g.level_kills = 0
                        g.transition_timer = 120
                        g.shotgun_active = False
                        sound_mgr.chan_music.play(sound_mgr.snd_stage_clear)
                        g.current_state = STATE_TRANSITION
                    
                    # HARDENED: Takes 6 kills per multiplier step (up from 4)
                    if g.multiplier_streak % 6 == 0 and g.multiplier < 8:
                        g.multiplier += 1
                    if settings["screen_shake_enabled"]:
                        g.shake_intensity = 7
                    g.strobe_flash = True
                    sound_mgr.chan_sfx.play(sound_mgr.snd_hit)
                    if obs in g.obstacles:
                        g.obstacles.remove(obs)
                    if b in g.bullets:
                        g.bullets.remove(b)
                    break

            # HARDENED: Tighter player hitboxes + shorter i-frames (30 frames vs 60)
            angle_diff_player = (g.player_angle - obs["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(obs["dist"] - g.player_distance) < 14 and abs(angle_diff_player) < 0.22 and g.invincible_timer <= 0:
                g.lives -= 1
                g.multiplier, g.multiplier_streak = 1, 0
                g.invincible_timer = 30
                if settings["screen_shake_enabled"]:
                    g.shake_intensity = 20
                sound_mgr.chan_explode.play(sound_mgr.snd_explode)
                if obs in g.obstacles:
                    g.obstacles.remove(obs)
                if g.lives <= 0:
                    g.gameover_timer = 150
                    g.current_state = STATE_GAMEOVER

            if obs["dist"] > 400 and obs in g.obstacles:
                g.obstacles.remove(obs)

    # Render Frame
    canvas = pygame.Surface((WIDTH, HEIGHT))
    render_frame(canvas, g, ui, settings)

    # Output Scaling & Screen Shake
    SCREEN.fill(BLACK)
    win_w, win_h = SCREEN.get_size()
    scale = min(win_w / WIDTH, win_h / HEIGHT)
    scaled_w, scaled_h = int(WIDTH * scale), int(HEIGHT * scale)
    offset_x, offset_y = (win_w - scaled_w) // 2, (win_h - scaled_h) // 2

    rx = random.randint(-int(g.shake_intensity), int(g.shake_intensity)) if (g.shake_intensity > 0 and settings["screen_shake_enabled"]) else 0
    ry = random.randint(-int(g.shake_intensity), int(g.shake_intensity)) if (g.shake_intensity > 0 and settings["screen_shake_enabled"]) else 0
    if g.shake_intensity > 0 and g.current_state == STATE_PLAYING:
        g.shake_intensity -= dt

    if g.multiplier >= 5 and g.current_state == STATE_PLAYING:
        scaled_down = pygame.transform.smoothscale(canvas, (WIDTH // 2, HEIGHT // 2))
        processed_canvas = pygame.transform.smoothscale(scaled_down, (WIDTH, HEIGHT))
    else:
        processed_canvas = canvas

    scaled_surf = pygame.transform.smoothscale(processed_canvas, (scaled_w, scaled_h))
    SCREEN.blit(scaled_surf, (offset_x + rx, offset_y + ry))
    pygame.display.flip()

pygame.quit()
sys.exit()