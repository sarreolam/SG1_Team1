from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .config import BatteryConfig, GridConfig, InverterFailureConfig, LoadShapeConfig, SolarConfig
from .constants import (
    CLOUD_BUCKETS,
    EVENING_PEAK_END,
    EVENING_PEAK_START,
    LOAD_NOISE_MAX,
    LOAD_NOISE_MIN,
    MAX_FAILURE_HOURS,
    MIN_FAILURE_HOURS,
    MORNING_PEAK_END,
    MORNING_PEAK_START,
    SEASON_WEIGHTS,
)
from .enums import EnergyStrategy


@dataclass
class Battery:
    config: BatteryConfig

    def __post_init__(self) -> None:
        self.soc_kwh = self.config.capacity_kwh * self.config.start_soc_fraction
        self.eta_charge = math.sqrt(self.config.round_trip_efficiency)
        self.eta_discharge = math.sqrt(self.config.round_trip_efficiency)

    @property
    def soc_pct(self) -> float:
        return (self.soc_kwh / self.config.capacity_kwh) * 100.0 if self.config.capacity_kwh else 0.0

    @property
    def usable_discharge_kwh(self) -> float:
        floor_kwh = self.config.capacity_kwh * self.config.min_soc_fraction
        return max(0.0, self.soc_kwh - floor_kwh)

    @property
    def free_capacity_kwh(self) -> float:
        return max(0.0, self.config.capacity_kwh - self.soc_kwh)

    def charge_from_input(self, input_kwh: float) -> tuple[float, float]:
        if input_kwh <= 0.0:
            return 0.0, 0.0
        max_input_kwh = self.free_capacity_kwh / self.eta_charge if self.eta_charge else 0.0
        accepted_input_kwh = min(input_kwh, max_input_kwh)
        stored_kwh = accepted_input_kwh * self.eta_charge
        self.soc_kwh = min(self.config.capacity_kwh, self.soc_kwh + stored_kwh)
        return accepted_input_kwh, stored_kwh

    def discharge_to_supply(self, needed_kwh: float) -> tuple[float, float]:
        if needed_kwh <= 0.0:
            return 0.0, 0.0
        raw_discharge_kwh = min(needed_kwh / self.eta_discharge if self.eta_discharge else 0.0, self.usable_discharge_kwh)
        supplied_kwh = raw_discharge_kwh * self.eta_discharge
        self.soc_kwh = max(0.0, self.soc_kwh - raw_discharge_kwh)
        return raw_discharge_kwh, supplied_kwh


@dataclass(frozen=True)
class WeatherModel:
    season: str
    rng: random.Random

    def sample_daily_cloud_coverage(self) -> float:
        weights = SEASON_WEIGHTS.get(self.season.lower(), SEASON_WEIGHTS["spring"])
        threshold = self.rng.random() * sum(weights)
        cumulative = 0.0
        for (low, high), weight in zip(CLOUD_BUCKETS, weights):
            cumulative += weight
            if threshold <= cumulative:
                return self.rng.uniform(low, high)
        return self.rng.uniform(*CLOUD_BUCKETS[0])


@dataclass(frozen=True)
class SolarArray:
    config: SolarConfig

    def generation_kw(self, env_now_min: int, cloud_coverage: float, inverter_down: bool = False) -> tuple[float, float]:
        if inverter_down:
            return 0.0, 0.0
        t_hours = (env_now_min % (24 * 60)) / 60.0
        sun_angle = (t_hours - 6.0) * (math.pi / 12.0)
        raw_kw = self.config.panel_capacity_kw * max(0.0, math.sin(sun_angle))
        weather_adjusted_kw = raw_kw * (1.0 - cloud_coverage)
        usable_kw = min(weather_adjusted_kw, self.config.inverter_max_output_kw)
        return weather_adjusted_kw, usable_kw


