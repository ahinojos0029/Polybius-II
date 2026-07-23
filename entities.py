# entities.py
import math
import random


def spawn_fragment(obstacles, angle, dist, level):
    obstacles.append(
        {
            "angle": angle + random.choice([-0.25, 0.25]),
            "dist": dist,
            "speed": 6.0 + (level * 0.5),
            "sides": 3,  # Shard shape
            "is_fragment": True,
        }
    )


def spawn_obstacle(obstacles, is_overdrive, level, multiplier):
    # Determine cluster size based on mode and active stress
    high_stress = level >= 3 or multiplier >= 4

    if is_overdrive:
        # Overdrive spawns 2 to 4 asteroids PER TICK
        cluster_count = random.randint(2, 3) + (1 if high_stress else 0)
    else:
        # Base mode spawns 1 to 2 asteroids PER TICK at higher stress
        cluster_count = random.randint(1, 2) if high_stress else 1

    for _ in range(cluster_count):
        # Scatter angles across the 360-degree radial core
        angle = random.uniform(0, 2 * math.pi)

        # Speed scaling
        base_speed = random.uniform(1.2, 2.2) + (level * 0.25) + (multiplier * 0.15)
        if is_overdrive:
            base_speed *= 1.3  # Faster incoming trajectory for Overdrive

        sides = random.choice([3, 4, 5, 6])

        obstacles.append(
            {
                "angle": angle,
                "dist": 10.0,  # Center core spawn point
                "speed": base_speed,
                "sides": sides,
                "is_fragment": False,
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
