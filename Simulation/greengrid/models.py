from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class StepResult:
    time_min: int
    day: int
    hour: int
    household_name: str
    household_type: str
    wealth_level: str
    season: str
    strategy: str
    cloud_coverage: float
    inverter_ok: bool
    solar_kw_raw: float
    solar_kw_used: float
    load_kw: float
    energy_gen_kwh: float
    energy_load_kwh: float
    net_kwh: float
    battery_soc_kwh: float
    battery_soc_pct: float
    battery_charged_kwh: float
    battery_discharged_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    curtailed_kwh: float
    unmet_load_kwh: float
    import_cost: float
    export_revenue: float
    net_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EventRecord:
    time_min: int
    day: int
    hour: int
    household_name: str
    event_type: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
