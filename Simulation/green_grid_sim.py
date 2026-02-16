import os
import csv
import random
import simpy
import math
from solar_model import sample_cloud_coverage, solar_generation_kw
from Configs import config1 as config

# --------- Helper / Parameters (tune via Configs/config.py) ---------
BATTERY_CAP_KWH = getattr(config, "BATTERY_CAPACITY", 5.0)
ROUND_TRIP = getattr(config, "ROUND_TRIP_EFFICIENCY", 0.9)
BATTERY_MIN_SOC_FRAC = getattr(config, "BATTERY_MIN_SOC_FRACTION", 0.05)

INVERTER_MAX_KW = getattr(config, "MAX_INVERTER_OUTPUT", 4.0)
TIMESTEP_MIN = getattr(config, "TIMESTEP", 30)
SIM_TOTAL_DAY = getattr(config, "SIMULATION_DURATION", 1)
MONTH_LENGTH_DAYS = getattr(config, "MONTH_LENGTH_DAYS", 30)

GRID_EXPORT_LIMIT= getattr(config, "GRID_EXPORT_LIMIT", 20.0)
IMPORT_COST = getattr(config, "IMPORTED_ENERGY_COST", 0.0075)
EXPORT_COST = getattr(config, "EXPORTED_ENERGY_COST", 0.009)


INVERTER_FAILURE_FREQ = getattr(config, "INVERTER_FAILURE_FREQUENCY", 0.05)
INVERTER_FAILURE_MIN_H = getattr(config, "INVERTER_FAILURE_DURATION", 7)
MANAGEMENT_STRATEGY = getattr(config, "MANAGEMENT_STRATEGY", "load_priority")


OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "log.csv")
EVENTS_CSV = os.path.join(OUTPUT_DIR, "events.csv")

