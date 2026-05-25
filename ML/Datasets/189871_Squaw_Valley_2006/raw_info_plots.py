# -*- coding: utf-8 -*-
"""
Created on Sun May 24 19:29:43 2026

@author: marco
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------------------------------------------
# 1. Styling & Plot Configurations (Clean, readable design)
# ------------------------------------------------------------------
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'font.family': 'sans-serif'
})

# ------------------------------------------------------------------
# 2. Data Loading & Preprocessing
# ------------------------------------------------------------------
print("Loading dataset...")
df = pd.read_csv('Datasets/189871_Squaw_Valley_2006/merged_clean.csv')
df['dt'] = pd.to_datetime(df['dt'])

# Filter data for daylight hours where generation occurs (is_daytime == 1)
daytime_df = df[df['is_daytime'] == 1].copy()

# Map numerical NSRDB Cloud Types to structural names
cloud_labels = {
    0: 'Clear', 1: 'Probably Clear', 2: 'Fog', 3: 'Water', 
    4: 'Super-Cooled', 5: 'Mixed', 6: 'Opaque Ice', 
    7: 'Cirrus', 8: 'Overlapping', 9: 'Overshooting', 10: 'Unknown'
}
daytime_df['Cloud_Name'] = daytime_df['Cloud Type'].map(cloud_labels)


# ==================================================================
# GRAPH 1: Weather Features vs. Solar Power (Dashboard)
# ==================================================================
print("Generating Graph 1: Feature Relationships...")
fig1, axes = plt.subplots(2, 2, figsize=(14, 10))

# Top-Left: GHI vs Power Output
sns.scatterplot(data=daytime_df, x='GHI', y='power_mw', alpha=0.3, color='orange', s=8, ax=axes[0, 0])
axes[0, 0].set_title('Solar Irradiance (GHI) vs Power Output')
axes[0, 0].set_xlabel('GHI ($W/m^2$)')
axes[0, 0].set_ylabel('Power Output (MW)')

# Top-Right: Temperature vs Power Output
sns.scatterplot(data=daytime_df, x='Temperature', y='power_mw', alpha=0.3, color='crimson', s=8, ax=axes[0, 1])
axes[0, 1].set_title('Ambient Temperature vs Power Output')
axes[0, 1].set_xlabel('Temperature (°C)')
axes[0, 1].set_ylabel('Power Output (MW)')

# Bottom-Left: Relative Humidity vs Power Output
sns.scatterplot(data=daytime_df, x='Relative Humidity', y='power_mw', alpha=0.3, color='dodgerblue', s=8, ax=axes[1, 0])
axes[1, 0].set_title('Relative Humidity vs Power Output')
axes[1, 0].set_xlabel('Relative Humidity (%)')
axes[1, 0].set_ylabel('Power Output (MW)')

# Bottom-Right: Categorical Bar Chart (Sorted by highest average power generation)
cloud_order = daytime_df.groupby('Cloud_Name')['power_mw'].mean().sort_values(ascending=False).index
sns.barplot(data=daytime_df, x='Cloud_Name', y='power_mw', ax=axes[1, 1], order=cloud_order, palette='viridis', errorbar=None)
axes[1, 1].set_title('Average Power Output by Cloud Type')
axes[1, 1].set_xlabel('Cloud Classification')
axes[1, 1].set_ylabel('Mean Power Output (MW)')
axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=30, ha='right')

plt.suptitle('Weather Features vs. Solar Power Generation (Daytime Hours)', fontweight='bold')
plt.tight_layout()
fig1.savefig('1_feature_relationships.png', dpi=150)
plt.close(fig1)


# ==================================================================
# GRAPH 2: Actual Generation vs. Forecast Models
# ==================================================================
print("Generating Graph 2: Actual vs Forecast Line Comparison...")
# Isolate a specific sample week to look closely at patterns
sample_week = df[(df['dt'] >= '2006-06-12') & (df['dt'] <= '2006-06-19')]

fig2, ax = plt.subplots(figsize=(14, 5.5))
ax.plot(sample_week['dt'], sample_week['power_mw'], label='Actual Power Generation', color='black', linewidth=2)
ax.plot(sample_week['dt'], sample_week['da_power_mw'], label='Day-Ahead Forecast', color='crimson', linestyle='--', alpha=0.8)
ax.plot(sample_week['dt'], sample_week['ha4_power_mw'], label='4-Hour Ahead Forecast', color='royalblue', linestyle=':', alpha=0.8)

ax.set_title('Actual Generation vs. Forecast Models (June 12-19, 2006)', fontweight='bold')
ax.set_xlabel('Date and Time')
ax.set_ylabel('Solar Power Output (MW)')
ax.legend(loc='upper right')
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
fig2.savefig('2_actual_vs_predicted.png', dpi=150)
plt.close(fig2)


# ==================================================================
# GRAPH 3: Case Study - Clear Day vs. Cloudy Day Storytelling
# ==================================================================
print("Generating Graph 3: Weather Micro-Storylines...")
# Filter for two contrasting days in June
cloudy_day = df[(df['dt'] >= '2006-06-13') & (df['dt'] < '2006-06-14')].copy()
clear_day = df[(df['dt'] >= '2006-06-19') & (df['dt'] < '2006-06-20')].copy()

# Compute continuous hour axes for smoother day plotting
cloudy_day['decimal_hour'] = cloudy_day['dt'].dt.hour + cloudy_day['dt'].dt.minute / 60
clear_day['decimal_hour'] = clear_day['dt'].dt.hour + clear_day['dt'].dt.minute / 60

fig3, axes3 = plt.subplots(2, 2, figsize=(14, 9.5), sharex='col')

# --- COLUMN 1: CLOUDY DAY (June 13) ---
# Weather parameters on dual axes
axes3[0, 0].plot(cloudy_day['decimal_hour'], cloudy_day['GHI'], color='darkorange', linewidth=2.5)
axes3[0, 0].set_ylabel('GHI ($W/m^2$)', color='darkorange')
axes3[0, 0].tick_params(axis='y', labelcolor='darkorange')
axes3[0, 0].set_title('Cloudy Day (June 13): Weather Conditions', fontweight='bold')
axes3[0, 0].grid(True, linestyle='--', alpha=0.4)

ax0_twin = axes3[0, 0].twinx()
ax0_twin.plot(cloudy_day['decimal_hour'], cloudy_day['Relative Humidity'], color='teal', linestyle='--', linewidth=1.8)
ax0_twin.set_ylabel('Relative Humidity (%)', color='teal')
ax0_twin.tick_params(axis='y', labelcolor='teal')

# Real Power Response
axes3[1, 0].plot(cloudy_day['decimal_hour'], cloudy_day['power_mw'], color='black', linewidth=2.5, label='Actual Power')
axes3[1, 0].plot(cloudy_day['decimal_hour'], cloudy_day['da_power_mw'], color='crimson', linestyle='--', linewidth=1.8, label='Day-Ahead Forecast')
axes3[1, 0].set_title('Cloudy Day: Highly Volatile Drop-offs', fontweight='bold')
axes3[1, 0].set_xlabel('Hour of Day')
axes3[1, 0].set_ylabel('Power Output (MW)')
axes3[1, 0].set_xlim(4, 20)  # Focus on daylight hours (4 AM - 8 PM)
axes3[1, 0].grid(True, linestyle='--', alpha=0.4)
axes3[1, 0].legend(loc='upper right')

# --- COLUMN 2: CLEAR DAY (June 19) ---
# Weather parameters on dual axes
axes3[0, 1].plot(clear_day['decimal_hour'], clear_day['GHI'], color='darkorange', linewidth=2.5)
axes3[0, 1].set_title('Clear Day (June 19): Weather Conditions', fontweight='bold')
axes3[0, 1].grid(True, linestyle='--', alpha=0.4)

ax1_twin = axes3[0, 1].twinx()
ax1_twin.plot(clear_day['decimal_hour'], clear_day['Relative Humidity'], color='teal', linestyle='--', linewidth=1.8)
ax1_twin.set_ylabel('Relative Humidity (%)', color='teal')
ax1_twin.tick_params(axis='y', labelcolor='teal')

# Real Power Response
axes3[1, 1].plot(clear_day['decimal_hour'], clear_day['power_mw'], color='black', linewidth=2.5, label='Actual Power')
axes3[1, 1].plot(clear_day['decimal_hour'], clear_day['da_power_mw'], color='crimson', linestyle='--', linewidth=1.8, label='Day-Ahead Forecast')
axes3[1, 1].set_title('Clear Day: Smooth, Ideal Generation Curve', fontweight='bold')
axes3[1, 1].set_xlabel('Hour of Day')
axes3[1, 1].set_xlim(4, 20)
axes3[1, 1].grid(True, linestyle='--', alpha=0.4)
axes3[1, 1].legend(loc='upper right')

plt.suptitle('Case Study: Solar Generation Response to Weather Storylines', fontweight='bold', y=0.98)
plt.tight_layout()
fig3.savefig('3_weather_storytelling.png', dpi=150)
plt.close(fig3)

print("Success! '1_feature_relationships.png', '2_actual_vs_predicted.png', and '3_weather_storytelling.png' have been saved.")