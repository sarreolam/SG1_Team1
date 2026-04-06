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
    name="neighborhood_mix",
    simulation=SimulationConfig(
        duration_days=30,
        timestep_minutes=60,
        season="summer",
        strategy=EnergyStrategy.LOAD_PRIORITY,
        seed=7,
    ),
    households=[
        HouseholdConfig(
            name="studio_low_01",
            household_type=HouseholdType.STUDIO,
            wealth_level=WealthLevel.LOW,
            battery=BatteryConfig(capacity_kwh=10.0),
            solar=SolarConfig(panel_capacity_kw=4.0, inverter_max_output_kw=3.5),
            load_shape=LoadShapeConfig(variability_multiplier=0.9),
        ),
        HouseholdConfig(
            name="family_mid_01",
            household_type=HouseholdType.SMALL_FAMILY,
            wealth_level=WealthLevel.MIDDLE,
        ),
        HouseholdConfig(
            name="family_high_01",
            household_type=HouseholdType.SMALL_FAMILY,
            wealth_level=WealthLevel.HIGH,
            solar=SolarConfig(panel_capacity_kw=6.0, inverter_max_output_kw=4.0),
        ),
        HouseholdConfig(
            name="large_luxury_01",
            household_type=HouseholdType.LARGE_FAMILY,
            wealth_level=WealthLevel.LUXURY,
            battery=BatteryConfig(capacity_kwh=18.0),
            solar=SolarConfig(panel_capacity_kw=7.0, inverter_max_output_kw=5.0),
            load_shape=LoadShapeConfig(variability_multiplier=1.15),
        ),
    ],
)
