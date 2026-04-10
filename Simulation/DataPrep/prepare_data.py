import pandas as pd
import glob, json, os

def prepare_all(input_dir=None, output_dir=None):
    base = os.path.dirname(__file__)

    if input_dir is None:
        input_dir = os.path.join(base, "..", "output")
    if output_dir is None:
        output_dir = os.path.join(base, "..", "Dashboard", "data")

    os.makedirs(output_dir, exist_ok=True)

    # Leer y combinar todos los CSVs
    all_files = glob.glob(os.path.join(input_dir, "*_log.csv"))
    dfs = [pd.read_csv(f) for f in all_files]
    df = pd.concat(dfs, ignore_index=True)
    df["day"] = df["time_min"] // (60 * 24)

    simulations = []

    for (household_type, wealth_level), group in df.groupby(["household_type", "wealth_level"]):
        sim_id = f"{household_type}_{wealth_level}"

        # --- Summary ---
        total_gen        = round(group["energy_gen_kwh"].sum(), 4)
        total_load       = round(group["energy_load_kwh"].sum(), 4)
        total_import     = round(group["grid_import_kwh"].sum(), 4)
        total_export     = round(group["grid_export_kwh"].sum(), 4)
        total_import_cost   = round(group["import_cost"].sum(), 4)
        total_export_revenue = round(group["export_revenue"].sum(), 4)
        self_consumed    = round(total_gen - total_export, 4)
        self_sufficiency = round((self_consumed / total_load * 100) if total_load > 0 else 0, 1)
        total_curtailed  = round(group["curtailed_kwh"].sum(), 4)
        total_surplus    = round(group.loc[group["net_kwh"] > 0, "net_kwh"].sum(), 4)
        total_deficit    = round(group.loc[group["net_kwh"] < 0, "net_kwh"].abs().sum(), 4)

        summary = {
            "total_gen_kwh":          total_gen,
            "total_load_kwh":         total_load,
            "total_grid_import_kwh":  total_import,
            "total_grid_export_kwh":  total_export,
            "total_import_cost":      total_import_cost,
            "total_export_revenue":   total_export_revenue,
            "self_sufficiency_pct":   self_sufficiency,
            "total_curtailed_kwh":    total_curtailed,
            "total_surplus_kwh":      total_surplus,
            "total_deficit_kwh":      total_deficit,
        }

        # --- Timeseries: promedio por hora (sobre los 30 días) ---
        hourly = group.groupby("hour").agg(
            solar_kw        =("solar_kw",         "mean"),
            load_kw         =("load_kw",          "mean"),
            net_kwh         =("net_kwh",          "mean"),
            battery_soc_pct =("battery_soc_pct",  "mean"),
            grid_import_kwh =("grid_import_kwh",  "mean"),
            grid_export_kwh =("grid_export_kwh",  "mean"),
        ).reset_index()

        timeseries = []
        for _, row in hourly.iterrows():
            timeseries.append({
                "hour":            int(row["hour"]),
                "solar_kw":        round(row["solar_kw"], 4),
                "load_kw":         round(row["load_kw"], 4),
                "net_kwh":         round(row["net_kwh"], 6),
                "battery_soc_pct": round(row["battery_soc_pct"], 2),
                "grid_import_kwh": round(row["grid_import_kwh"], 6),
                "grid_export_kwh": round(row["grid_export_kwh"], 6),
            })

        # --- Por día (para filtros de tendencia) ---
        daily = group.groupby("day").agg(
            solar_kwh   =("energy_gen_kwh",   "sum"),
            load_kwh    =("energy_load_kwh",  "sum"),
            import_kwh  =("grid_import_kwh",  "sum"),
            export_kwh  =("grid_export_kwh",  "sum"),
            net_kwh     =("net_kwh",          "sum"),
            import_cost =("import_cost",      "sum"),
        ).reset_index()

        by_day = []
        for _, row in daily.iterrows():
            by_day.append({
                "day":        int(row["day"]),
                "solar_kwh":  round(row["solar_kwh"], 4),
                "load_kwh":   round(row["load_kwh"], 4),
                "import_kwh": round(row["import_kwh"], 4),
                "export_kwh": round(row["export_kwh"], 4),
                "net_kwh":    round(row["net_kwh"], 4),
                "import_cost":round(row["import_cost"], 4),
            })

        simulations.append({
            "id": sim_id,
            "metadata": {
                "household_type": household_type,
                "wealth_level":   wealth_level,
            },
            "summary":    summary,
            "timeseries": timeseries,
            "by_day":     by_day,
        })

    # Guardar el JSON principal que usan los componentes
    output = {"simulations": simulations}
    with open(os.path.join(output_dir, "all_energy_simulations.json"), "w") as f:
        json.dump(output, f, indent=2)

    # Mantener los JSONs auxiliares por si acaso
    duck = df.groupby("hour")[["solar_kw","load_kw","net_kwh"]].mean().reset_index()
    duck.to_json(os.path.join(output_dir, "duck_curve.json"), orient="records")

    by_type = df.groupby(["household_type","hour"])[["solar_kw","load_kw"]].mean().reset_index()
    by_type.to_json(os.path.join(output_dir, "by_type_hourly.json"), orient="records")

    by_wealth = df.groupby("wealth_level")[["energy_gen_kwh","energy_load_kwh","grid_import_kwh","grid_export_kwh"]].sum().reset_index()
    by_wealth.to_json(os.path.join(output_dir, "by_wealth_summary.json"), orient="records")

    print(f"Done. {len(simulations)} simulations written to energy_simulations.json")
    print(f"Saved to: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    prepare_all()