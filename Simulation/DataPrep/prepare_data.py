import pandas as pd
import glob, json, os

def prepare_all(input_dir=None, output_dir=None):
    base = os.path.dirname(__file__)
    
    if input_dir is None:
        input_dir = os.path.join(base, "..", "output")
    if output_dir is None:
        output_dir = os.path.join(base, "..", "Dashboard", "data")

    os.makedirs(output_dir, exist_ok=True)

    all_files = glob.glob(os.path.join(input_dir, "*_log.csv"))
    dfs = [pd.read_csv(f) for f in all_files]
    df = pd.concat(dfs, ignore_index=True)
    df["day"] = df["time_min"] // (60 * 24)

    duck = df.groupby("hour")[["solar_kw","load_kw","net_kwh"]].mean().reset_index()
    duck.to_json(os.path.join(output_dir, "duck_curve.json"), orient="records")

    by_type = df.groupby(["household_type","hour"])[["solar_kw","load_kw"]].mean().reset_index()
    by_type.to_json(os.path.join(output_dir, "by_type_hourly.json"), orient="records")

    by_wealth = df.groupby("wealth_level")[["energy_gen_kwh","energy_load_kwh","grid_import_kwh","grid_export_kwh"]].sum().reset_index()
    by_wealth.to_json(os.path.join(output_dir, "by_wealth_summary.json"), orient="records")

    print(f"Data preparation complete. Files saved to: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    prepare_all()