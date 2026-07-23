# entities.py
import math
import random

def spawn_obstacle(obstacles, options_overdrive, level, multiplier):
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

def spawn_powerup(powerups, angle, dist, level, multiplier):
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