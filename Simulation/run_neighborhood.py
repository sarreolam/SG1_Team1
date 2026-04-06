from greengrid import NeighborhoodSimulation
from scenarios.neighborhood_mix import SCENARIO


if __name__ == "__main__":
    result = NeighborhoodSimulation(SCENARIO).run()
    print("Run directory:", result["run_dir"])
    print("Files:")
    print(" -", result["household_csv"])
    print(" -", result["neighborhood_csv"])
    print(" -", result["events_csv"])
    print(" -", result["summary_csv"])
