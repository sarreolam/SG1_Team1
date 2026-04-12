from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import argparse


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_dashboard_data(source_dir: Path, output_dir: Path) -> None:
    household = pd.read_csv(source_dir / "household_timeseries.csv")
    neighborhood = pd.read_csv(source_dir / "neighborhood_timeseries.csv")
    events = pd.read_csv(source_dir / "events.csv")
    summary = pd.read_csv(source_dir / "summary.csv")

    # KPIs
    kpis = {
        "total_generation_kwh": round(float(summary["total_generation_kwh"].sum()), 2),
        "total_load_kwh": round(float(summary["total_load_kwh"].sum()), 2),
        "total_grid_import_kwh": round(float(summary["total_grid_import_kwh"].sum()), 2),
        "total_grid_export_kwh": round(float(summary["total_grid_export_kwh"].sum()), 2),
        "total_curtailed_kwh": round(float(summary["total_curtailed_kwh"].sum()), 2),
        "avg_battery_soc_pct": round(float(summary["avg_battery_soc_pct"].mean()), 2),
        "net_cost": round(float(summary["net_cost"].sum()), 2),
        "household_count": int(summary["household_name"].nunique()),
        "avg_cloud_coverage": round(float(neighborhood["cloud_coverage_avg"].mean()), 4),
    }
    _write_json(output_dir / "kpis.json", kpis)

    # Neighborhood time series
    keep_cols = [
        "time_min", "day", "hour", "season", "strategy",
        "household_count", "cloud_coverage_avg", "inverter_availability_pct",
        "solar_kw_used", "load_kw", "battery_soc_kwh",
        "grid_import_kwh", "grid_export_kwh", "curtailed_kwh", "net_cost"
    ]
    _write_json(
        output_dir / "timeseries_neighborhood.json",
        neighborhood[keep_cols].to_dict(orient="records")
    )

    # Duck curve
    duck = neighborhood[["day", "hour", "load_kw", "solar_kw_used"]].copy()
    duck["net_load_kw"] = duck["load_kw"] - duck["solar_kw_used"]
    _write_json(output_dir / "duck_curve.json", duck.to_dict(orient="records"))

    # By household type
    by_type = (
        household.groupby("household_type", as_index=False)
        .agg({
            "energy_gen_kwh": "sum",
            "energy_load_kwh": "sum",
            "grid_import_kwh": "sum",
            "grid_export_kwh": "sum",
            "battery_soc_pct": "mean",
            "net_cost": "sum",
        })
        .rename(columns={
            "energy_gen_kwh": "generation_kwh",
            "energy_load_kwh": "load_kwh",
            "grid_import_kwh": "import_kwh",
            "grid_export_kwh": "export_kwh",
            "battery_soc_pct": "avg_soc_pct",
        })
    )
    _write_json(output_dir / "by_household_type.json", by_type.to_dict(orient="records"))

    # By wealth level
    by_wealth = (
        household.groupby("wealth_level", as_index=False)
        .agg({
            "energy_gen_kwh": "sum",
            "energy_load_kwh": "sum",
            "grid_import_kwh": "sum",
            "grid_export_kwh": "sum",
            "battery_soc_pct": "mean",
            "net_cost": "sum",
        })
        .rename(columns={
            "energy_gen_kwh": "generation_kwh",
            "energy_load_kwh": "load_kwh",
            "grid_import_kwh": "import_kwh",
            "grid_export_kwh": "export_kwh",
            "battery_soc_pct": "avg_soc_pct",
        })
    )
    _write_json(output_dir / "by_wealth_level.json", by_wealth.to_dict(orient="records"))

    # Household rankings
    rankings = (
        household.groupby(
            ["household_name", "household_type", "wealth_level"], as_index=False
        )
        .agg({
            "energy_gen_kwh": "sum",
            "energy_load_kwh": "sum",
            "grid_import_kwh": "sum",
            "grid_export_kwh": "sum",
            "net_cost": "sum",
            "battery_soc_pct": "mean",
        })
        .rename(columns={
            "energy_gen_kwh": "total_generation_kwh",
            "energy_load_kwh": "total_load_kwh",
            "grid_import_kwh": "total_import_kwh",
            "grid_export_kwh": "total_export_kwh",
            "battery_soc_pct": "avg_soc_pct",
        })
        .sort_values("net_cost", ascending=True)
    )
    _write_json(output_dir / "household_rankings.json", rankings.to_dict(orient="records"))

    # Events summary
    if not events.empty and "event_type" in events.columns:
        event_counts = events["event_type"].value_counts().to_dict()
    else:
        event_counts = {}
    _write_json(output_dir / "events_summary.json", event_counts)

    # Filters
    filters = {
        "seasons": sorted(household["season"].dropna().unique().tolist()),
        "strategies": sorted(household["strategy"].dropna().unique().tolist()),
        "household_types": sorted(household["household_type"].dropna().unique().tolist()),
        "wealth_levels": sorted(household["wealth_level"].dropna().unique().tolist()),
    }
    _write_json(output_dir / "filters.json", filters)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare dashboard JSON files from simulation CSVs.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("output/latest"),
        help="Directory containing household_timeseries.csv, neighborhood_timeseries.csv, events.csv, summary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../Dashboard/data"),
        help="Directory where dashboard JSON files will be written",
    )
    args = parser.parse_args()

    build_dashboard_data(args.source, args.output)
    print(f"Dashboard data prepared from: {args.source.resolve()}")
    print(f"JSON files written to: {args.output.resolve()}")


if __name__ == "__main__":
    main()