# events.py
import pygame
from storage import save_settings, save_leaderboard
from game_state import (
    STATE_WARNING,
    STATE_MAIN_MENU,
    STATE_CAMPAIGN_MENU,
    STATE_OPTIONS,
    STATE_LEADERBOARD,
    STATE_PLAYING,
    STATE_TRANSITION,
    STATE_GAMEOVER,
    STATE_ENTER_NAME,
    STATE_PAUSED,
)


def handle_events(g, settings, sound_mgr, discord):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            g.running = False

        elif event.type == pygame.KEYDOWN:
            # --- GLOBAL ESCAPE KEY HANDLING ---
            if event.key == pygame.K_ESCAPE:
                if g.current_state in (STATE_PLAYING, STATE_TRANSITION):
                    g.previous_state = g.current_state  # Remember where we paused from
                    g.current_state = STATE_PAUSED
                    g.pause_selection = 0
                elif g.current_state == STATE_PAUSED:
                    # Restore previous state (defaults to STATE_PLAYING if not set)
                    g.current_state = getattr(g, "previous_state", STATE_PLAYING)
                elif g.current_state == STATE_OPTIONS:
                    if g.options_category == 1:
                        g.options_category = 0
                        g.options_item_idx = 0
                    else:
                        g.current_state = STATE_MAIN_MENU
                        g.menu_selection = 0
                elif g.current_state in (STATE_CAMPAIGN_MENU, STATE_LEADERBOARD):
                    g.current_state = STATE_MAIN_MENU
                    g.menu_selection = 0
                elif g.current_state == STATE_MAIN_MENU:
                    g.running = False  # Only quit application if on Main Menu

            # --- PAUSE MENU INPUTS ---
            elif g.current_state == STATE_PAUSED:
                pause_options_count = 6 if g.overdrive_unlocked else 5
                if event.key in (pygame.K_UP, pygame.K_w):
                    g.pause_selection = (g.pause_selection - 1) % pause_options_count
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    g.pause_selection = (g.pause_selection + 1) % pause_options_count
                elif event.key in (
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_a,
                    pygame.K_d,
                ):
                    if g.pause_selection == 0:
                        g.current_state = getattr(g, "previous_state", STATE_PLAYING)
                    elif g.pause_selection == 1:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            settings["master_volume"] = max(
                                0.0, round(settings["master_volume"] - 0.1, 1)
                            )
                        else:
                            settings["master_volume"] = min(
                                1.0, round(settings["master_volume"] + 0.1, 1)
                            )
                        sound_mgr.rebuild_sounds(settings["master_volume"])
                        save_settings(settings)
                    elif g.pause_selection == 2:
                        settings["invert_x"] = not settings["invert_x"]
                        save_settings(settings)
                    elif g.pause_selection == 3:
                        settings["invert_y"] = not settings["invert_y"]
                        save_settings(settings)
                    elif g.pause_selection == 4:
                        settings["colorblind_mode"] = not settings.get(
                            "colorblind_mode", False
                        )
                        save_settings(settings)
                    elif g.pause_selection == 5 and g.overdrive_unlocked:
                        g.options_overdrive = not g.options_overdrive
                elif event.key == pygame.K_q:
                    g.current_state = STATE_MAIN_MENU
                    g.menu_selection = 0

            # --- WARNING SCREEN ---
            elif g.current_state == STATE_WARNING:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    g.current_state = STATE_MAIN_MENU

            # --- MAIN MENU ---
            elif g.current_state == STATE_MAIN_MENU:
                if event.key in (pygame.K_UP, pygame.K_w):
                    g.menu_selection = (
                        g.menu_selection - 1
                    ) % 4  # Wrap around 4 options
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    g.menu_selection = (g.menu_selection + 1) % 4
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if g.menu_selection == 0:
                        g.reset_game(1)
                        g.transition_timer = 120
                        g.current_state = STATE_TRANSITION
                    elif g.menu_selection == 1:
                        g.current_state = STATE_CAMPAIGN_MENU
                    elif g.menu_selection == 2:
                        g.current_state = (
                            STATE_LEADERBOARD  # Open Leaderboard directly!
                        )
                    elif g.menu_selection == 3:
                        g.secret_typed_buffer = ""
                        g.options_category = 0
                        g.active_category_idx = 0
                        g.options_item_idx = 0
                        g.current_state = STATE_OPTIONS

            # --- CAMPAIGN MENU ---
            elif g.current_state == STATE_CAMPAIGN_MENU:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    g.campaign_level_selected = max(1, g.campaign_level_selected - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    g.campaign_level_selected = min(10, g.campaign_level_selected + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    g.reset_game(g.campaign_level_selected)
                    g.transition_timer = 120
                    g.current_state = STATE_TRANSITION

            # --- OPTIONS MENU ---
            elif g.current_state == STATE_OPTIONS:
                categories_count = 3

                # Mode 0: Selecting a category on the left panel
                if g.options_category == 0:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        g.active_category_idx = (
                            g.active_category_idx - 1
                        ) % categories_count
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        g.active_category_idx = (
                            g.active_category_idx + 1
                        ) % categories_count
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_SPACE,
                        pygame.K_RIGHT,
                        pygame.K_d,
                    ):
                        g.options_category = 1
                        g.options_item_idx = 0
                    elif event.key == pygame.K_l:
                        g.current_state = STATE_LEADERBOARD

                # Mode 1: Adjusting items inside the chosen category
                elif g.options_category == 1:
                    if g.active_category_idx == 0:
                        items_count = 2  # Controls
                    elif g.active_category_idx == 1:
                        items_count = 3  # Audio & Video
                    elif g.active_category_idx == 2:
                        items_count = (
                            2 if g.overdrive_unlocked else 1
                        )  # Gameplay & Extras

                    if event.key in (pygame.K_UP, pygame.K_w):
                        g.options_item_idx = (g.options_item_idx - 1) % items_count
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        g.options_item_idx = (g.options_item_idx + 1) % items_count
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        g.options_category = 0
                    elif event.key in (
                        pygame.K_RIGHT,
                        pygame.K_RETURN,
                        pygame.K_SPACE,
                        pygame.K_d,
                    ):
                        # CONTROLS CATEGORY
                        if g.active_category_idx == 0:
                            if g.options_item_idx == 0:
                                settings["invert_x"] = not settings["invert_x"]
                            elif g.options_item_idx == 1:
                                settings["invert_y"] = not settings["invert_y"]
                            save_settings(settings)

                        # AUDIO & VIDEO CATEGORY
                        elif g.active_category_idx == 1:
                            if g.options_item_idx == 1:
                                settings["screen_shake_enabled"] = not settings[
                                    "screen_shake_enabled"
                                ]
                            elif g.options_item_idx == 2:
                                settings["colorblind_mode"] = not settings.get(
                                    "colorblind_mode", False
                                )
                            save_settings(settings)

                        # GAMEPLAY & EXTRAS CATEGORY
                        elif g.active_category_idx == 2:
                            if g.options_item_idx == 0:
                                settings["discord_rpc_enabled"] = not settings[
                                    "discord_rpc_enabled"
                                ]
                                if not settings["discord_rpc_enabled"]:
                                    discord.clear()
                            elif g.options_item_idx == 1 and g.overdrive_unlocked:
                                g.options_overdrive = not g.options_overdrive
                            save_settings(settings)

                    # Allow volume adjustment with Left/Right arrows
                    if g.active_category_idx == 1 and g.options_item_idx == 0:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            settings["master_volume"] = max(
                                0.0, round(settings["master_volume"] - 0.1, 1)
                            )
                            sound_mgr.rebuild_sounds(settings["master_volume"])
                            save_settings(settings)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            settings["master_volume"] = min(
                                1.0, round(settings["master_volume"] + 0.1, 1)
                            )
                            sound_mgr.rebuild_sounds(settings["master_volume"])
                            save_settings(settings)

                # Secret code check
                if not g.overdrive_unlocked and event.unicode.isalpha():
                    g.secret_typed_buffer += event.unicode.lower()
                    if "sinnes" in g.secret_typed_buffer:
                        g.unlock_overdrive(settings)
                        g.secret_typed_buffer = ""

            # --- LEADERBOARD ---
            elif g.current_state == STATE_LEADERBOARD:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    g.current_state = STATE_MAIN_MENU

            # --- PLAYING ---
            elif g.current_state == STATE_PLAYING:
                if event.key == pygame.K_SPACE and g.shoot_cooldown <= 0:
                    sound_mgr.chan_sfx.play(sound_mgr.snd_laser)
                    if g.shotgun_active:
                        for offset in [-0.15, 0.0, 0.15]:
                            g.bullets.append(
                                {
                                    "angle": g.player_angle + offset,
                                    "dist": g.player_distance,
                                }
                            )
                    else:
                        g.bullets.append(
                            {"angle": g.player_angle, "dist": g.player_distance}
                        )
                    g.shoot_cooldown = 8 if g.rapid_fire_timer > 0 else 16

            # --- ENTER NAME (HIGH SCORE) ---
            elif g.current_state == STATE_ENTER_NAME:
                if event.key in (pygame.K_UP, pygame.K_w):
                    curr_char_code = ord(g.player_name_chars[g.name_cursor_idx])
                    curr_char_code = 65 if curr_char_code >= 90 else curr_char_code + 1
                    g.player_name_chars[g.name_cursor_idx] = chr(curr_char_code)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    curr_char_code = ord(g.player_name_chars[g.name_cursor_idx])
                    curr_char_code = 90 if curr_char_code <= 65 else curr_char_code - 1
                    g.player_name_chars[g.name_cursor_idx] = chr(curr_char_code)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    g.name_cursor_idx = max(0, g.name_cursor_idx - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    g.name_cursor_idx = min(2, g.name_cursor_idx + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    new_name = "".join(g.player_name_chars)
                    g.leaderboard.append([new_name, g.score])
                    g.leaderboard.sort(key=lambda x: x[1], reverse=True)
                    g.leaderboard.pop()
                    save_leaderboard(g.leaderboard)
                    g.high_score = g.leaderboard[0][1]
                    g.current_state = STATE_MAIN_MENU
                    g.menu_selection = 0
