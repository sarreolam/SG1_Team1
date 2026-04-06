from greengrid import (
    BatteryConfig,
    EnergyStrategy,
    HouseholdConfig,
    HouseholdType,
    LoadShapeConfig,
    ScenarioConfig,
    SimulationConfig,
    SolarConfig,
    WealthLevel,
)

SCENARIO = ScenarioConfig(
    name="single_home",
    simulation=SimulationConfig(
        duration_days=30,
        timestep_minutes=60,
        season="winter",
        strategy=EnergyStrategy.CHARGE_PRIORITY,
        seed=42,
    ),
    households=[
        HouseholdConfig(
            name="house_01",
            household_type=HouseholdType.SMALL_FAMILY,
            wealth_level=WealthLevel.MIDDLE,
            battery=BatteryConfig(capacity_kwh=13.5, round_trip_efficiency=0.9),
            solar=SolarConfig(panel_capacity_kw=5.0, inverter_max_output_kw=4.0),
            load_shape=LoadShapeConfig(variability_multiplier=1.0),
        )
    ],
)
