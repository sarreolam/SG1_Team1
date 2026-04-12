from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import asdict
from statistics import mean
from typing import Dict, List
from pathlib import Path

import simpy

from .components import GridConnection
from .config import ScenarioConfig
from .household import HouseholdSimulator
from .io_utils import create_run_directories, write_csv
from DataPrep.prepare_data import build_dashboard_data


class NeighborhoodSimulation:
    def __init__(self, scenario: ScenarioConfig) -> None:
        self.scenario = scenario
        self.env = simpy.Environment()
        self.rng = random.Random(scenario.simulation.seed)
        self.households = [
            HouseholdSimulator(
                config=household,
                simulation=scenario.simulation,
                grid=GridConnection(scenario.grid),
                inverter_failure=scenario.inverter_failure,
                rng=random.Random(self.rng.randint(0, 10**9)),
            )
            for household in scenario.households
        ]
        self.neighborhood_log: List[Dict[str, object]] = []

    def _aggregate_step(self, env_now_min: int, step_rows: List[dict]) -> None:
        totals = defaultdict(float)
        inverter_up_count = 0
        for row in step_rows:
            inverter_up_count += int(bool(row["inverter_ok"]))
            for key in (
                "solar_kw_raw",
                "solar_kw_used",
                "load_kw",
                "energy_gen_kwh",
                "energy_load_kwh",
                "net_kwh",
                "battery_soc_kwh",
                "battery_charged_kwh",
                "battery_discharged_kwh",
                "grid_import_kwh",
                "grid_export_kwh",
                "curtailed_kwh",
                "unmet_load_kwh",
                "import_cost",
                "export_revenue",
                "net_cost",
            ):
                totals[key] += float(row[key])

        self.neighborhood_log.append(
            {
                "time_min": env_now_min,
                "day": (env_now_min // (24 * 60)) + 1,
                "hour": int((env_now_min // 60) % 24),
                "household_count": len(step_rows),
                "season": self.scenario.simulation.season,
                "strategy": self.scenario.simulation.strategy.value,
                "cloud_coverage_avg": round(mean(float(row["cloud_coverage"]) for row in step_rows), 4),
                "inverter_availability_pct": round((inverter_up_count / len(step_rows)) * 100.0 if step_rows else 0.0, 2),
                **{key: round(value, 6) for key, value in totals.items()},
            }
        )

    def _process(self):
        dt_min = self.scenario.simulation.timestep_minutes
        total_min = self.scenario.simulation.duration_days * 24 * 60
        current_min = 0
        while current_min < total_min:
            step_rows = [house.step(current_min, dt_min).to_dict() for house in self.households]
            self._aggregate_step(current_min, step_rows)
            current_min += dt_min
            yield self.env.timeout(dt_min)

    def run(self) -> dict:
        self.env.process(self._process())
        self.env.run()
        return self._persist_results()

    def _persist_results(self) -> dict:
        run_dir, latest_dir = create_run_directories(self.scenario.name)

        household_rows = [row.to_dict() for house in self.households for row in house.log]
        event_rows = [event.to_dict() for house in self.households for event in house.events]
        summary_rows = self.summary_rows()

        files = {
            "household_timeseries.csv": household_rows,
            "neighborhood_timeseries.csv": self.neighborhood_log,
            "events.csv": event_rows,
            "summary.csv": summary_rows,
        }

        for filename, rows in files.items():
            write_csv(run_dir / filename, rows)
            write_csv(latest_dir / filename, rows)

        dashboard_dir = Path("../Dashboard/data")
        build_dashboard_data(
            source_dir=latest_dir,
            output_dir=dashboard_dir,
        )

        return {
            "run_dir": str(run_dir),
            "household_csv": str(run_dir / "household_timeseries.csv"),
            "neighborhood_csv": str(run_dir / "neighborhood_timeseries.csv"),
            "events_csv": str(run_dir / "events.csv"),
            "summary_csv": str(run_dir / "summary.csv"),
            "summary": self.summary_rows(),
        }

    def summary_rows(self) -> List[dict]:
        rows = []
        for house in self.households:
            house_rows = [row.to_dict() for row in house.log]
            total_generation = sum(float(row["energy_gen_kwh"]) for row in house_rows)
            total_load = sum(float(row["energy_load_kwh"]) for row in house_rows)
            total_import = sum(float(row["grid_import_kwh"]) for row in house_rows)
            total_export = sum(float(row["grid_export_kwh"]) for row in house_rows)
            total_curtailed = sum(float(row["curtailed_kwh"]) for row in house_rows)
            total_cost = sum(float(row["net_cost"]) for row in house_rows)
            avg_soc_pct = mean(float(row["battery_soc_pct"]) for row in house_rows)
            inverter_failures = sum(1 for e in house.events if e.event_type == "INVERTER_FAILURE")
            rows.append(
                {
                    "household_name": house.config.name,
                    "household_type": house.config.household_type.value,
                    "wealth_level": house.config.wealth_level.value,
                    "season": self.scenario.simulation.season,
                    "strategy": self.scenario.simulation.strategy.value,
                    "avg_battery_soc_pct": round(avg_soc_pct, 2),
                    "peak_battery_soc_kwh": round(house.peak_soc_kwh, 4),
                    "min_battery_soc_kwh": round(house.min_soc_kwh, 4),
                    "total_generation_kwh": round(total_generation, 4),
                    "total_load_kwh": round(total_load, 4),
                    "total_grid_import_kwh": round(total_import, 4),
                    "total_grid_export_kwh": round(total_export, 4),
                    "total_curtailed_kwh": round(total_curtailed, 4),
                    "net_cost": round(total_cost, 4),
                    "charge_cycles": house.total_charge_cycles,
                    "discharge_cycles": house.total_discharge_cycles,
                    "inverter_failures": inverter_failures,
                }
            )
        return rows
