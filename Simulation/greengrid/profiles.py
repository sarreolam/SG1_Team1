from __future__ import annotations

from .constants import HOUSEHOLD_TEMPLATES, WEALTH_MULTIPLIERS
from .enums import HouseholdType, WealthLevel


def household_template(household_type: HouseholdType) -> dict:
    return HOUSEHOLD_TEMPLATES[household_type]


def wealth_multiplier(level: WealthLevel) -> float:
    return WEALTH_MULTIPLIERS[level]
