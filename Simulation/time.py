import simpy
import random
import math
import typing
from solar_model import sample_cloud_coverage, solar_generation_kw
from Configs import config1

DEMAND = 100
cloud_today = sample_cloud_coverage(config1.SEASON)
current_day = -1

def simulation(env):
    global DEMAND, cloud_today, current_day

    while env.now < config1.SIMULATION_DURATION:
        day = int(env.now // (60 * 24))
        if day != current_day:
            current_day = day
            cloud_today = sample_cloud_coverage(config1.SEASON)

        power_to_use = solar_generation_kw(int(env.now), cloud_today, inverter_down=False)
        print(env.now, power_to_use, "cloud:", round(cloud_today, 2))

        DEMAND -= power_to_use

        # Si querías recargar demanda "cada día"
        if int(env.now) % (60 * 24) == 0:
            DEMAND += 100

        yield env.timeout(config1.TIMESTEP)

def calculate_generation(env):
    sun_angle = ((env.now/60) - 6) * (math.pi / 12)
    power_generation = config1.SOLAR_PEAK * max(0, (math.sin(sun_angle)))
    return power_generation

env = simpy.Environment()
env.process(simulation(env))
print("Doing something")
env.run(until=config1.SIMULATION_DURATION)
