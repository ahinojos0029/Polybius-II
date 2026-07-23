# render.py
import math
import random
import pygame
from config import (
    AMBER,
    BLACK,
    BLUE_TEXT,
    CB_PLAYER,
    CYAN,
    GREEN,
    LEVEL_PALETTES,
    MAGENTA,
    RED_TEXT,
    SUBLIMINALS,
    WHITE,
    WIDTH,
    HEIGHT,
)
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


def render_frame(canvas, g, ui, settings):
    # --- 1. SCREEN SHAKE OFFSET CALCULATION ---
    if (
        g.shake_intensity > 0
        and g.current_state in (STATE_PLAYING, STATE_PAUSED)
        and settings.get("screen_shake_enabled", True)
    ):
        intensity = int(g.shake_intensity)
        render_offset_x = random.randint(-intensity, intensity)
        render_offset_y = random.randint(-intensity, intensity)
        g.shake_intensity = max(0, g.shake_intensity - 1)
    else:
        render_offset_x = 0
        render_offset_y = 0
        g.shake_intensity = 0

    if g.current_state == STATE_WARNING:
        canvas.fill(BLACK)
        ui.draw_text(
            canvas,
            "WARNING: PHOTOSENSITIVE SEIZURES",
            WIDTH // 2,
            80,
            RED_TEXT,
            "lg",
            center=True,
        )
        ui.draw_text(
            canvas,
            "A small percentage of people may experience seizures",
            WIDTH // 2,
            150,
            WHITE,
            "sm",
            center=True,
        )
        ui.draw_text(
            canvas,
            "when exposed to certain visual images, including flashing",
            WIDTH // 2,
            175,
            WHITE,
            "sm",
            center=True,
        )
        ui.draw_text(
            canvas,
            "lights or patterns that may appear in video games.",
            WIDTH // 2,
            200,
            WHITE,
            "sm",
            center=True,
        )
        ui.draw_text(
            canvas,
            "By proceeding, you accept all health risks.",
            WIDTH // 2,
            260,
            AMBER,
            "sm",
            center=True,
        )
        if (g.frame_count // 30) % 2 == 0:
            ui.draw_text(
                canvas,
                "PRESS SPACE OR ENTER TO CONTINUE",
                WIDTH // 2,
                360,
                GREEN,
                "md",
                center=True,
            )

    elif g.current_state == STATE_MAIN_MENU:
        canvas.fill(BLACK)
        ui.draw_text(canvas, "POLYBIUS", WIDTH // 2, 80, CYAN, "xl", center=True)
        options = [
            "1. ARCADE QUICK RUN",
            "2. CAMPAIGN SELECTOR",
            "3. LEADERBOARD",
            "4. OPTIONS",
        ]
        for idx, opt in enumerate(options):
            color = GREEN if idx == g.menu_selection else WHITE
            prefix = "> " if idx == g.menu_selection else "  "
            ui.draw_text(
                canvas, prefix + opt, WIDTH // 2 - 140, 220 + (idx * 45), color, "md"
            )
        ui.draw_text(
            canvas,
            "USE ARROWS TO NAVIGATE | ENTER TO SELECT | ESC TO QUIT",
            WIDTH // 2,
            430,
            WHITE,
            "sm",
            center=True,
        )

    elif g.current_state == STATE_CAMPAIGN_MENU:
        canvas.fill(BLACK)
        ui.draw_text(
            canvas, "CAMPAIGN STAGE SELECT", WIDTH // 2, 80, MAGENTA, "lg", center=True
        )
        ui.draw_text(
            canvas,
            f"SELECTED STAGE: {g.campaign_level_selected}",
            WIDTH // 2,
            180,
            WHITE,
            "xl",
            center=True,
        )
        ui.draw_text(
            canvas,
            "USE LEFT/RIGHT ARROWS TO CHOOSE STAGE",
            WIDTH // 2,
            260,
            CYAN,
            "md",
            center=True,
        )
        if (g.frame_count // 30) % 2 == 0:
            ui.draw_text(
                canvas,
                "PRESS ENTER TO LAUNCH STAGE",
                WIDTH // 2,
                360,
                GREEN,
                "md",
                center=True,
            )
        ui.draw_text(
            canvas, "PRESS ESC TO RETURN", WIDTH // 2, 420, AMBER, "sm", center=True
        )

    elif g.current_state == STATE_OPTIONS:
        canvas.fill(BLACK)
        ui.draw_text(
            canvas, "SYSTEM CONFIGURATION", WIDTH // 2, 35, AMBER, "lg", center=True
        )

        categories = ["CONTROLS", "AUDIO & VIDEO", "EXTRAS"]

        # Divider Line
        pygame.draw.line(canvas, WHITE, (210, 85), (210, 370), 1)

        # Left Column: Categories
        for idx, cat in enumerate(categories):
            if idx == g.active_category_idx:
                color = GREEN if g.options_category == 0 else AMBER
                prefix = "> " if g.options_category == 0 else "  "
            else:
                color = WHITE
                prefix = "  "
            ui.draw_text(canvas, prefix + cat, 20, 110 + (idx * 50), color, "md")

        # Right Column: Submenu Items
        opts = []
        if g.active_category_idx == 0:
            opts = [
                ("INVERT HORIZONTAL (X)", "ON" if settings["invert_x"] else "OFF"),
                ("INVERT VERTICAL (Y)", "ON" if settings["invert_y"] else "OFF"),
            ]
        elif g.active_category_idx == 1:
            opts = [
                (
                    "STRESS VOLUME",
                    (
                        f"{int(settings['master_volume'] * 100)}%"
                        if settings["master_volume"] > 0
                        else "MUTED"
                    ),
                ),
                (
                    "SCREEN SHAKE",
                    "ENABLED" if settings["screen_shake_enabled"] else "DISABLED",
                ),
                (
                    "COLORBLIND MODE",
                    "ENABLED" if settings.get("colorblind_mode", False) else "DISABLED",
                ),
            ]
        elif g.active_category_idx == 2:
            opts = [
                (
                    "DISCORD RICH PRESENCE",
                    "ENABLED" if settings["discord_rpc_enabled"] else "DISABLED",
                ),
            ]
            if g.overdrive_unlocked:
                opts.append(
                    ("OVERDRIVE MODE", "ENABLED" if g.options_overdrive else "DISABLED")
                )

        for idx, (label, val) in enumerate(opts):
            if g.options_category == 1 and idx == g.options_item_idx:
                color = GREEN
                prefix = "> "
            else:
                color = WHITE if g.options_category == 1 else (130, 130, 130)
                prefix = "  "
            ui.draw_text(
                canvas, f"{prefix}{label}: {val}", 225, 110 + (idx * 42), color, "md"
            )

        if not g.overdrive_unlocked:
            ui.draw_text(
                canvas,
                "TYPE SECRET PASSWORD FOR MORE SETTINGS",
                WIDTH // 2,
                385,
                CYAN,
                "sm",
                center=True,
            )

        hint = (
            "ENTER/RIGHT: CHOOSE CATEGORY | ESC: MAIN MENU"
            if g.options_category == 0
            else "ARROWS: ADJUST | ESC: BACK TO CATEGORIES"
        )
        ui.draw_text(canvas, hint, WIDTH // 2, 430, WHITE, "sm", center=True)

    elif g.current_state == STATE_LEADERBOARD:
        canvas.fill(BLACK)

        view_board = (
            g.leaderboard_overdrive if g.leaderboard_tab == 1 else g.leaderboard_normal
        )
        title_text = (
            "OVERDRIVE LEADERBOARD (2X PTS)"
            if g.leaderboard_tab == 1
            else "STANDARD LEADERBOARD"
        )
        title_color = RED_TEXT if g.leaderboard_tab == 1 else AMBER

        ui.draw_text(canvas, title_text, WIDTH // 2, 40, title_color, "lg", center=True)
        ui.draw_text(
            canvas,
            "< LEFT / RIGHT TO SWITCH BOARDS >",
            WIDTH // 2,
            75,
            CYAN,
            "sm",
            center=True,
        )

        for idx, entry in enumerate(view_board):
            line_str = f"{idx+1}. {entry[0]}  ---  {entry[1]:06d}"
            ui.draw_text(
                canvas, line_str, WIDTH // 2, 125 + (idx * 35), WHITE, "md", center=True
            )

        if (g.frame_count // 30) % 2 == 0:
            ui.draw_text(
                canvas,
                "PRESS ENTER OR ESC TO RETURN",
                WIDTH // 2,
                380,
                GREEN,
                "md",
                center=True,
            )

    elif g.current_state == STATE_TRANSITION:
        canvas.fill(BLACK)
        cx, cy = WIDTH // 2, HEIGHT // 2
        max_radius = 400
        spin_speed = 0.05
        active_palette = LEVEL_PALETTES[(g.level - 1) % len(LEVEL_PALETTES)]
        for i in range(20):
            radius = ((g.frame_count * 6.0 + i * 18) % max_radius) + 2
            color = active_palette[i % len(active_palette)]
            points = []
            for j in range(6):
                angle = (g.frame_count * spin_speed) + (j * (2 * math.pi / 6))
                points.append(
                    (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
                )
            pygame.draw.polygon(canvas, color, points, width=1)

        ui.draw_text(
            canvas,
            f"STAGE {g.level} READY",
            WIDTH // 2,
            HEIGHT // 2 - 20,
            CYAN,
            "xl",
            center=True,
        )
        if (g.frame_count // 20) % 2 == 0:
            ui.draw_text(
                canvas,
                "PREPARE YOURSELF",
                WIDTH // 2,
                HEIGHT // 2 + 30,
                AMBER,
                "md",
                center=True,
            )

    elif g.current_state in (STATE_PLAYING, STATE_PAUSED):
        canvas.fill(
            (40, 0, 40)
            if (g.strobe_flash and g.current_state == STATE_PLAYING)
            else BLACK
        )
        g.strobe_flash = False
        active_palette = LEVEL_PALETTES[(g.level - 1) % len(LEVEL_PALETTES)]

        # Tunnel Rendering
        cx, cy = WIDTH // 2, HEIGHT // 2
        max_radius = 400
        pulse = math.sin(g.frame_count * (0.08 + g.level * 0.01)) * (20 + g.level * 2)
        spin_speed = (0.02 + (g.multiplier * 0.008) + (g.level * 0.005)) * (
            -1 if g.multiplier >= 4 else 1
        )
        if g.options_overdrive:
            spin_speed *= 1.8

        sides = 8 if g.level < 3 else (6 if g.level < 5 else 10)

        overdrive_mult = 1.75 if g.options_overdrive else 1.0
        tunnel_speed = (8.5 + (g.level * 0.6) + (g.multiplier * 1.5)) * overdrive_mult

        for i in range(45):
            radius = ((g.frame_count * tunnel_speed + i * 14) % max_radius) + 2 + pulse
            if radius <= 0:
                continue
            color = active_palette[(i + (g.frame_count // 5)) % len(active_palette)]
            points = []
            for j in range(sides):
                angle = (g.frame_count * spin_speed) + (j * (2 * math.pi / sides))
                points.append(
                    (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
                )
            pygame.draw.polygon(canvas, color, points, width=2)

        if g.level >= 5:
            for i in range(15):
                radius = (
                    (g.frame_count * (tunnel_speed * 0.7) + i * 25) % max_radius
                ) + 10
                sq_spin = -spin_speed * 1.5
                color = active_palette[(i + 2) % len(active_palette)]
                pts = []
                for j in range(4):
                    angle = (g.frame_count * sq_spin) + (
                        j * (math.pi / 2) + math.pi / 4
                    )
                    pts.append(
                        (
                            cx + math.cos(angle) * radius * 1.2,
                            cy + math.sin(angle) * radius * 1.2,
                        )
                    )
                pygame.draw.polygon(canvas, color, pts, width=2)

        if g.level >= 10:
            for i in range(12):
                radius = max_radius - (
                    (g.frame_count * (tunnel_speed * 0.85) + i * 30) % max_radius
                )
                if radius <= 0:
                    continue
                color = active_palette[(i + 4) % len(active_palette)]
                pygame.draw.circle(canvas, color, (cx, cy), int(radius), width=2)

        # Bullets
        for b in g.bullets:
            bx, by = (
                cx + math.cos(b["angle"]) * b["dist"],
                cy + math.sin(b["angle"]) * b["dist"],
            )
            bx_end, by_end = cx + math.cos(b["angle"]) * (
                b["dist"] + 14
            ), cy + math.sin(b["angle"]) * (b["dist"] + 14)
            pygame.draw.line(canvas, WHITE, (bx, by), (bx_end, by_end), 2)

        # Powerups
        for p in g.powerups:
            px_p = cx + math.cos(p["angle"]) * p["dist"]
            py_p = cy + math.sin(p["angle"]) * p["dist"]
            p_color = (
                MAGENTA
                if p["type"] == "F"
                else (
                    CYAN if p["type"] == "S" else (GREEN if p["type"] == "H" else AMBER)
                )
            )
            if (g.frame_count // 10) % 2 == 0:
                ui.draw_text(
                    canvas, p["type"], int(px_p - 6), int(py_p - 6), p_color, "md"
                )

        # Obstacles
        for obs in g.obstacles:
            ox, oy = (
                cx + math.cos(obs["angle"]) * obs["dist"],
                cy + math.sin(obs["angle"]) * obs["dist"],
            )
            obs_color = active_palette[(g.frame_count // 4) % len(active_palette)]
            poly_pts = []
            size = 8 + (obs["dist"] * 0.045)
            rot = g.frame_count * 0.12
            for k in range(obs["sides"]):
                a = rot + (k * (2 * math.pi / obs["sides"]))
                poly_pts.append((ox + math.cos(a) * size, oy + math.sin(a) * size))
            pygame.draw.polygon(canvas, obs_color, poly_pts, width=2)

        # Player Ship
        px, py = (
            cx + math.cos(g.player_angle) * g.player_distance,
            cy + math.sin(g.player_angle) * g.player_distance,
        )
        if g.invincible_timer <= 0 or (int(g.invincible_timer) // 6) % 2 == 0:
            fa = g.player_angle + math.pi
            p1 = (px + math.cos(fa) * 12, py + math.sin(fa) * 12)
            p2 = (px + math.cos(fa + 2.4) * 10, py + math.sin(fa + 2.4) * 10)
            p3 = (px + math.cos(fa - 2.4) * 10, py + math.sin(fa - 2.4) * 10)

            player_color = CB_PLAYER if settings.get("colorblind_mode", False) else CYAN
            if settings.get("colorblind_mode", False):
                pygame.draw.polygon(canvas, BLACK, [p1, p2, p3], width=5)
            pygame.draw.polygon(canvas, player_color, [p1, p2, p3], width=2)

        # --- Randomized & High-Contrast Subliminals ---
        dt = 1.0  # Or pass 'dt' into render_frame if available

        # 1. Countdown cooldown when no message is active
        if getattr(g, "subliminal_timer", 0) <= 0:
            g.next_subliminal_cooldown -= 1.0 * dt
            if g.next_subliminal_cooldown <= 0 and g.current_state == STATE_PLAYING:
                # Pick a new random phrase
                g.subliminal_text = random.choice(SUBLIMINALS)

                # Active flash duration (20 to 45 ticks based on multiplier)
                g.subliminal_timer = min(45, 20 + (g.multiplier * 3))

                # Set a RANDOM interval for the next appearance
                min_wait = max(40, 120 - (g.multiplier * 10))
                max_wait = max(90, 240 - (g.multiplier * 15))
                g.next_subliminal_cooldown = float(random.randint(min_wait, max_wait))

        # 2. Render & decrement active flash timer
        if getattr(g, "subliminal_timer", 0) > 0 and g.current_state == STATE_PLAYING:
            g.subliminal_timer -= 1.0 * dt

            # Compute high-contrast color by inverting the current level background
            bg_color = active_palette[0]
            contrast_color = (255 - bg_color[0], 255 - bg_color[1], 255 - bg_color[2])

            # Position centered at cy + high stress jitter
            flash_x = (WIDTH // 2) + (
                random.randint(-10, 10) if g.multiplier >= 5 else 0
            )
            flash_y = cy + (random.randint(-8, 8) if g.multiplier >= 6 else 0)

            ui.draw_text(
                canvas,
                g.subliminal_text,
                flash_x,
                flash_y,
                contrast_color,
                "lg",
                center=True,
            )

        # HUD UI
        ui.draw_text(canvas, f"SCORE: {g.score:06d}", 20, 15, AMBER, "md")
        ui.draw_text(canvas, f"HI-SCORE: {g.high_score:06d}", 20, 35, WHITE, "sm")
        ui.draw_text(canvas, f"STAGE: {g.level}", 20, 55, CYAN, "md")

        stress_color = (
            RED_TEXT
            if (g.multiplier >= 4 and (g.frame_count // 12) % 2 == 0)
            else GREEN
        )
        ui.draw_text(canvas, f"STRESS: {g.multiplier}X", 20, 75, stress_color, "md")

        if g.rapid_fire_timer > 0:
            ui.draw_text(canvas, "RAPID FIRE", 20, 100, AMBER, "sm")
        if g.shotgun_active:
            ui.draw_text(canvas, "SPREAD SHOT", 20, 118, CYAN, "sm")

        # --- Overdrive HUD Indicator & Heat Gauge ---
        if g.options_overdrive:
            ui.draw_text(canvas, "OVERDRIVE: ACTIVE [2X PTS]", 20, 138, RED_TEXT, "sm")

            gun_heat = getattr(g, "gun_heat", 0.0)
            is_overheated = getattr(g, "overheated", False)
            heat_color = (
                RED_TEXT if is_overheated else (AMBER if gun_heat > 60 else GREEN)
            )

            pygame.draw.rect(canvas, WHITE, (20, 155, 100, 8), 1)
            pygame.draw.rect(canvas, heat_color, (21, 156, int(gun_heat * 0.98), 6))
            if is_overheated:
                if (g.frame_count // 10) % 2 == 0:
                    ui.draw_text(canvas, "OVERHEAT!", 128, 152, RED_TEXT, "sm")

        for i in range(min(g.lives, 12)):
            pygame.draw.circle(canvas, RED_TEXT, (WIDTH - 30 - (i * 15), 25), 5)

        # Pause Overlay
        if g.current_state == STATE_PAUSED:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(210)
            overlay.fill(BLACK)
            canvas.blit(overlay, (0, 0))

            ui.draw_text(
                canvas, "GAME PAUSED", WIDTH // 2, 50, AMBER, "xl", center=True
            )
            pause_opts = [
                ("RESUME GAME", ""),
                ("STRESS VOLUME", f"{int(settings['master_volume'] * 100)}%"),
                ("INVERT X", "ON" if settings["invert_x"] else "OFF"),
                ("INVERT Y", "ON" if settings["invert_y"] else "OFF"),
                (
                    "COLORBLIND MODE",
                    "ON" if settings.get("colorblind_mode", False) else "OFF",
                ),
            ]
            if g.overdrive_unlocked:
                pause_opts.append(
                    ("OVERDRIVE MODE", "ON" if g.options_overdrive else "OFF")
                )

            for idx, (label, val) in enumerate(pause_opts):
                color = GREEN if idx == g.pause_selection else WHITE
                prefix = "> " if idx == g.pause_selection else "  "
                text_str = f"{prefix}{label}: {val}" if val else f"{prefix}{label}"
                ui.draw_text(
                    canvas,
                    text_str,
                    WIDTH // 2,
                    130 + (idx * 35),
                    color,
                    "md",
                    center=True,
                )

            ui.draw_text(
                canvas,
                "PRESS [Q] TO ABORT RUN & EXIT TO MENU",
                WIDTH // 2,
                395,
                RED_TEXT,
                "sm",
                center=True,
            )
            ui.draw_text(
                canvas, "PRESS ESC TO RESUME", WIDTH // 2, 425, CYAN, "sm", center=True
            )

    elif g.current_state == STATE_GAMEOVER:
        canvas.fill(BLACK)
        ui.draw_text(
            canvas, "MISSION TERMINATED", WIDTH // 2, 120, RED_TEXT, "xl", center=True
        )
        ui.draw_text(
            canvas,
            f"FINAL SCORE: {g.score:06d}",
            WIDTH // 2,
            200,
            AMBER,
            "lg",
            center=True,
        )
        ui.draw_text(
            canvas,
            f"HIGH SCORE:  {g.high_score:06d}",
            WIDTH // 2,
            235,
            WHITE,
            "lg",
            center=True,
        )
        if (g.frame_count // 30) % 2 == 0:
            ui.draw_text(
                canvas,
                "PRESS ENTER TO CONTINUE",
                WIDTH // 2,
                320,
                BLUE_TEXT,
                "md",
                center=True,
            )

    elif g.current_state == STATE_ENTER_NAME:
        canvas.fill(BLACK)
        ui.draw_text(
            canvas, "NEW HIGH SCORE!", WIDTH // 2, 80, AMBER, "xl", center=True
        )
        ui.draw_text(
            canvas, "ENTER YOUR INITIALS", WIDTH // 2, 150, WHITE, "md", center=True
        )
        start_x = WIDTH // 2 - 60
        for i, char in enumerate(g.player_name_chars):
            box_color = GREEN if i == g.name_cursor_idx else WHITE
            pygame.draw.rect(canvas, box_color, (start_x + (i * 45), 210, 36, 45), 2)
            ui.draw_text(canvas, char, start_x + (i * 45) + 12, 218, box_color, "lg")
        if (g.frame_count // 30) % 2 == 0:
            ui.draw_text(
                canvas,
                "USE ARROWS & ENTER TO SUBMIT",
                WIDTH // 2,
                320,
                CYAN,
                "sm",
                center=True,
            )

    return render_offset_x, render_offset_y
