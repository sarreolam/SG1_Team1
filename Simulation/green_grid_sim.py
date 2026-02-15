import os
import csv
import random
import simpy
from solar_model import sample_cloud_coverage, solar_generation_kw
from Configs import config1 as config

# --------- Helper / Parameters (tune via Configs/config.py) ---------
BATTERY_CAP_KWH = getattr(config, "BATTERY_CAPACITY", 5.0)
BATTERY_MIN_SOC_FRAC = 0.05
ROUND_TRIP = getattr(config, "ROUND_TRIP_EFFICIENCY", 0.1)
INVESTER_MAX_KW = getattr(config, "MAX_INVERTER_OUTPUT", 5.0)
TIMESTEP_MIN = getattr(config, "TIMESTEP", 30)
SIM_TOTAL_DAY = getattr(config, "SIMULATION_DURATION", 1440)
CAN_EXPORT = getattr(config, "CAN_EXPORT", True)
GRID_EXPORT_LIMIT_KW = getattr(config, "GRID_EXPORT_LIMIT", 5.0)
INVERTER_FAILURE_FREQ = getattr(config, "INVERTER_FAILURE_FREQUENCY", 0.05)
INVERTER_FAILURE_MIN_H = getattr(config, "INVERTER_FAILURE_DURATION", 7)

OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "log.csv")

# --------- Simple demand model ---------
def sample_load_kw(env_now_min):
    hour = int((env_now_min // 60) % 24)
    load = getattr(config, "BASE_LOAD", 0.9)
    
    # morning bump
    if 7 <= hour < 9:
        load += 0.6
    # evening peak
    if 18 <= hour < 21:
        load += 0.8
    # random spike occasionally
    if random.random() < 0.05:
        load += random.uniform(0.0, getattr(config, "PEAK_LOAD", 3.5))
    load += random.uniform(-0.1, 0.2)
    return max(0.0, load)

# ---- Model class ---------
class SimpleGreenGrid:
    def __init__(self, env, start_soc_frac=0.5, season=None):
        self.env = env
        self.battery_soc = BATTERY_CAP_KWH * start_soc_frac
        self.season = season or getattr(config, "SEASON", "summer")
        self.cloud_today = sample_cloud_coverage(self.season)
        self.inverter_down_until = -1
        self.log = []

    def inverter_ok(self):
        return self.env.now >= self.inverter_down_until
    
    def maybe_inverter_failure(self):
        # call once per day at midnight
        if random.random() < INVERTER_FAILURE_FREQ:
            # failure duration sample (hours)
            dur_h = max(1.0, random.gauss(INVERTER_FAILURE_MIN_H, INVERTER_FAILURE_MIN_H * 0.5))
            self.inverter_down_until = self.env.now + int(dur_h * 60)
            return True, dur_h
        return False, 0.0

    def step(self, dt_min):
        """Single timestep energy balance. dt_min in minutes."""
        dt_h = dt_min / 60.0
        t = int(self.env.now)
        hour = int((t // 60) % 24)

        # daily update at midnight
        if t % (24 * 60) == 0:
            self.cloud_today = sample_cloud_coverage(self.season)
            self.maybe_inverter_failure()

        # measure
        solar_kw = solar_generation_kw(int(self.env.now), self.cloud_today, inverter_down=(not self.inverter_ok()))
        load_kw = sample_load_kw(int(self.env.now))

        usable_solar_kw = min(solar_kw, INVESTER_MAX_KW) if self.inverter_ok() else 0.0
        energy_gen_kwh = usable_solar_kw * dt_h
        energy_load_kwh = load_kw * dt_h

        grid_import_kwh = 0.0
        grid_export_kwh = 0.0

        net_kwh = energy_gen_kwh - energy_load_kwh

        battery_before = self.battery_soc

        if net_kwh > 0:
            # charge battery first
            space_kwh = BATTERY_CAP_KWH - self.battery_soc
            # charge energy taken from net before efficiency loss
            charge_input = min(net_kwh, space_kwh)
            # only part sorted due to efficiency loss
            stored_kwh = charge_input * ROUND_TRIP
            self.battery_soc += stored_kwh
            leftover_kwh = net_kwh - charge_input
            if CAN_EXPORT and leftover_kwh > 1e-9:
                # export limited by GRID_EXPORT_LIMIT_KW
                export_kw_possible = min(leftover_kwh / dt_h if dt_h > 0 else 0.0, GRID_EXPORT_LIMIT_KW)
                grid_export_kwh = export_kw_possible * dt_h
        else:
            need = -net_kwh
            available_kwh = max(0.0, self.battery_soc - BATTERY_CAP_KWH * BATTERY_MIN_SOC_FRAC)
            # discharge energy before efficiency loss
            # to supply energy_load, we need to withdraw discharge = need / efficiency
            if ROUND_TRIP > 0:
                discharge_needed_kwh = min(need / ROUND_TRIP, available_kwh)
                supplied_kwh = discharge_needed_kwh * ROUND_TRIP
            else:
                discharge_needed_kwh = 0.0
                supplied_kwh = 0.0
            
            self.battery_soc -= discharge_needed_kwh
            remaining_need_kwh = need - supplied_kwh
            if remaining_need_kwh > 1e-9:
                grid_import_kwh = remaining_need_kwh
        
        # clamp battery
        self.battery_soc = min(max(0.0, self.battery_soc), BATTERY_CAP_KWH)

        # If net was negative (we should discharge) but SoC increased, flag it
        if net_kwh < -1e-9 and self.battery_soc > battery_before + 1e-6:
            print("WARNING: SoC increased despite deficit at time", self.env.now,
                  "net_kwh", net_kwh, "batt_before", battery_before, "batt_after", self.battery_soc)

        self.log.append({
            "time_min": int(self.env.now),
            "hour": hour,
            "solar_kw": round(solar_kw, 4),
            "load_kw": round(load_kw, 4),
            "energy_gen_kwh": round(energy_gen_kwh, 6),
            "energy_load_kwh": round(energy_load_kwh, 6),
            "battery_soc_kwh": round(self.battery_soc, 6),
            "grid_import_kwh": round(grid_import_kwh, 6),
            "grid_export_kwh": round(grid_export_kwh, 6),
            "inverter_ok": self.inverter_ok(),
            "cloud": round(self.cloud_today, 4)
        })

    def run(self, dt_min, total_min):
        steps = int(total_min // dt_min)
        for _ in range(steps):
            self.step(dt_min)
            yield self.env.timeout(dt_min)

# ---- RUN HELPER ----
def run_simulation(days=None):
    dt = TIMESTEP_MIN
    total_min = SIM_TOTAL_DAY * 24 * 60 if days is None else days * 24 * 60

    env = simpy.Environment()
    plant = SimpleGreenGrid(env, start_soc_frac=0.5)
    env.process(plant.run(dt, total_min))
    env.run()

    # save log to CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as f:
        fieldnames = list(plant.log[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in plant.log:
            writer.writerow(r)
    
    print("Simulation finished. CSV: ", OUTPUT_CSV)


if __name__ == "__main__":
    run_simulation(days=1)

