import simpy
import random
import math
import typing
from Configs import config1

DEMAND = 100

def simulation(env):
    global DEMAND
    while env.now < config1.SIMULATION_DURATION:
        power_to_use = calculate_generation(env)
        print(env.now, power_to_use)
        DEMAND -= power_to_use
        if env.now % 48 == 0:
            DEMAND += 100
        yield env.timeout(config1.TIMESTEP)
        

def calculate_generation(env):
    sun_angle = ((env.now/60) - 6) * (math.pi / 12)
    power_generation = config1.SOLAR_PEAK * max(0,(math.sin(sun_angle)))
    return power_generation



env = simpy.Environment()
env.process(simulation(env))
print("Doing something")
env.run(until=config1.SIMULATION_DURATION)