ETA_CHARGE = math.sqrt(ROUND_TRIP)
ETA_DISCHARGE = math.sqrt(ROUND_TRIP)


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
    def __init__(self, env, start_soc_frac=0.5, season=None, strategy=None):
        self.env = env
        self.battery_soc = BATTERY_CAP_KWH * start_soc_frac
        self.season = season or getattr(config, "SEASON", "summer")
        self.cloud_today = sample_cloud_coverage(self.season)
        self.inverter_down_until = -1
        self.strategy = strategy or MANAGEMENT_STRATEGY
        
        self.log = []
        self.events = []

        self.total_charge_cycles = 0
        self.total_discharge_cycles = 0
        self.last_was_charging = False
        self.last_was_discharging = False
        self.peak_battery_soc = start_soc_frac * BATTERY_CAP_KWH
        self.min_battery_soc = start_soc_frac * BATTERY_CAP_KWH

        self.prev_inverter_ok = True

        self.month_exported_kwh = 0.0
        self.month_index = 0


        # New: track curtailment
        self.total_curtailed_kwh = 0.0

        export_mode = f"Limited to {GRID_EXPORT_LIMIT} kW" 
        self._log_event("SIMULATION START", 
                       f"Strategy: {self.strategy}, Season: {self.season}, Export: {export_mode}")

    def inverter_ok(self):
        return self.env.now >= self.inverter_down_until
    
    def maybe_inverter_failure(self):
        # call once per day at midnight
        if random.random() < INVERTER_FAILURE_FREQ:
            # failure duration sample (hours)
            dur_h = random.gauss(INVERTER_FAILURE_MIN_H, INVERTER_FAILURE_MIN_H * 0.5)
            dur_h = max(4.0, min(72.0, dur_h))
            self.inverter_down_until = self.env.now + int(dur_h * 60)
            self._log_event("INVERTER FAILURE", f"Duration: {dur_h:.2f} hours, until minute {self.inverter_down_until}")
            return True, dur_h
        return False, 0.0
    
    def _log_event(self, event_type, description):
        self.events.append({
            "time_min": int(self.env.now),
            "hour": int((self.env.now // 60) % 24),
            "event_type": event_type,
            "description": description
        })

    def _track_battery_cycles(self, is_charging, is_discharging):
        if is_charging and not self.last_was_charging:
            self.total_charge_cycles += 1
            self._log_event("BATTERY CHARGE START", f"Cycle #{self.total_charge_cycles}")

        if is_discharging and not self.last_was_discharging:
            self.total_discharge_cycles += 1
            self._log_event("BATTERY DISCHARGE START", f"Cycle #{self.total_discharge_cycles}")

        self.last_was_charging = is_charging
        self.last_was_discharging = is_discharging

    def _apply_strategy_surplus(self, net_kwh, dt_h):
        """
        Handle surplus energy based on strategy and grid constraints.
        Returns: (grid_export_kwh, battery_charged_kwh, curtailed_kwh)
        """
        space_kwh = BATTERY_CAP_KWH - self.battery_soc
        grid_export_kwh = 0.0
        battery_charged_kwh = 0.0
        curtailed_kwh = 0.0
        
        # Check if export is allowed

        monthly_cap = GRID_EXPORT_LIMIT
        remaining_monthly_kwh = max(0.0, monthly_cap - self.month_exported_kwh)

        can_export_to_grid = remaining_monthly_kwh > 0.0

        if self.strategy == "load_priority":
            # Default: charge battery first, then export
            charge_input = min(net_kwh, space_kwh / ETA_CHARGE)
            stored_kwh = charge_input * ETA_CHARGE

            self.battery_soc += stored_kwh
            battery_charged_kwh = stored_kwh

            leftover_kwh = net_kwh - charge_input
            if leftover_kwh > 1e-9:
                if can_export_to_grid:
                    export_kw_possible = min(leftover_kwh / dt_h if dt_h > 0 else 0.0, GRID_EXPORT_LIMIT)
                    export_kwh_possible = export_kw_possible * dt_h
                    export_kwh = min(export_kwh_possible, remaining_monthly_kwh)
                    grid_export_kwh = export_kwh
                    self.month_exported_kwh += grid_export_kwh
                    curtailed_kwh = leftover_kwh - grid_export_kwh
                else:
                    # Cannot export - must curtail
                    curtailed_kwh = leftover_kwh
                    if curtailed_kwh > 0.01:  # Only log significant curtailment
                        self._log_event("SOLAR CURTAILMENT", 
                                      f"Battery full, cannot export: {curtailed_kwh:.4f} kWh wasted")

        elif self.strategy == "charge_priority":
            # Charge battery as much as possible, then export leftovers
            charge_input = min(net_kwh, space_kwh / ETA_CHARGE)
            stored_kwh = charge_input * ETA_CHARGE

            self.battery_soc += stored_kwh
            battery_charged_kwh = stored_kwh

            leftover_kwh = net_kwh - charge_input
            if leftover_kwh > 1e-9 and self.battery_soc >= BATTERY_CAP_KWH * 0.99:
                if can_export_to_grid:
                    export_kw_possible = min(leftover_kwh / dt_h if dt_h > 0 else 0.0, GRID_EXPORT_LIMIT)
                    export_kwh_possible = export_kw_possible * dt_h
                    export_kwh = min(export_kwh_possible, remaining_monthly_kwh)
                    grid_export_kwh = export_kwh
                    self.month_exported_kwh += grid_export_kwh
                    curtailed_kwh = leftover_kwh - grid_export_kwh
                else:
                    curtailed_kwh = leftover_kwh
                    if curtailed_kwh > 0.01:
                        self._log_event("SOLAR CURTAILMENT", 
                                      f"Battery full, cannot export: {curtailed_kwh:.4f} kWh wasted")
        
        elif self.strategy == "produce_priority":
            # Export first, then charge battery with leftovers
            max_export_kwh = GRID_EXPORT_LIMIT * dt_h

            if can_export_to_grid:
                if net_kwh > max_export_kwh:
                    grid_export_kwh = max_export_kwh
                    remaining = net_kwh - max_export_kwh
                    charge_input = min(remaining, space_kwh / ETA_CHARGE)
                    stored_kwh = charge_input * ETA_CHARGE
                    self.month_exported_kwh += grid_export_kwh

                    self.battery_soc += stored_kwh
                    battery_charged_kwh = stored_kwh
                    curtailed_kwh = remaining - charge_input
                else:
                    grid_export_kwh = net_kwh
                    self.month_exported_kwh += grid_export_kwh
            else:
                # Cannot export - charge battery instead
                charge_input = min(net_kwh, space_kwh / ETA_CHARGE)
                stored_kwh = charge_input * ETA_CHARGE

                self.battery_soc += stored_kwh
                battery_charged_kwh = stored_kwh
                curtailed_kwh = net_kwh - charge_input
                if curtailed_kwh > 0.01:
                    self._log_event("SOLAR CURTAILMENT", 
                                  f"Cannot export, battery full: {curtailed_kwh:.4f} kWh wasted")

        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        return grid_export_kwh, battery_charged_kwh, curtailed_kwh
            

    def step(self, dt_min):
        """Single timestep energy balance. dt_min in minutes."""
        dt_h = dt_min / 60.0
        t = int(self.env.now)
        hour = int((t // 60) % 24)

        was_ok = self.prev_inverter_ok
        now_ok = self.inverter_ok()

        # daily update at midnight
        if t % (24 * 60) == 0:
            self.cloud_today = sample_cloud_coverage(self.season)
            self._log_event("DAILY UPDATE", f"New cloud coverage: {self.cloud_today:.2f}")
            self.maybe_inverter_failure()

            day_index = t // (24 * 60)
            if day_index > 0 and day_index % MONTH_LENGTH_DAYS == 0:
                self.month_exported_kwh = 0.0
                self.month_index += 1
                self._log_event("MONTH RESET", f"Month #{self.month_index} export quota reset")


        if (not was_ok) and now_ok:
            self._log_event("INVERTER RECOVERY", "Inverter is back online")

        # measure
        solar_kw = solar_generation_kw(int(self.env.now), self.cloud_today, inverter_down=(not self.inverter_ok()))
        load_kw = sample_load_kw(int(self.env.now))

        usable_solar_kw = min(solar_kw, INVERTER_MAX_KW) if self.inverter_ok() else 0.0
        energy_gen_kwh = usable_solar_kw * dt_h
        energy_load_kwh = load_kw * dt_h

        # metrics tracking
        grid_import_kwh = 0.0
        grid_export_kwh = 0.0
        unmet_load_kwh = 0.0
        battery_charged_kwh = 0.0
        battery_discharged_kwh = 0.0
        curtailed_kwh = 0.0

        net_kwh = energy_gen_kwh - energy_load_kwh
        battery_before = self.battery_soc

        if net_kwh > 0:
            grid_export_kwh, battery_charged_kwh, curtailed_kwh = self._apply_strategy_surplus(net_kwh, dt_h)
            self.total_curtailed_kwh += curtailed_kwh
        else:
            need = -net_kwh
            available_kwh = max(0.0, self.battery_soc - BATTERY_CAP_KWH * BATTERY_MIN_SOC_FRAC)
            # discharge energy before efficiency loss
            # to supply energy_load, we need to withdraw discharge = need / efficiency
            if ROUND_TRIP > 0:
                discharge_needed_kwh = min(need / ETA_DISCHARGE, available_kwh)
                supplied_kwh = discharge_needed_kwh * ETA_DISCHARGE

            else:
                discharge_needed_kwh = 0.0
                supplied_kwh = 0.0
            
            self.battery_soc -= discharge_needed_kwh
            battery_discharged_kwh = discharge_needed_kwh

            
            remaining_need_kwh = need - supplied_kwh
            unmet_load_kwh = remaining_need_kwh - grid_import_kwh

            if remaining_need_kwh > 1e-9:
                grid_import_kwh = remaining_need_kwh
                unmet_load_kwh = 0.0

            if unmet_load_kwh > 1e-9:
                self._log_event("UNMET LOAD", f"{unmet_load_kwh:.4f} kWh unmet")

        
        # Limits and validations
        # clamp battery
        self.battery_soc = min(max(0.0, self.battery_soc), BATTERY_CAP_KWH)

        if self.battery_soc > self.peak_battery_soc:
            self.peak_battery_soc = self.battery_soc
            if self.battery_soc >= BATTERY_CAP_KWH * 0.99:
                self._log_event("BATTERY FULL", f"SoC: {self.battery_soc:.4f} kWh")

        if self.battery_soc < self.min_battery_soc:
            self.min_battery_soc = self.battery_soc
            if self.battery_soc <= BATTERY_CAP_KWH * BATTERY_MIN_SOC_FRAC * 1.01:
                self._log_event("BATTERY LOW", f"SoC: {self.battery_soc:.4f} kWh")

        is_charging = battery_charged_kwh > 1e-9
        is_discharging = battery_discharged_kwh > 1e-9
        self._track_battery_cycles(is_charging, is_discharging)

        # If net was negative (we should discharge) but SoC increased, flag it
        if net_kwh < -1e-9 and self.battery_soc > battery_before + 1e-6:
            self._log_event("WARNING", f"SoC increased during deficit. net={net_kwh:.6f}, before={battery_before:.6f}, after={self.battery_soc:.6f}")
        self.prev_inverter_ok = now_ok

        import_cost = grid_import_kwh * IMPORT_COST
        export_revenue = grid_export_kwh * EXPORT_COST
        net_cost = import_cost - export_revenue


        
        self.log.append({
            "time_min": int(self.env.now),
            "hour": hour,
            "solar_kw": round(solar_kw, 4),
            "load_kw": round(load_kw, 4),
            "energy_gen_kwh": round(energy_gen_kwh, 6),
            "energy_load_kwh": round(energy_load_kwh, 6),
            "net_kwh": round(net_kwh, 6),
            "battery_soc_kwh": round(self.battery_soc, 6),
            "battery_soc_pct": round(self.battery_soc / BATTERY_CAP_KWH * 100, 2),
            "battery_charged_kwh": round(battery_charged_kwh, 6),
            "battery_discharged_kwh": round(battery_discharged_kwh, 6),
            "grid_import_kwh": round(grid_import_kwh, 6),
            "grid_export_kwh": round(grid_export_kwh, 6),
            "curtailed_kwh": round(curtailed_kwh, 6), 
            "unmet_load_kwh": round(unmet_load_kwh, 6),
            "inverter_ok": self.inverter_ok(),
            "cloud": round(self.cloud_today, 4),
            "strategy": self.strategy,
            "import_cost": round(import_cost, 6),
            "export_revenue": round(export_revenue, 6),
            "net_cost": round(net_cost, 6),
            "month_exported_kwh": round(self.month_exported_kwh, 6)
        })

    def run(self, dt_min, total_min):
        steps = int(total_min // dt_min)
        for _ in range(steps):
            self.step(dt_min)
            yield self.env.timeout(dt_min)

        self._log_event("SIMULATION END", 
                        f"Total charge cycles: {self.total_charge_cycles}, "
                        f"Total discharge cycles: {self.total_discharge_cycles}, "
                        f"Peak SoC: {self.peak_battery_soc:.4f} kWh, "
                        f"Min SoC: {self.min_battery_soc:.4f} kWh, "
                        f"Total curtailed: {self.total_curtailed_kwh:.4f} kWh")

# ---- RUN HELPER ----
def run_simulation(days=None):
    dt = TIMESTEP_MIN
    
    if SIM_TOTAL_DAY is not None:
        total_min = SIM_TOTAL_DAY * 24 * 60
        print(f"Simulating {SIM_TOTAL_DAY} day(s) = {total_min} minutes")
    elif days is not None:
        total_min = days * 24 * 60
        print(f"Simulating {days} day(s) = {total_min} minutes")
    
    strat = MANAGEMENT_STRATEGY or "load_priority"
    print(f"Strategy: {strat}")
    print(f"Timestep: {dt} minutes")
    print(f"Total timesteps: {total_min // dt}")
    print(f"Battery capacity: {BATTERY_CAP_KWH} kWh")
    print(f"Round-trip efficiency: {ROUND_TRIP*100}%")
    print(f"Season: {getattr(config, 'SEASON', 'summer')}")
    print(f"Export mode: {GRID_EXPORT_LIMIT} kW limit")
    print("-" * 70)

    env = simpy.Environment()
    plant = SimpleGreenGrid(env, start_soc_frac=0.5, strategy=strat)
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

    with open(EVENTS_CSV, "w", newline="") as f:
        if plant.events:
            fieldnames = list(plant.events[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in plant.events:
                writer.writerow(e)

    # ========== CALCULATE MONTHLY TOTALS ==========
    total_solar_gen = sum(r['energy_gen_kwh'] for r in plant.log)
    total_load = sum(r['energy_load_kwh'] for r in plant.log)
    total_import = sum(r['grid_import_kwh'] for r in plant.log)
    total_export = sum(r['grid_export_kwh'] for r in plant.log)
    total_curtailed = sum(r['curtailed_kwh'] for r in plant.log)
    total_import_cost = sum(r['import_cost'] for r in plant.log)
    total_export_revenue = sum(r['export_revenue'] for r in plant.log)
    net_balance = total_export_revenue - total_import_cost
    
    # Calculate performance indicators
    solar_used = total_solar_gen - total_export
    self_sufficiency_pct = (solar_used / total_load * 100) if total_load > 0 else 0
    grid_dependency_pct = (total_import / total_load * 100) if total_load > 0 else 0

    print(f"Simulation completed")
    print(f"Main log: {OUTPUT_CSV} ({len(plant.log)} records)")
    print(f"Events: {EVENTS_CSV} ({len(plant.events)} events)")
    print("-" * 70)
    
    print(f"\nENERGY SUMMARY ({SIM_TOTAL_DAY} days):")
    print("=" * 70)
    print(f"Total solar generated:        {total_solar_gen:>10.2f} kWh")
    print(f"Total consumed:               {total_load:>10.2f} kWh")
    print(f"Total grid import:            {total_import:>10.2f} kWh")
    print(f"Total grid export:            {total_export:>10.2f} kWh")
    print(f"Total curtailed (wasted):     {total_curtailed:>10.2f} kWh ({total_curtailed/total_solar_gen*100:.1f}% of generation)")
    
    print(f"\nECONOMIC BALANCE:")
    print("=" * 70)
    print(f"Cost of imported energy:      ${total_import_cost:>10.4f}")
    print(f"Revenue from exported energy: ${total_export_revenue:>10.4f}")
    print(f"Net balance:                  ${net_balance:>10.4f} {'(Loss)' if net_balance < 0 else '(Profit)'}")
    
    print(f"\nPERFORMANCE INDICATORS:")
    print("=" * 70)
    print(f"Self-sufficiency:             {self_sufficiency_pct:>10.1f}%")
    print(f"Grid dependency:              {grid_dependency_pct:>10.1f}%")
    print(f"Solar utilization efficiency: {(solar_used/total_solar_gen*100) if total_solar_gen > 0 else 0:>10.1f}%")
    
    print(f"\nBATTERY:")
    print("=" * 70)
    print(f"Charge cycles:                {plant.total_charge_cycles:>10}")
    print(f"Discharge cycles:             {plant.total_discharge_cycles:>10}")
    print(f"Peak SoC:                     {plant.peak_battery_soc:>10.4f} kWh ({plant.peak_battery_soc/BATTERY_CAP_KWH*100:.1f}%)")
    print(f"Minimum SoC:                  {plant.min_battery_soc:>10.4f} kWh ({plant.min_battery_soc/BATTERY_CAP_KWH*100:.1f}%)")
    
    print("\n" + "=" * 70)
    print(f"Files saved: {OUTPUT_CSV}, {EVENTS_CSV}")
    print("=" * 70)


if __name__ == "__main__":
    run_simulation()