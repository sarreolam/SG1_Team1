from __future__ import annotations

from enum import Enum


class EnergyStrategy(str, Enum):
    LOAD_PRIORITY = "load_priority"
    CHARGE_PRIORITY = "charge_priority"
    PRODUCE_PRIORITY = "produce_priority"


class HouseholdType(str, Enum):
    STUDIO = "studio"
    SMALL_FAMILY = "small_family"
    LARGE_FAMILY = "large_family"


class WealthLevel(str, Enum):
    LOW = "low"
    MIDDLE = "middle"
    HIGH = "high"
    LUXURY = "luxury"
