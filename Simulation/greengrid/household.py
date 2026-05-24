from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

from .components import Battery, EnergyDispatcher, GridConnection, InverterFailureModel, LoadModel, SolarArray, SolarArrayML, WeatherModel
from .config import HouseholdConfig, InverterFailureConfig, SimulationConfig
from .models import EventRecord, StepResult
from .profiles import household_template, wealth_multiplier


@dataclass
class HouseholdSimulator:
    config: HouseholdConfig
    simulation: SimulationConfig
    grid: GridConnection
    inverter_failure: InverterFailureConfig
    rng: random.Random
    battery: Battery = field(init=False)
    solar: SolarArray = field(init=False)
    weather: WeatherModel = field(init=False)
    inverter: InverterFailureModel = field(init=False)
    dispatcher: EnergyDispatcher = field(init=False)
    log: List[StepResult] = field(default_factory=list)
    events: List[EventRecord] = field(default_factory=list)
    current_cloud_coverage: float = field(default=0.0)
    peak_soc_kwh: float = field(default=0.0)
    min_soc_kwh: float = field(default=0.0)
    total_charge_cycles: int = field(default=0)
    total_discharge_cycles: int = field(default=0)
    _was_charging: bool = field(default=False)
    _was_discharging: bool = field(default=False)

    def __post_init__(self) -> None:
        template = household_template(self.config.household_type)
        self.battery = Battery(self.config.battery)
        self.solar = SolarArrayML(self.config.solar)
        self.weather = WeatherModel(self.simulation.season, self.rng)
        self.inverter = InverterFailureModel(self.inverter_failure, self.rng)
        self.dispatcher = EnergyDispatcher(self.simulation.strategy, self.grid)
        self.load_model = LoadModel(
            base_load_kw=template["base_load_kw"],
            peak_spike_kw=template["peak_spike_kw"],
            shape=self.config.load_shape,
            wealth_multiplier=wealth_multiplier(self.config.wealth_level),
            rng=self.rng,
        )
        self.current_cloud_coverage = self.weather.sample_daily_cloud_coverage()
        self.peak_soc_kwh = self.battery.soc_kwh
        self.min_soc_kwh = self.battery.soc_kwh
        self._event(0, "SIMULATION_START", f"strategy={self.simulation.strategy.value}, season={self.simulation.season}")

    def _event(self, env_now_min: int, event_type: str, description: str) -> None:
        self.events.append(
            EventRecord(
                time_min=env_now_min,
                day=(env_now_min // (24 * 60)) + 1,
                hour=int((env_now_min // 60) % 24),
                household_name=self.config.name,
                event_type=event_type,
                description=description,
            )
        )

    def _track_cycles(self, env_now_min: int, charging: bool, discharging: bool) -> None:
        if charging and not self._was_charging:
            self.total_charge_cycles += 1
            self._event(env_now_min, "BATTERY_CHARGE_START", f"cycle={self.total_charge_cycles}")
        if discharging and not self._was_discharging:
            self.total_discharge_cycles += 1
            self._event(env_now_min, "BATTERY_DISCHARGE_START", f"cycle={self.total_discharge_cycles}")
        self._was_charging = charging
        self._was_discharging = discharging

    def _day_setup(self, env_now_min: int) -> None:
        self.current_cloud_coverage = self.weather.sample_daily_cloud_coverage()
        self._event(env_now_min, "DAILY_UPDATE", f"cloud_coverage={self.current_cloud_coverage:.3f}")
        failed, duration_h = self.inverter.maybe_fail_at_day_start(env_now_min)
        if failed:
            self._event(env_now_min, "INVERTER_FAILURE", f"duration_hours={duration_h:.2f}")

    def step(self, env_now_min: int, dt_min: int) -> StepResult:
        if env_now_min % (24 * 60) == 0:
            self._day_setup(env_now_min)

        dt_h = dt_min / 60.0
        inverter_ok = self.inverter.is_up(env_now_min)
        solar_kw_raw, solar_kw_used = self.solar.generation_kw(
            env_now_min,
            cloud_coverage=self.current_cloud_coverage,
            inverter_down=not inverter_ok,
        )
        load_kw = self.load_model.sample_kw(env_now_min)

        energy_gen_kwh = solar_kw_used * dt_h
        energy_load_kwh = load_kw * dt_h
        net_kwh = energy_gen_kwh - energy_load_kwh

        battery_charged_kwh = 0.0
        battery_discharged_kwh = 0.0
        grid_import_kwh = 0.0
        grid_export_kwh = 0.0
        curtailed_kwh = 0.0
        unmet_load_kwh = 0.0

        if net_kwh >= 0.0:
            resolved = self.dispatcher.resolve_surplus(net_kwh, dt_h, self.battery)
            battery_charged_kwh = resolved["battery_charged_kwh"]
            grid_export_kwh = resolved["grid_export_kwh"]
            curtailed_kwh = resolved["curtailed_kwh"]
            if curtailed_kwh > 1e-9:
                self._event(env_now_min, "SOLAR_CURTAILMENT", f"kwh={curtailed_kwh:.4f}")
        else:
            need_kwh = -net_kwh
            battery_discharged_kwh, supplied_kwh = self.battery.discharge_to_supply(need_kwh)
            remaining_need_kwh = max(0.0, need_kwh - supplied_kwh)
            grid_import_kwh = remaining_need_kwh

        self.peak_soc_kwh = max(self.peak_soc_kwh, self.battery.soc_kwh)
        self.min_soc_kwh = min(self.min_soc_kwh, self.battery.soc_kwh)
        self._track_cycles(env_now_min, battery_charged_kwh > 1e-9, battery_discharged_kwh > 1e-9)

        import_cost = grid_import_kwh * self.grid.config.import_cost_per_kwh
        export_revenue = grid_export_kwh * self.grid.config.export_price_per_kwh
        net_cost = import_cost - export_revenue

        if not inverter_ok and env_now_min + dt_min >= self.inverter.down_until_min:
            self._event(env_now_min, "INVERTER_RECOVERY", "recovered")

        result = StepResult(
            time_min=env_now_min,
            day=(env_now_min // (24 * 60)) + 1,
            hour=int((env_now_min // 60) % 24),
            household_name=self.config.name,
            household_type=self.config.household_type.value,
            wealth_level=self.config.wealth_level.value,
            season=self.simulation.season,
            strategy=self.simulation.strategy.value,
            cloud_coverage=round(self.current_cloud_coverage, 4),
            inverter_ok=inverter_ok,
            solar_kw_raw=round(solar_kw_raw, 4),
            solar_kw_used=round(solar_kw_used, 4),
            load_kw=round(load_kw, 4),
            energy_gen_kwh=round(energy_gen_kwh, 6),
            energy_load_kwh=round(energy_load_kwh, 6),
            net_kwh=round(net_kwh, 6),
            battery_soc_kwh=round(self.battery.soc_kwh, 6),
            battery_soc_pct=round(self.battery.soc_pct, 2),
            battery_charged_kwh=round(battery_charged_kwh, 6),
            battery_discharged_kwh=round(battery_discharged_kwh, 6),
            grid_import_kwh=round(grid_import_kwh, 6),
            grid_export_kwh=round(grid_export_kwh, 6),
            curtailed_kwh=round(curtailed_kwh, 6),
            unmet_load_kwh=round(unmet_load_kwh, 6),
            import_cost=round(import_cost, 6),
            export_revenue=round(export_revenue, 6),
            net_cost=round(net_cost, 6),
        )
        self.log.append(result)
        return result