@dataclass(frozen=True)
class LoadModel:
    base_load_kw: float
    peak_spike_kw: float
    shape: LoadShapeConfig
    wealth_multiplier: float
    rng: random.Random

    def sample_kw(self, env_now_min: int) -> float:
        hour = int((env_now_min // 60) % 24)
        load = self.base_load_kw
        if MORNING_PEAK_START <= hour < MORNING_PEAK_END:
            load += self.shape.morning_bump_kw
        if EVENING_PEAK_START <= hour < EVENING_PEAK_END:
            load += self.shape.evening_bump_kw
        if self.rng.random() < self.shape.random_spike_probability:
            load += self.rng.uniform(0.0, self.peak_spike_kw)
        noise_min = self.shape.noise_min_kw if self.shape.noise_min_kw is not None else LOAD_NOISE_MIN
        noise_max = self.shape.noise_max_kw if self.shape.noise_max_kw is not None else LOAD_NOISE_MAX
        load += self.rng.uniform(noise_min, noise_max)
        return max(0.0, load * self.wealth_multiplier * self.shape.variability_multiplier)


@dataclass
class GridConnection:
    config: GridConfig

    def export(self, available_kwh: float, dt_h: float) -> tuple[float, float]:
        if not self.config.allow_export:
            return 0.0, available_kwh
        max_export_kwh = self.config.export_limit_kw * dt_h
        exported_kwh = min(available_kwh, max_export_kwh)
        curtailed_kwh = max(0.0, available_kwh - exported_kwh)
        return exported_kwh, curtailed_kwh


@dataclass
class InverterFailureModel:
    config: InverterFailureConfig
    rng: random.Random
    down_until_min: int = -1

    def is_up(self, env_now_min: int) -> bool:
        return env_now_min >= self.down_until_min

    def maybe_fail_at_day_start(self, env_now_min: int) -> tuple[bool, float]:
        if self.rng.random() >= self.config.daily_failure_probability:
            return False, 0.0
        duration_h = self.rng.gauss(self.config.mean_duration_hours, self.config.mean_duration_hours * 0.5)
        duration_h = max(MIN_FAILURE_HOURS, min(MAX_FAILURE_HOURS, duration_h))
        self.down_until_min = env_now_min + int(duration_h * 60)
        return True, duration_h


class EnergyDispatcher:
    def __init__(self, strategy: EnergyStrategy, grid: GridConnection) -> None:
        self.strategy = strategy
        self.grid = grid

    def resolve_surplus(self, net_kwh: float, dt_h: float, battery: Battery) -> dict:
        result = {
            "battery_charged_kwh": 0.0,
            "grid_export_kwh": 0.0,
            "curtailed_kwh": 0.0,
        }
        if net_kwh <= 0.0:
            return result

        if self.strategy in {EnergyStrategy.LOAD_PRIORITY, EnergyStrategy.CHARGE_PRIORITY}:
            _, stored_kwh = battery.charge_from_input(net_kwh)
            leftover_kwh = max(0.0, net_kwh - (stored_kwh / battery.eta_charge if battery.eta_charge else 0.0))
            exported_kwh, curtailed_kwh = self.grid.export(leftover_kwh, dt_h)
            result.update(
                battery_charged_kwh=stored_kwh,
                grid_export_kwh=exported_kwh,
                curtailed_kwh=curtailed_kwh,
            )
            return result

        if self.strategy == EnergyStrategy.PRODUCE_PRIORITY:
            exported_kwh, leftover_kwh = self.grid.export(net_kwh, dt_h)
            _, stored_kwh = battery.charge_from_input(leftover_kwh)
            curtailed_kwh = max(0.0, leftover_kwh - (stored_kwh / battery.eta_charge if battery.eta_charge else 0.0))
            result.update(
                battery_charged_kwh=stored_kwh,
                grid_export_kwh=exported_kwh,
                curtailed_kwh=curtailed_kwh,
            )
            return result

        raise ValueError(f"Unsupported strategy: {self.strategy}")

@dataclass
class SolarArrayML:
    """
    Reemplaza SolarArray usando el modelo ML entrenado.
    Mantiene la misma firma de generation_kw() para no romper household.py.
    El cloud_coverage se ignora — el ML ya lo tiene baked-in en el weather data.
    """
    config: SolarConfig

    def __post_init__(self) -> None:
        from datetime import datetime
        from ML.components_ml import SolarGeneratorML

        self._ml = SolarGeneratorML(
            panel_capacity_kw=self.config.panel_capacity_kw,
            inverter_max_kw=self.config.inverter_max_output_kw,
        )
        self._sim_start = datetime(2006, 1, 1)

    def generation_kw(
        self,
        env_now_min: int,
        cloud_coverage: float = 0.0,   
        inverter_down: bool = False,
    ) -> tuple[float, float]:
        if inverter_down:
            return 0.0, 0.0

        from datetime import timedelta
        sim_dt = self._sim_start + timedelta(minutes=env_now_min)
        predicted_kw = self._ml.get_power(sim_dt)

        usable_kw = min(predicted_kw, self.config.inverter_max_output_kw)
        return predicted_kw, usable_kw