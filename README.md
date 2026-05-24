## Installation & Running the Simulation

## Live Dashboard
You can view the deployed dashboard here:  
https://sarreolam.github.io/SG1_Team1/

### Prerequisites
- **Python 3.10+** (3.11 recommended)
- `pip` (comes with most Python installs)
- `npm` 

### Clone the repository
```bash
git clone https://github.com/sarreolam/SG1_Team1.git
cd SG1_Team1
```

Windows (CMD)
```bash
python -m venv venv
.\.venv\Scripts\activate.bat
```

macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Setting up the ML Model (run once before the simulation)

The simulation uses a Linear Regression model trained on real weather data
from Squaw Valley 2006. You need to run the following two steps once before
running the simulation for the first time.

**Step 1 — Place the dataset files**

Make sure the folder `ML/Datasets/189871_Squaw_Valley_2006/` contains the
four raw CSV files:
- `189871_Actual_DPV_113MW_5m.csv`
- `189871_DA_DPV_113MW_60m.csv`
- `189871_HA4_DPV_113MW_60m.csv`
- `189871_Weather_30m.csv`

**Step 2 — Prepare the data**

From the project root:
```bash
py .\ML\prepare_ml_data.py
```

This merges and cleans the raw CSVs into `ML/Datasets/189871_Squaw_Valley_2006/merged_clean.csv`.

**Step 3 — Train the model**

```bash
py .\ML\solar_model.py
```

This trains the Linear Regression model using Gradient Descent and saves
the weights to `ML/model_weights.json`. You should see training metrics
printed in the terminal (RMSE, MAE, R²).

To also see sample predictions after training:
```bash
py .\ML\solar_model.py --eval
```

Once these two steps are done, the simulation will automatically use the
trained model via `ML/components_ml.py`.

---

## Run the simulation
```bash
py .\Simulation\run_neighborhood.py
```

## Creating Custom Scenarios

You can run multiple simulations by creating your own scenario configuration.
Define a `SCENARIO` using `ScenarioConfig` and add as many households as needed.

Example:

```python
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
        # Add more households here...
    ],
)
```

You can define multiple households with different configurations (wealth level, solar, battery, etc.) to simulate diverse neighborhoods.

---

## Running a Scenario

Create a run file that imports the scenario and executes the simulation:

```python
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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
```

Running this script will:

* Execute the simulation ⚡
* Generate CSV outputs 📄
* Automatically run `prep_data.py`
* Produce JSON files ready for the dashboard 📊

---

## Preparing Data Manually

If you want to prepare data from a previously generated simulation, you can run:

Latest output:

```bash
py .\DataPrep\prepare_data.py --source output/latest
```

Specific scenario run:

```bash
py .\DataPrep\prepare_data.py --source output/scenarioname_date_hour
```

This will regenerate the JSON files used by the dashboard.

---

## Running the Dashboard

Open a new terminal and navigate to the project:

```bash
cd SG1_Team1
cd Dashboard
```

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

The dashboard will load the prepared JSON data and display the simulation results in real time 🎯