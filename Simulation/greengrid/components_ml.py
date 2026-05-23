"""
components_ml.py
----------------
Drop-in ML-powered solar generator for the Green Grid simulator.
Replaces the hard-coded math.sin() solar generation with a trained
Linear Regression model that uses real weather data.

Supports all 7 California cities — set CITY below to match your team.

HOW TO USE IN household.py:
----------------------------
1. Import at the top:
       from greengrid.components_ml import SolarGeneratorML

2. Add to HouseholdSimulator.__init__():
       self.solar_ml = SolarGeneratorML(
           panel_capacity_kw = config.solar.panel_capacity_kw,
           inverter_max_kw   = config.solar.inverter_max_output_kw
       )

3. Replace _solar_output_kw():
       def _solar_output_kw(self, sim_datetime) -> float:
           return self.solar_ml.get_power(sim_datetime)

4. In your SimPy loop, pass the current datetime:
       from datetime import datetime, timedelta
       start = datetime(2006, 1, 1)
       current_dt = start + timedelta(hours=env.now)
       solar_kw = self._solar_output_kw(current_dt)
"""

import os, sys, json
import pandas as pd
import numpy as np

# ── CONFIGURE YOUR CITY HERE ─────────────────────────────────────────────────
CITY = 'Squaw_Valley'

# ── City metadata ─────────────────────────────────────────────────────────────
CITY_CONFIG = {
    'Squaw_Valley':    {'prefix': '189871', 'farm_mw': 112.9}
}

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..', '..')
DATASETS_DIR = os.path.join(PROJECT_ROOT, 'Datasets')
ML_DIR       = os.path.join(SCRIPT_DIR, '..', 'ml')
MODEL_PATH   = os.path.join(ML_DIR, 'model_weights.json')

sys.path.insert(0, ML_DIR)
from solar_model import SolarModel


class SolarGeneratorML:
    """
    ML-powered solar output calculator.
    Loaded once per simulation run; shared across all household instances.

    Parameters
    ----------
    panel_capacity_kw : float
        Household panel capacity in kW (from SolarConfig).
    inverter_max_kw : float
        Inverter output cap in kW (from SolarConfig).
    city : str
        City name key (default: module-level CITY variable).
    """

    # Class-level cache so model and weather load only once
    _model        = None
    _weather_data = None
    _farm_mw      = None

    def __init__(self, panel_capacity_kw: float = 5.0,
                 inverter_max_kw: float = 4.0,
                 city: str = CITY):

        self.panel_capacity_kw = panel_capacity_kw
        self.inverter_max_kw   = inverter_max_kw

        if SolarGeneratorML._model is None:
            SolarGeneratorML._model = SolarModel().load(MODEL_PATH)
            print(f"[SolarGeneratorML] Model loaded ({city})")

        if SolarGeneratorML._weather_data is None:
            cfg = CITY_CONFIG[city]
            SolarGeneratorML._farm_mw = cfg['farm_mw']

            # Find the city's dataset folder
            city_folder = next(
                (d for d in os.listdir(DATASETS_DIR)
                 if city.split('_')[0] in d or cfg['prefix'] in d),
                None
            )
            if city_folder is None:
                raise FileNotFoundError(
                    f"Dataset folder for '{city}' not found in {DATASETS_DIR}"
                )

            weather_csv = os.path.join(DATASETS_DIR, city_folder, 'merged_clean.csv')
            if not os.path.exists(weather_csv):
                raise FileNotFoundError(
                    f"merged_clean.csv missing. Run: python prepare_ml_data.py --city {city}"
                )

            SolarGeneratorML._weather_data = pd.read_csv(
                weather_csv, parse_dates=['dt']
            ).set_index('dt')
            print(f"[SolarGeneratorML] Weather loaded: "
                  f"{len(SolarGeneratorML._weather_data):,} rows")

    def get_power(self, sim_datetime) -> float:
        """
        Predict solar output in kW for a given datetime.

        Parameters
        ----------
        sim_datetime : datetime-like
            Current simulation timestamp (should be within 2006).

        Returns
        -------
        float : Predicted kW, capped at inverter_max_kw. Returns 0.0 at night.
        """
        row = self._lookup_weather(sim_datetime)
        if row is None:
            return 0.0

        # Skip model call at night
        if row['GHI'] == 0 and row['Solar Zenith Angle'] >= 90:
            return 0.0

        features = {col: row[col] for col in SolarGeneratorML._model.features}

        # Model predicts MW for the full farm; scale to this household's kW
        predicted_mw = SolarGeneratorML._model.predict(features)
        scale        = self.panel_capacity_kw / (SolarGeneratorML._farm_mw * 1000)
        predicted_kw = predicted_mw * 1000 * scale

        return min(predicted_kw, self.inverter_max_kw)

    def _lookup_weather(self, sim_datetime):
        """Round to nearest 30-min slot and fetch weather row."""
        dt = pd.Timestamp(sim_datetime)
        rounded = dt.replace(
            minute=0 if dt.minute < 15 else 30,
            second=0, microsecond=0
        )
        idx = SolarGeneratorML._weather_data.index
        if rounded in idx:
            return SolarGeneratorML._weather_data.loc[rounded]
        # Fallback to closest available
        closest = idx[np.argmin(np.abs(idx - rounded))]
        return SolarGeneratorML._weather_data.loc[closest]


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    from datetime import datetime

    gen = SolarGeneratorML(panel_capacity_kw=5.0, inverter_max_kw=4.0)

    tests = [
        datetime(2006, 7, 15,  2, 0),   # night
        datetime(2006, 7, 15,  8, 0),   # morning
        datetime(2006, 7, 15, 12, 0),   # noon
        datetime(2006, 7, 15, 18, 0),   # evening
        datetime(2006, 3, 13, 12, 0),   # historically peak day
        datetime(2006, 1, 15, 12, 0),   # winter noon
    ]

    print(f"\nSmoke test — {CITY}")
    print(f"{'Datetime':25s} | {'kW':>8}")
    print("-" * 38)
    for dt in tests:
        kw = gen.get_power(dt)
        print(f"{str(dt):25s} | {kw:8.4f} kW")
