"""
prepare_ml_data.py
------------------
Merges and cleans the 4 dataset files for ANY California city into a
single training-ready CSV for the linear regression model.

Handles:
  - Timezone correction: Weather is UTC, Actual is Pacific (UTC-8)
  - Mixed date formats: Berkeley uses dashes, others use slashes
  - Different farm capacities per city (for correct MW scaling)

Usage:
    python prepare_ml_data.py                        # defaults to San Diego
    python prepare_ml_data.py --city San_Diego

Output: Datasets/<city_folder>/merged_clean.csv
"""

import pandas as pd
import numpy as np
import os
import sys

# ── City config ─────────────────────────────────────────────────────────────
CITY_CONFIG = {
    'Squaw_Valley':   {'prefix': '189871', 'farm_mw': 112.9}
}

# ── Parse city argument ──────────────────────────────────────────────────────
city_name = 'Squaw_Valley'
config = CITY_CONFIG[city_name]
farm_mw = config['farm_mw']
prefix = config['prefix']

# ── Paths ────────────────────────────────────────────────────────────────────
# From Simulation/DataPrep/, go up two levels to project root, then Datasets/
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..', '..')
DATASETS_DIR = os.path.join(PROJECT_ROOT, 'Datasets')

# Find the city folder (handles slight name variations)
city_folder = next(
    (d for d in os.listdir(DATASETS_DIR) if city_name.split('_')[0] in d or prefix in d),
    None
)
if city_folder is None:
    print(f"Could not find folder for city '{city_name}' in {DATASETS_DIR}")
    sys.exit(1)

CITY_DIR    = os.path.join(DATASETS_DIR, city_folder)
ACTUAL_PATH  = os.path.join(CITY_DIR, f'{prefix}_Actual_DPV_{int(farm_mw*1000/1000*1000):.0f}MW_5m.csv')
WEATHER_PATH = os.path.join(CITY_DIR, f'{prefix}_Weather_30m.csv')
DA_PATH      = os.path.join(CITY_DIR, f'{prefix}_DA_DPV_{int(farm_mw*1000/1000*1000):.0f}MW_60m.csv')
HA4_PATH     = os.path.join(CITY_DIR, f'{prefix}_HA4_DPV_{int(farm_mw*1000/1000*1000):.0f}MW_60m.csv')
OUTPUT_PATH  = os.path.join(CITY_DIR, 'merged_clean.csv')

# Simpler: just find files by keyword
def find_file(folder, keyword):
    matches = [f for f in os.listdir(folder) if keyword in f]
    if not matches:
        raise FileNotFoundError(f"No file with '{keyword}' in {folder}")
    return os.path.join(folder, matches[0])

ACTUAL_PATH  = find_file(CITY_DIR, 'Actual')
WEATHER_PATH = find_file(CITY_DIR, 'Weather')
DA_PATH      = find_file(CITY_DIR, 'DA_')
HA4_PATH     = find_file(CITY_DIR, 'HA4')

# ── STEP 1: Load ─────────────────────────────────────────────────────────────
print("=" * 58)
print(f"  Preparing data for: {city_name}  (farm: {farm_mw} MW)")
print("=" * 58)

actual  = pd.read_csv(ACTUAL_PATH)
da      = pd.read_csv(DA_PATH)
ha4     = pd.read_csv(HA4_PATH)
weather = pd.read_csv(WEATHER_PATH, skiprows=2)

print(f"  Actual:  {len(actual):,} rows")
print(f"  Weather: {len(weather):,} rows")

# ── STEP 2: Parse timestamps (handles both / and - formats) ──────────────────
print("\nParsing timestamps...")
# 'mixed' format handles both '01/01/06 00:00' and '01-01-06 0:00'
actual['dt'] = pd.to_datetime(actual['LocalTime'], format='mixed', dayfirst=False)
da['dt']     = pd.to_datetime(da['LocalTime'],     format='mixed', dayfirst=False)
ha4['dt']    = pd.to_datetime(ha4['LocalTime'],    format='mixed', dayfirst=False)

# Weather is UTC — all CA cities are UTC-8 (Pacific Standard Time)
weather['dt_utc']   = pd.to_datetime(weather[['Year','Month','Day','Hour','Minute']])
weather['dt']       = weather['dt_utc'] - pd.Timedelta(hours=8)

# ── STEP 3: Resample to 30-min ───────────────────────────────────────────────
print("Resampling to 30-min intervals...")
actual_30 = (actual.set_index('dt')['Power(MW)']
             .resample('30min').mean().reset_index())
actual_30.columns = ['dt', 'power_mw']

da_30 = (da.set_index('dt')['Power(MW)']
         .resample('30min').interpolate(method='time').reset_index())
da_30.columns = ['dt', 'da_power_mw']

ha4_30 = (ha4.set_index('dt')['Power(MW)']
          .resample('30min').interpolate(method='time').reset_index())
ha4_30.columns = ['dt', 'ha4_power_mw']

# ── STEP 4: Select weather features ──────────────────────────────────────────
WEATHER_FEATURES = ['dt', 'GHI', 'Clearsky GHI', 'DHI', 'DNI',
                    'Temperature', 'Relative Humidity',
                    'Solar Zenith Angle', 'Cloud Type', 'Wind Speed']

weather_sel = weather[WEATHER_FEATURES].copy()

# ── STEP 5: Merge ─────────────────────────────────────────────────────────────
print("Merging all files...")
merged = actual_30.merge(weather_sel, on='dt', how='inner')
merged = merged.merge(da_30,  on='dt', how='left')
merged = merged.merge(ha4_30, on='dt', how='left')
print(f"  Merged shape: {merged.shape}")

# ── STEP 6: Clean ────────────────────────────────────────────────────────────
print("Cleaning...")
merged['da_power_mw']  = merged['da_power_mw'].ffill().bfill()
merged['ha4_power_mw'] = merged['ha4_power_mw'].ffill().bfill()
merged['power_mw']     = merged['power_mw'].clip(lower=0)
merged.dropna(subset=['GHI', 'power_mw'], inplace=True)

# ── STEP 7: Engineered features ───────────────────────────────────────────────
merged['hour']          = merged['dt'].dt.hour
merged['month']         = merged['dt'].dt.month
merged['is_daytime']    = (merged['Solar Zenith Angle'] < 90).astype(int)
merged['clearsky_ratio'] = (merged['GHI'] / merged['Clearsky GHI'].clip(lower=1)).clip(0, 1)

# Store farm capacity in the CSV metadata comment (first row not needed,
# instead save it as a separate config)
config_path = os.path.join(CITY_DIR, 'city_config.json')
import json
with open(config_path, 'w') as f:
    json.dump({'city': city_name, 'farm_mw': farm_mw, 'prefix': prefix}, f)

# ── STEP 8: Summary & save ────────────────────────────────────────────────────
print(f"\nDataset summary:")
print(f"  Total rows:   {len(merged):,}")
print(f"  Daytime rows: {merged['is_daytime'].sum():,}")
print(f"  Date range:   {merged['dt'].min()} to {merged['dt'].max()}")
print(f"  Nulls:        {merged.isnull().sum().sum()}")

corr = merged[['power_mw','GHI']].corr().iloc[0,1]
print(f"  GHI-power correlation (after timezone fix): {corr:.3f}")

merged.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved: {OUTPUT_PATH}")
print(f"Config: {config_path}")
print("Done!")