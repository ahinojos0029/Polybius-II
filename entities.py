# entities.py
import math
import random

def spawn_fragment(obstacles, angle, dist, level):
    obstacles.append({
        "angle": angle + random.choice([-0.25, 0.25]),
        "dist": dist,
        "speed": 6.0 + (level * 0.5),
        "sides": 3,  # Shard shape
        "is_fragment": True
    })

def spawn_obstacle(obstacles, overdrive, level, multiplier):
    angle = random.uniform(0, 2 * math.pi)
    speed = 2.0 + (level * 0.4) + (multiplier * 0.2)
    sides = random.choice([4, 5, 6])
    obstacles.append({
        "angle": angle,
        "dist": 20,
        "speed": speed,
        "sides": sides,
        "is_fragment": False
    })

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