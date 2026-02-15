import random
import math
from Configs import config1 as config


SEASON_WEIGHTS = {
    "spring": (0.1, 0.3, 0.4, 0.2),
    "summer": (0.05, 0.15, 0.3, 0.5),
    "fall":   (0.2, 0.4, 0.3, 0.1),
    "winter": (0.3, 0.4, 0.2, 0.1),
}

def sample_cloud_coverage(season: str) -> float:
    """
    Regresa un número 0-1.
    Ej: 0.3 significa 30% menos generación.
    """
    w = SEASON_WEIGHTS.get(season.lower(), SEASON_WEIGHTS["spring"])

    buckets = [
        ((0.0, 0.2), w[0]),  # Clear
        ((0.2, 0.6), w[1]),  # Partly Cloudy
        ((0.6, 0.8), w[2]),  # Mostly Cloudy
        ((0.8, 0.9), w[3]),  # Overcast
    ]

    r = random.random() * sum(w)
    acc = 0.0
    for (lo, hi), weight in buckets:
        acc += weight
        if r <= acc:
            return random.uniform(lo, hi)

    return random.uniform(0.0, 0.2)

def solar_generation_kw(env_now_min: int, cloud_coverage: float, inverter_down: bool = False) -> float:
    """
    Curva senoidal (día despejado) + reduce por nubes + clipping por inversor.
    Devuelve kW.
    """
    if inverter_down:
        return 0.0

    hour = int((env_now_min // 60) % 24)

    sun_angle = (hour - 6) * (math.pi / 12.0)
    ideal = config.SOLAR_PEAK * max(0.0, math.sin(sun_angle))


    actual = ideal * (1.0 - cloud_coverage)

    return min(actual, float(config.MAX_INVERTER_OUTPUT))
