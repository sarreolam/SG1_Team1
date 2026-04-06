from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .enums import EnergyStrategy, HouseholdType, WealthLevel

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


@dataclass(frozen=True)
class BatteryConfig:
    capacity_kwh: float = 13.5
    round_trip_efficiency: float = 0.9
    min_soc_fraction: float = 0.05
    start_soc_fraction: float = 0.5


@dataclass(frozen=True)
class SolarConfig:
    panel_capacity_kw: float = 5.0
    inverter_max_output_kw: float = 4.0


@dataclass(frozen=True)
class GridConfig:
    export_limit_kw: float = 20.0
    import_cost_per_kwh: float = 0.0075
    export_price_per_kwh: float = 0.009
    allow_export: bool = True


@dataclass(frozen=True)
class InverterFailureConfig:
    daily_failure_probability: float = 0.005
    mean_duration_hours: float = 36.0


@dataclass(frozen=True)
class SimulationConfig:
    duration_days: int = 30
    timestep_minutes: int = 60
    season: str = "winter"
    month_length_days: int = 30
    strategy: EnergyStrategy = EnergyStrategy.LOAD_PRIORITY
    seed: Optional[int] = 42


@dataclass(frozen=True)
class LoadShapeConfig:
    morning_bump_kw: float = 0.6
    evening_bump_kw: float = 0.8
    random_spike_probability: float = 0.05
    variability_multiplier: float = 1.0
    noise_min_kw: float = -0.1
    noise_max_kw: float = 0.2


@dataclass(frozen=True)
class HouseholdConfig:
    name: str
    household_type: HouseholdType
    wealth_level: WealthLevel
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    solar: SolarConfig = field(default_factory=SolarConfig)
    load_shape: LoadShapeConfig = field(default_factory=LoadShapeConfig)


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    simulation: SimulationConfig
    grid: GridConfig = field(default_factory=GridConfig)
    inverter_failure: InverterFailureConfig = field(default_factory=InverterFailureConfig)
    households: List[HouseholdConfig] = field(default_factory=list)
