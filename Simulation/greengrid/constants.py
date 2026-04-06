from __future__ import annotations

from .enums import HouseholdType, WealthLevel

SEASON_WEIGHTS = {
    "spring": (0.1, 0.3, 0.4, 0.2),
    "summer": (0.05, 0.15, 0.3, 0.5),
    "fall": (0.2, 0.4, 0.3, 0.1),
    "autumn": (0.2, 0.4, 0.3, 0.1),
    "winter": (0.3, 0.4, 0.2, 0.1),
}

CLOUD_BUCKETS = (
    (0.0, 0.2),  # clear
    (0.2, 0.6),  # partly cloudy
    (0.6, 0.8),  # mostly cloudy
    (0.8, 0.9),  # overcast
)

HOUSEHOLD_TEMPLATES = {
    HouseholdType.STUDIO: {
        "persons_range": "1",
        "daily_avg_kwh": 11.0,
        "base_load_kw": 0.2,
        "peak_spike_kw": 2.5,
    },
    HouseholdType.SMALL_FAMILY: {
        "persons_range": "2-3",
        "daily_avg_kwh": 24.0,
        "base_load_kw": 0.4,
        "peak_spike_kw": 4.5,
    },
    HouseholdType.LARGE_FAMILY: {
        "persons_range": "4+",
        "daily_avg_kwh": 36.0,
        "base_load_kw": 0.8,
        "peak_spike_kw": 7.0,
    },
}

WEALTH_MULTIPLIERS = {
    WealthLevel.LOW: 0.8,
    WealthLevel.MIDDLE: 1.0,
    WealthLevel.HIGH: 1.2,
    WealthLevel.LUXURY: 1.5,
}

MORNING_PEAK_START = 7
MORNING_PEAK_END = 9
EVENING_PEAK_START = 18
EVENING_PEAK_END = 21
RANDOM_SPIKE_PROBABILITY = 0.05
LOAD_NOISE_MIN = -0.1
LOAD_NOISE_MAX = 0.2
MIN_FAILURE_HOURS = 4.0
MAX_FAILURE_HOURS = 72.0
FULL_BATTERY_THRESHOLD = 0.99
LOW_BATTERY_TOLERANCE = 1.01
