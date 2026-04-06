import os
import green_grid_sim
from Configs import config_studio, config_small_family, config_large_family

configs = [config_studio, config_small_family, config_large_family]

output_dir = os.path.join(os.path.dirname(__file__), "output")

for cfg in configs:
    print(f"\nRunning: {cfg.HOUSEHOLD_TYPE} - {cfg.WEALTH_LEVEL}")
    green_grid_sim.run_simulation(config=cfg, output_dir=output_dir)